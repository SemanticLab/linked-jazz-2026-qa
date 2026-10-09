"""Second pass: statements on OTHER person items (the objects) whose reference blocks sit in an overlap transcript."""
import json, os, sys
sys.argv = ["x"]; exec(open("harvest_semlab.py").read().split("# ---- 1. overlap list")[0])  # reuse helpers
h = json.load(open("data/semlab_harvest.json"))
tset = {t["transcript"] for t in h["overlap"]}
have_blocks = set(h["blocks"])
known_stmts = {s["stmt_id"] for s in h["statements"]}
cand = []
for fn in os.listdir(CACHE):
    e = json.load(open(f"{CACHE}/{fn}"))
    if "Q1" not in [val(c["mainsnak"]) for c in e.get("claims", {}).get("P1", [])]: continue  # persons only
    for prop, cl in e.get("claims", {}).items():
        for c in cl:
            if "P25" not in c.get("qualifiers", {}) or c["id"] in known_stmts: continue
            refs = [val(s) for ref in c.get("references", []) for s in ref.get("snaks", {}).get("P26", [])]
            cand.append({"stmt_id": c["id"], "subject": e["id"], "prop": prop, "object": val(c["mainsnak"]),
                         "method": val(c["qualifiers"]["P25"][0]), "consensus": val(c["qualifiers"]["P40"][0]) if "P40" in c["qualifiers"] else None,
                         "rank": c.get("rank"), "ref_blocks": refs})
print("candidate statements on object items:", len(cand), file=sys.stderr)
need = [b for s in cand for b in s["ref_blocks"] if b and b not in have_blocks]
print("blocks to fetch:", len(need), file=sys.stderr)
bents = get_entities(need)
blocks = dict(h["blocks"])
for q, e in bents.items():
    blocks[q] = {"block": q, "parent": (claims(e,"P24") or [None])[0], "local_id": (claims(e,"P17") or [None])[0],
                 "text": (claims(e,"P19") or [None])[0], "speaker": (claims(e,"P23") or [None])[0],
                 "text_url": (claims(e,"P20") or [None])[0], "entities": claims(e,"P21"), "label": label(e)}
keep = [s for s in cand if any(blocks.get(b, {}).get("parent") in tset for b in s["ref_blocks"])]
print("reverse statements in overlap transcripts:", len(keep), file=sys.stderr)
from collections import Counter
print(Counter(s["method"] for s in keep), Counter(s["prop"] for s in keep).most_common(), file=sys.stderr)
print("objects of reverse stmts that are overlap interviewees:", sum(1 for s in keep if any(s["object"] in t["interviewees"] for t in h["overlap"])), file=sys.stderr)
# objects of reverse statements may be new items -> fetch labels
newobj = [s["object"] for s in keep if s["object"] not in h["items"]] + [b["speaker"] for b in blocks.values() if b["speaker"] and b["speaker"] not in h["items"]]
oents = get_entities(newobj)
for q, e in oents.items():
    h["items"][q] = {"label": label(e), "description": e.get("descriptions",{}).get("en",{}).get("value"),
                     "wd_qid": (claims(e,"P8") or [None])[0], "instance_of": claims(e,"P1"), "slug": (claims(e,"P7") or [None])[0]}
for s in keep: s["reverse"] = True
h["statements"] += keep; h["blocks"] = blocks
# aliases for all person items in cache (helps name matching)
for fn in os.listdir(CACHE):
    e = json.load(open(f"{CACHE}/{fn}"))
    if e["id"] in h["items"]:
        h["items"][e["id"]]["aliases"] = [a["value"] for a in e.get("aliases", {}).get("en", [])]
json.dump(h, open("data/semlab_harvest.json","w"), indent=1)
print("total statements now:", len(h["statements"]), file=sys.stderr)
