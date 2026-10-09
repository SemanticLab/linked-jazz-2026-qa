import json, sqlite3
DB = "/Users/m/git/ch-jazz-mashup/linked_jazz.sqlite"
h = json.load(open("data/semlab_harvest.json"))
doc_ids = sorted({d for t in h["overlap"] for d in t["sqlite_docs"]})
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
q = lambda sql, *a: [dict(r) for r in con.execute(sql, a)]
ph = ",".join("?"*len(doc_ids))
out = {"documents": {}, "doc_interviewees": {}, "doc_participants": {}, "persons": {}, "relationships": {}, "blocks": {}}
for d in q(f"select doc_id, collection, title, interviewee, interviewer, date, year, method, source_url, num_pages, num_blocks, transcript_url, audited from documents where doc_id in ({ph})", *doc_ids):
    out["documents"][d["doc_id"]] = d
for r in q(f"select * from doc_interviewees where doc_id in ({ph}) order by doc_id, ord", *doc_ids):
    out["doc_interviewees"].setdefault(r["doc_id"], []).append(r)
for r in q(f"select * from doc_participants where doc_id in ({ph})", *doc_ids):
    out["doc_participants"].setdefault(r["doc_id"], []).append(r)
for r in q(f"select person_id, doc_id, canonical, count, confidence, surface_forms, qid, wd_label, wd_description, curation, audit from persons where doc_id in ({ph})", *doc_ids):
    out["persons"].setdefault(r["doc_id"], []).append(r)
src = {}
for r in q(f"select rs.rel_id, rs.block_id, b.page, b.block, b.speaker, b.text from relationship_sources rs join blocks b using(block_id) join relationships r using(rel_id) where r.doc_id in ({ph})", *doc_ids):
    src.setdefault(r["rel_id"], []).append({k: r[k] for k in ("block_id","page","block","speaker","text")})
for r in q(f"select r.*, p.canonical, p.qid as person_qid from relationships r join persons p using(person_id) where r.doc_id in ({ph})", *doc_ids):
    r["sources"] = src.get(r["rel_id"], [])
    out["relationships"].setdefault(r["doc_id"], []).append(r)
for r in q(f"select block_id, doc_id, page, block, type, speaker, text, audit_speaker from blocks where doc_id in ({ph}) order by doc_id, page, block", *doc_ids):
    out["blocks"].setdefault(r["doc_id"], []).append(r)
# node and edge info not needed here
json.dump(out, open("data/sqlite_side.json","w"))
print("docs", len(out["documents"]), "persons", sum(map(len,out["persons"].values())), "rels", sum(map(len,out["relationships"].values())), "blocks", sum(map(len,out["blocks"].values())))
for d in doc_ids:
    dd = out["documents"][d]
    print(d, dd["collection"], dd["interviewee"], dd["date"], dd["num_blocks"], "rels:", len(out["relationships"].get(d,[])), "itv:", [(i["label"], i["role"]) for i in out["doc_interviewees"].get(d,[])])
