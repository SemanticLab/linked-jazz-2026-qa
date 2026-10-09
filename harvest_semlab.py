"""Harvest human-judged relationships for the overlapping transcripts from base.semlab.io
via the wbgetentities API (SPARQL is too slow behind Cloudflare)."""
import csv, json, os, sys, time, urllib.request, urllib.parse
UA = "semlab-data-process"
API = "https://base.semlab.io/w/api.php"
CACHE = "raw/entities"; os.makedirs(CACHE, exist_ok=True)
REL_PROPS = None  # any statement with a P25 qualifier counts

def get_entities(ids):
    ids = list(dict.fromkeys(ids))
    out = {}
    need = []
    for q in ids:
        p = f"{CACHE}/{q}.json"
        if os.path.exists(p): out[q] = json.load(open(p))
        else: need.append(q)
    for i in range(0, len(need), 20):
        chunk = need[i:i+20]
        url = API + "?" + urllib.parse.urlencode({"action":"wbgetentities","ids":"|".join(chunk),"format":"json","props":"labels|descriptions|claims|aliases"})
        for attempt in range(5):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                body = urllib.request.urlopen(req, timeout=120).read()
                try: d = json.loads(body)
                except Exception: print("BODY:", body[:300], file=sys.stderr); raise
                break
            except Exception as e:
                print("retry", attempt, e, file=sys.stderr); time.sleep(2*(attempt+1))
        else: raise SystemExit("API failed")
        for q, e in d.get("entities", {}).items():
            json.dump(e, open(f"{CACHE}/{q}.json","w"))
            out[q] = e
        print(f"  fetched {min(i+20,len(need))}/{len(need)}", file=sys.stderr)
    return out

def val(snak):
    dv = snak.get("datavalue", {}).get("value")
    if isinstance(dv, dict):
        if "id" in dv: return dv["id"]
        if "time" in dv: return dv["time"]
        if "text" in dv: return dv["text"]
    return dv

def claims(e, p):
    return [val(c["mainsnak"]) for c in e.get("claims", {}).get(p, [])]

def label(e): return e.get("labels", {}).get("en", {}).get("value")

# ---- 1. overlap list
sem = list(csv.DictReader(open('semlab_transcripts.csv')))
srcmap = {'Hamilton College':'hamilton','Smithsonian':'si','Rutgers':'rutgers'}
by_t = {}
for r in sem:
    t = r['t'].rsplit('/',1)[-1]
    d = by_t.setdefault(t, {'transcript':t,'label':r['tLabel'],'source':r['sourceLabel'],'collection':srcmap.get(r['sourceLabel']),
                            'slug':r['slug'],'md5':r['md5'],'source_url':r['url'],'interviewees':{},'dates':set()})
    if r['interviewee']:
        d['interviewees'][r['interviewee'].rsplit('/',1)[-1]] = {'label':r['intervieweeLabel'],'wd_qid':r['wdqid'] or None}
    if r['date'] and not r['date'].startswith('_:'): d['dates'].add(r['date'][:10])
sq = [l.rstrip('\n').split('|') for l in open('sqlite_interviewees_rhs.txt')][1:]
sq_by_qid, sq_by_name = {}, {}
for doc_id, coll, interviewee, qid, lab, role in sq:
    rec = {'doc_id':doc_id,'collection':coll,'doc_interviewee':interviewee,'label':lab,'role':role}
    if qid: sq_by_qid.setdefault(qid, []).append(rec)
    sq_by_name.setdefault(lab.lower(), []).append(rec)
overlap = []
for t, d in sorted(by_t.items(), key=lambda x: x[1]['label']):
    if not d['collection']: continue
    d['dates'] = sorted(d['dates'])
    docs = {}
    for pid, iv in d['interviewees'].items():
        hits = [h for h in sq_by_qid.get(iv['wd_qid'], []) if h['collection']==d['collection']] if iv['wd_qid'] else []
        if not hits: hits = [h for h in sq_by_name.get(iv['label'].lower(), []) if h['collection']==d['collection']]
        iv['sqlite_docs'] = [h['doc_id'] for h in hits]
        for h in hits: docs[h['doc_id']] = h
    d['sqlite_docs'] = sorted(docs)
    overlap.append(d)
print("overlap transcripts:", len(overlap), file=sys.stderr)

# ---- 2. interviewee items -> statements with P25 qualifier
people_ids = [pid for d in overlap for pid in d['interviewees']]
tr_ids = [d['transcript'] for d in overlap]
ents = get_entities(people_ids + tr_ids)
stmts = []
for d in overlap:
    for pid in d['interviewees']:
        e = ents[pid]
        for prop, cl in e.get("claims", {}).items():
            for c in cl:
                q = c.get("qualifiers", {})
                if "P25" not in q: continue
                refs = []
                for ref in c.get("references", []):
                    for s in ref.get("snaks", {}).get("P26", []): refs.append(val(s))
                stmts.append({"stmt_id": c["id"], "subject": pid, "prop": prop, "object": val(c["mainsnak"]),
                              "method": val(q["P25"][0]), "consensus": val(q["P40"][0]) if "P40" in q else None,
                              "rank": c.get("rank"), "ref_blocks": refs})
print("statements on overlap interviewees:", len(stmts), file=sys.stderr)

# ---- 3. referenced blocks
block_ids = [b for s in stmts for b in s["ref_blocks"] if b]
bents = get_entities(block_ids)
blocks = {}
for q, e in bents.items():
    blocks[q] = {"block": q, "parent": (claims(e,"P24") or [None])[0], "local_id": (claims(e,"P17") or [None])[0],
                 "text": (claims(e,"P19") or [None])[0], "speaker": (claims(e,"P23") or [None])[0],
                 "text_url": (claims(e,"P20") or [None])[0], "entities": claims(e,"P21"), "label": label(e)}
# ---- 4. object persons + methods + speakers
obj_ids = [s["object"] for s in stmts] + [s["method"] for s in stmts] + [b["speaker"] for b in blocks.values() if b["speaker"]]
oents = get_entities(obj_ids)
items = {q: {"label": label(e), "description": e.get("descriptions",{}).get("en",{}).get("value"),
             "wd_qid": (claims(e,"P8") or [None])[0], "instance_of": claims(e,"P1"), "slug": (claims(e,"P7") or [None])[0]}
         for q, e in {**oents, **{p: ents[p] for p in people_ids}}.items()}
props = {r['p'].rsplit('/',1)[-1]: r['pLabel'] for r in csv.DictReader(open('semlab_properties.csv'))} if os.path.exists('semlab_properties.csv') else {}

json.dump({"overlap": overlap, "statements": stmts, "blocks": blocks, "items": items, "props": props},
          open("data/semlab_harvest.json","w"), indent=1)
# summary
from collections import Counter
tset = set(tr_ids)
in_overlap = sum(1 for s in stmts if any(blocks.get(b,{}).get("parent") in tset for b in s["ref_blocks"]))
print("statements with a ref block in an overlap transcript:", in_overlap, file=sys.stderr)
print(Counter(s["method"] for s in stmts), file=sys.stderr)
print(Counter(s["prop"] for s in stmts).most_common(), file=sys.stderr)
print("blocks fetched:", len(blocks), "with text:", sum(1 for b in blocks.values() if b["text"]), file=sys.stderr)
print("ref-block parents:", Counter(b["parent"] in tset for b in blocks.values()), file=sys.stderr)
