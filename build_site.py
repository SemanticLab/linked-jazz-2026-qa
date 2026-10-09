"""Slim comparison.json into site/data.js (embedded, works over file://)."""
import json
C = json.load(open("data/comparison.json"))
def cut(s, n=700): return s if not s or len(s) <= n else s[:n] + " …"
pairs = []
for i, P in enumerate(C["pairs"]):
    pairs.append({"id": i, "t": P["transcript"], "sl": P["subject_label"], "si": P["subject_item"], "so": P["subject_ord"],
        "ol": P["object_label"], "oi": P["object_item"], "ow": P["object_wd"], "od": P["object_desc"],
        "sp": [{"c": x["canonical"], "q": x["qid"], "n": x.get("count"), "sf": x.get("surface_forms", [])[:8], "pid": x["person_id"]} for x in P["sqlite_persons"]],
        "pm": P["person_match"], "v": P["verdict"], "cr": P["crowd_relations"], "ner": P["ner"], "lr": P["sqlite_relation"],
        "lc": P["sqlite_confidence"], "cm": P["consensus_max"], "same": P["same_passage"],
        "h": [{"rel": x["relation"], "m": x["method"], "con": x["consensus"], "id": x["stmt_id"],
               "refs": [{"b": r["block"], "lid": r["local_id"], "txt": cut(r["text"]), "spk": r["speaker"],
                         "al": {"d": r["aligned"]["doc_id"], "p": r["aligned"]["page"], "b": r["aligned"]["block"], "s": r["aligned"]["score"]} if r["aligned"] else None} for r in x["refs"]]}
              for x in P["semlab"]],
        "l": [{"id": x["rel_id"], "d": x["doc_id"], "rel": x["relation"], "dir": x["direction"], "dr": x["directed"], "conf": x["confidence"],
               "prop": cut(x["proposed"], 300), "ev": cut(x["evidence"], 600), "evs": x["evidence_speaker"], "skip": x["skipped"], "model": x["model"],
               "audit": (lambda a: (a.get("change") if isinstance(a, dict) else None))(json.loads(x["audit"]) if x["audit"] and x["audit"].startswith("{") else {}),
               "src": [{"p": s["page"], "b": s["block"], "spk": s["speaker"], "txt": cut(s["text"], 500)} for s in x["sources"][:4]]} for x in P["sqlite"]]})
out = {"transcripts": C["transcripts"], "pairs": pairs, "agg": C["agg"], "tiers": C["tiers"], "generated": __import__("datetime").date.today().isoformat()}
s = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
open("site/data.js", "w").write("window.QA_DATA=" + s + ";")
print("site/data.js", round(len(s)/1e6, 1), "MB", len(pairs), "pairs")
