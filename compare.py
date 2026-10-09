"""Compare human-judged relationships (base.semlab.io) with the LLM/audit relationships in linked_jazz.sqlite
for the overlapping transcripts. Writes data/comparison.json."""
import json, re, unicodedata
from collections import Counter, defaultdict

H = json.load(open("data/semlab_harvest.json"))
S = json.load(open("data/sqlite_side.json"))
ITEMS, BLOCKS = H["items"], H["blocks"]
PROP = {"P29":"knows of","P30":"mentor of","P31":"collaborated with","P32":"acquaintance of","P33":"has met","P34":"friend of",
        "P35":"in music group with","P36":"played with","P37":"played under","P38":"toured with","P39":"influenced by",
        "P70":"grew up with","P71":"recorded with","P113":"relative of","P123":"life partner"}
METHOD = {"Q18800":"ner","Q18801":"crowd"}   # supervised NER (name tagged, 'knows of') / 52nd Street crowdsourcing
TIER = {"knows of":"T0","has met":"T1","acquaintance of":"T1","friend of":"T2",
        "played with":"T3","in music group with":"T3","toured with":"T3","collaborated with":"T3","recorded with":"T3",
        "played under":"T4","bandleader of":"T4b",
        "mentored by":"T5","influenced by":"T5","mentor of":"T5","influence on":"T5"}   # crowd used 'mentor of' in both directions
NEAR = {("T3","T4"),("T4","T3"),("T3","T4b"),("T4b","T3"),("T1","T2"),("T2","T1")}  # cross-tier pairs still counted 'near'

def norm_name(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode().lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split())
def norm_text(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s).split()
def shingles(words, k=5):
    if len(words) < k: return {" ".join(words)} if words else set()
    return {" ".join(words[i:i+k]) for i in range(len(words)-k+1)}

def directed(rel, direction):
    """SQLite relation+direction -> label from the interviewee's point of view (semlab's convention)."""
    if rel == "played under": return "played under" if direction != "interviewee" else "bandleader of"
    if rel == "mentor of":    return "mentor of" if direction == "interviewee" else "mentored by"
    if rel == "influenced by": return "influence on" if direction == "interviewee" else "influenced by"
    return rel

transcripts, pairs_all = [], []
for T in H["overlap"]:
    tq = T["transcript"]
    cand_docs = T["sqlite_docs"]
    # ---- blocks of candidate docs -> shingle index
    idx = defaultdict(set); sq_blocks = {}
    for d in cand_docs:
        for b in S["blocks"].get(d, []):
            w = norm_text(b["text"]); b["_w"] = w; sq_blocks[b["block_id"]] = b
            for sh in shingles(w): idx[sh].add(b["block_id"])
    # ---- semlab statements for this transcript
    stmts = [s for s in H["statements"] if any(BLOCKS.get(b,{}).get("parent") == tq for b in s["ref_blocks"])]
    ref_ids = {b for s in stmts for b in s["ref_blocks"] if BLOCKS.get(b,{}).get("parent") == tq}
    align = {}
    for rb in ref_ids:
        w = norm_text(BLOCKS[rb]["text"]); sh = shingles(w)
        best = None
        if sh:
            c = Counter()
            for x in sh:
                for bid in idx.get(x, ()): c[bid] += 1
            for bid, n in c.most_common(5):
                cont = n/len(sh)
                if best is None or cont > best[1]: best = (bid, cont)
        if (best is None or best[1] < 0.5) and 1 <= len(w) <= 12:  # short block: substring search
            needle = " ".join(w)
            for bid, b in sq_blocks.items():
                if needle and needle in " ".join(b["_w"]): best = (bid, 1.0); break
        if best and best[1] >= 0.5:
            b = sq_blocks[best[0]]
            align[rb] = {"block_id": b["block_id"], "doc_id": b["doc_id"], "page": b["page"], "block": b["block"], "score": round(best[1],2)}
    doc_hits = Counter(a["doc_id"] for a in align.values())
    docs = [d for d in cand_docs if doc_hits[d] >= max(3, 0.1*len(align))] or cand_docs[:1]
    # ---- subject + person matching
    itv_rows = [r for d in docs for r in S["doc_interviewees"].get(d, [])]
    def match_subject(pid):
        it = ITEMS.get(pid, {}); q = it.get("wd_qid"); nm = norm_name(it.get("label"))
        for r in itv_rows:
            if q and r["qid"] == q: return r
        for r in itv_rows:
            if norm_name(r["label"]) == nm: return r
        return None
    persons = [p for d in docs for p in S["persons"].get(d, [])]
    by_qid = defaultdict(list); by_name = defaultdict(list)
    for p in persons:
        if p["qid"]: by_qid[p["qid"]].append(p)
        names = {norm_name(p["canonical"])} | {norm_name(x) for x in json.loads(p["surface_forms"] or "[]")}
        if p["wd_label"]: names.add(norm_name(p["wd_label"]))
        for n in names:
            if n: by_name[n].append(p)
    def match_person(oid):
        it = ITEMS.get(oid, {}); q = it.get("wd_qid")
        if q and by_qid.get(q): return by_qid[q], "qid"
        names = {norm_name(it.get("label"))} | {norm_name(a) for a in it.get("aliases", [])}
        hits = []
        for n in names:
            for p in by_name.get(n, []):
                if p not in hits: hits.append(p)
        if hits: return hits, "name"
        # fuzzy fallback: same first token, surname close (OCR / spelling variants: Barkan ~ Barkin)
        import difflib
        for n in names:
            if len(n.split()) < 2: continue
            for cand, ps in by_name.items():
                if len(cand.split()) < 2 or cand.split()[0] != n.split()[0]: continue
                if difflib.SequenceMatcher(None, n, cand).ratio() >= 0.88:
                    for p in ps:
                        if p not in hits: hits.append(p)
        if hits: return hits, "fuzzy"
        return [], None
    rels = [r for d in docs for r in S["relationships"].get(d, [])]
    rel_by_person = defaultdict(list)
    for r in rels: rel_by_person[(r["subject_ord"], r["person_id"])].append(r)
    # ---- pairs
    pairs = {}
    used_rel = set()
    for s in stmts:
        subj = match_subject(s["subject"])
        key = (s["subject"], s["object"])
        if key not in pairs:
            ps, how = match_person(s["object"])
            it = ITEMS.get(s["object"], {})
            pairs[key] = {"transcript": tq, "subject_item": s["subject"], "subject_label": ITEMS[s["subject"]]["label"],
                          "subject_ord": subj["ord"] if subj else None, "subject_matched": bool(subj),
                          "object_item": s["object"], "object_label": it.get("label"), "object_wd": it.get("wd_qid"),
                          "object_desc": it.get("description"),
                          "sqlite_persons": [{"person_id": p["person_id"], "doc_id": p["doc_id"], "canonical": p["canonical"], "qid": p["qid"],
                                              "count": p["count"], "surface_forms": json.loads(p["surface_forms"] or "[]")} for p in ps],
                          "person_match": how, "semlab": [], "sqlite": []}
        refs = []
        for b in s["ref_blocks"]:
            if BLOCKS.get(b,{}).get("parent") != tq: continue
            bl = BLOCKS[b]; a = align.get(b)
            refs.append({"block": b, "local_id": bl["local_id"], "text": bl["text"], "speaker": ITEMS.get(bl["speaker"],{}).get("label") if bl["speaker"] else None, "aligned": a})
        pairs[key]["semlab"].append({"stmt_id": s["stmt_id"], "relation": PROP.get(s["prop"], s["prop"]), "method": METHOD.get(s["method"], s["method"]),
                                     "consensus": int(s["consensus"]) if s["consensus"] else None, "refs": refs})
    for key, P in pairs.items():
        if P["subject_ord"] is None: continue
        for sp in P["sqlite_persons"]:
            for r in rel_by_person.get((P["subject_ord"], sp["person_id"]), []):
                used_rel.add(r["rel_id"])
                P["sqlite"].append({"rel_id": r["rel_id"], "doc_id": r["doc_id"], "canonical": r["canonical"], "qid": r["person_qid"], "relation": r["relation"],
                                    "direction": r["direction"], "directed": directed(r["relation"], r["direction"]) if r["relation"] else None,
                                    "confidence": r["confidence"], "proposed": r["proposed"], "evidence": r["evidence"], "evidence_speaker": r["evidence_speaker"],
                                    "skipped": r["skipped"], "model": r["model"], "audit": r["audit"], "sources": r["sources"]})
    # SQLite relationships not covered by any semlab statement
    itv_by_ord = {r["ord"]: r for r in itv_rows}
    for r in rels:
        if r["rel_id"] in used_rel or r["skipped"]: continue
        subj = itv_by_ord.get(r["subject_ord"])
        key = ("sqlite", r["rel_id"])
        pairs[key] = {"transcript": tq, "subject_item": None, "subject_label": subj["label"] if subj else r["subject"], "subject_ord": r["subject_ord"], "subject_matched": True,
                      "object_item": None, "object_label": r["canonical"], "object_wd": r["person_qid"], "object_desc": None,
                      "sqlite_persons": [{"person_id": r["person_id"], "doc_id": r["doc_id"], "canonical": r["canonical"], "qid": r["person_qid"]}],
                      "person_match": None, "semlab": [],
                      "sqlite": [{"rel_id": r["rel_id"], "doc_id": r["doc_id"], "canonical": r["canonical"], "qid": r["person_qid"], "relation": r["relation"],
                                  "direction": r["direction"], "directed": directed(r["relation"], r["direction"]), "confidence": r["confidence"],
                                  "proposed": r["proposed"], "evidence": r["evidence"], "evidence_speaker": r["evidence_speaker"], "skipped": None,
                                  "model": r["model"], "audit": r["audit"], "sources": r["sources"]}]}
    # ---- verdicts
    for key, P in pairs.items():
        crowd = sorted({x["relation"] for x in P["semlab"] if x["method"] == "crowd"})
        ner = any(x["method"] == "ner" for x in P["semlab"])
        sq = [x for x in P["sqlite"] if not x["skipped"] and x["relation"]]
        skipped = [x["skipped"] for x in P["sqlite"] if x["skipped"]]
        sq_rel = sq[0]["directed"] if sq else None
        P["crowd_relations"] = crowd; P["ner"] = ner; P["sqlite_relation"] = sq_rel
        P["sqlite_confidence"] = sq[0]["confidence"] if sq else None
        P["consensus_max"] = max([x["consensus"] or 0 for x in P["semlab"] if x["method"]=="crowd"], default=None)
        if crowd and sq_rel:
            if sq_rel in crowd: v = "agree"
            elif any(TIER.get(sq_rel) == TIER.get(c) or (TIER.get(sq_rel), TIER.get(c)) in NEAR for c in crowd): v = "near"
            elif sq_rel == "knows of": v = "llm_weaker"      # human asserted a tie, LLM only 'knows of'
            else: v = "differ"
        elif crowd and not sq_rel:
            if not P["subject_matched"]: v = "subject_unmatched"
            elif not P["sqlite_persons"]: v = "human_only_person_missing"   # person never detected by the LLM pipeline
            elif skipped: v = "human_only_skipped"                           # LLM pipeline skipped the person (not a person / host ...)
            else: v = "human_only_no_relation"                               # person detected but no relationship row
        elif ner and sq_rel:
            v = "agree" if sq_rel == "knows of" else "llm_upgraded"          # human only tagged the name; LLM asserted a tie
        elif ner and not sq_rel:
            v = "ner_only_person_missing" if not P["sqlite_persons"] else ("ner_only_skipped" if skipped else "ner_only_no_relation")
        elif not P["semlab"] and sq_rel:
            v = "llm_only"
        else: v = "other"
        P["verdict"] = v
        # evidence: same passage?
        # same passage: judge on the blocks behind the crowd's judgment; fall back to name-tag blocks only when there is no crowd statement
        judged_stmts = [x for x in P["semlab"] if x["method"] == "crowd"] or P["semlab"]
        sem_blocks = {a["aligned"]["block_id"] for x in judged_stmts for a in x["refs"] if a["aligned"]}
        sq_blocks_ = {s_["block_id"] for x in P["sqlite"] for s_ in x["sources"]}
        P["same_passage"] = bool(sem_blocks & sq_blocks_) if (sem_blocks and sq_blocks_) else None
        pairs_all.append(P)
    vc = Counter(P["verdict"] for P in pairs.values())
    cv = Counter(P["verdict"] for P in pairs.values() if P["crowd_relations"])
    judged = cv["agree"]+cv["near"]+cv["differ"]+cv["llm_weaker"]
    doc_meta = [S["documents"][d] for d in docs]
    transcripts.append({"transcript": tq, "label": T["label"], "source": T["source"], "collection": T["collection"], "dates": T["dates"],
                        "semlab_source_url": T["source_url"], "md5": T["md5"], "interviewees": T["interviewees"],
                        "sqlite_docs": [{"doc_id": d["doc_id"], "title": d["title"], "interviewee": d["interviewee"], "num_blocks": d["num_blocks"],
                                         "source_url": d["source_url"], "transcript_url": d["transcript_url"], "audited": d["audited"]} for d in doc_meta],
                        "candidate_docs_dropped": [d for d in cand_docs if d not in docs],
                        "n_ref_blocks": len(ref_ids), "n_aligned": len(align), "align_by_doc": dict(doc_hits),
                        "n_statements": len(stmts), "n_crowd": sum(1 for s in stmts if METHOD.get(s["method"])=="crowd"),
                        "n_ner": sum(1 for s in stmts if METHOD.get(s["method"])=="ner"),
                        "n_sqlite_rels": sum(1 for r in rels if not r["skipped"]), "n_sqlite_persons": len(persons),
                        "verdicts": dict(vc), "crowd_verdicts": dict(cv), "crowd_pairs": sum(cv.values()),
                        "crowd_agree_rate": round((cv["agree"]+cv["near"])/judged, 3) if judged else None,
                        "crowd_exact_rate": round(cv["agree"]/judged, 3) if judged else None})
    print(f"{tq:7} {T['label'][:44]:44} refs {len(ref_ids):4} aligned {len(align):4}  crowd {transcripts[-1]['n_crowd']:3} ner {transcripts[-1]['n_ner']:3} sq {transcripts[-1]['n_sqlite_rels']:3}  "
          f"agree {vc['agree']:3} near {vc['near']:3} differ {vc['differ']:3} weaker {vc['llm_weaker']:3} h-only {vc['human_only_person_missing']+vc['human_only_no_relation']+vc['human_only_skipped']:3} llm-only {vc['llm_only']:3} up {vc['llm_upgraded']:3}  docs {docs} drop {transcripts[-1]['candidate_docs_dropped']}")

# ---- aggregates
agg = {"verdicts": Counter(P["verdict"] for P in pairs_all),
       "crowd_verdicts": Counter(P["verdict"] for P in pairs_all if P["crowd_relations"]),
       "ner_only_verdicts": Counter(P["verdict"] for P in pairs_all if P["ner"] and not P["crowd_relations"]),
       "crowd_relation_dist": Counter(x["relation"] for P in pairs_all for x in P["semlab"] if x["method"]=="crowd"),
       "sqlite_relation_dist": Counter(P["sqlite_relation"] for P in pairs_all if P["sqlite_relation"]),
       "by_collection": {c: Counter(P["verdict"] for P in pairs_all if next(t for t in transcripts if t["transcript"]==P["transcript"])["collection"]==c) for c in ("hamilton","si","rutgers")},
       "confusion": Counter(), "confusion_pairs": Counter(), "by_confidence": defaultdict(Counter), "by_consensus": defaultdict(Counter),
       "person_match": Counter(), "same_passage": Counter()}
for P in pairs_all:
    if P["crowd_relations"]:
        for c in P["crowd_relations"]:
            agg["confusion"][(c, P["sqlite_relation"] or "—")] += 1
        agg["person_match"][P["person_match"] or "none"] += 1
        agg["by_consensus"][P["consensus_max"]][P["verdict"]] += 1
    if P["sqlite_relation"] and P["verdict"] in ("agree","near","differ","llm_weaker"):
        b = P["sqlite_confidence"]; bucket = "≥0.9" if b and b>=0.9 else "0.8" if b and b>=0.8 else "0.7" if b and b>=0.7 else "<0.7"
        agg["by_confidence"][bucket][P["verdict"]] += 1
        agg["same_passage"][str(P["same_passage"])] += 1
agg["confusion"] = [{"human": k[0], "llm": k[1], "n": v} for k, v in sorted(agg["confusion"].items(), key=lambda x: -x[1])]
agg["by_confidence"] = {k: dict(v) for k, v in agg["by_confidence"].items()}
agg["by_consensus"] = {str(k): dict(v) for k, v in agg["by_consensus"].items()}
agg["verdicts"] = dict(agg["verdicts"]); agg["crowd_verdicts"] = dict(agg["crowd_verdicts"]); agg["ner_only_verdicts"] = dict(agg["ner_only_verdicts"])
agg["crowd_relation_dist"] = dict(agg["crowd_relation_dist"]); agg["sqlite_relation_dist"] = dict(agg["sqlite_relation_dist"]); agg["by_collection"] = {k: dict(v) for k, v in agg["by_collection"].items()}
agg["person_match"] = dict(agg["person_match"]); agg["same_passage"] = dict(agg["same_passage"])
agg["totals"] = {"transcripts": len(transcripts), "pairs": len(pairs_all), "ref_blocks": sum(t["n_ref_blocks"] for t in transcripts),
                 "aligned": sum(t["n_aligned"] for t in transcripts), "crowd": sum(t["n_crowd"] for t in transcripts), "ner": sum(t["n_ner"] for t in transcripts),
                 "sqlite_rels": sum(t["n_sqlite_rels"] for t in transcripts)}
json.dump({"transcripts": transcripts, "pairs": pairs_all, "agg": agg, "tiers": TIER, "prop": PROP}, open("data/comparison.json","w"))
print(json.dumps(agg["totals"])); print(json.dumps(agg["verdicts"], indent=0)); print(agg["person_match"], agg["same_passage"])
print("confusion top:"); [print(f"  {c['human']:22} -> {c['llm']:22} {c['n']}") for c in agg["confusion"][:40]]
