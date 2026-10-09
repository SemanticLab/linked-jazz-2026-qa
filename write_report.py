import json
from collections import Counter, defaultdict
C = json.load(open("data/comparison.json")); P = C["pairs"]; T = C["transcripts"]; A = C["agg"]
tcoll = {t["transcript"]: t for t in T}
crowd = [p for p in P if p["crowd_relations"]]
J = [p for p in crowd if p["verdict"] in ("agree","near","differ","llm_weaker")]
ner = [p for p in P if p["ner"] and not p["crowd_relations"]]
llm_only = [p for p in P if p["verdict"]=="llm_only"]
def vc(xs): return Counter(p["verdict"] for p in xs)
def pc(a,b): return f"{100*a/b:.0f}%" if b else "–"
def rate_row(label, xs):
    c = vc(xs); n = sum(c[k] for k in ("agree","near","differ","llm_weaker"))
    return f"| {label} | {n} | {pc(c['agree'],n)} | {pc(c['agree']+c['near'],n)} | {pc(c['llm_weaker'],n)} | {pc(c['differ'],n)} |"
cv = vc(crowd); av = vc(P)
tot = A["totals"]
L = []
w = L.append
w("# Human judgments vs the LLM pipeline: Linked Jazz relationship QA\n")
w(f"Generated {__import__('datetime').date.today().isoformat()} from `linked_jazz.sqlite` (schema v2.1) and base.semlab.io. Explore every pair in `site/index.html`.\n")
w("## Summary\n")
w(f"- **{tot['transcripts']} transcripts** exist on both sides: {sum(1 for t in T if t['collection']=='hamilton')} Hamilton College, {sum(1 for t in T if t['collection']=='si')} Smithsonian, {sum(1 for t in T if t['collection']=='rutgers')} Rutgers (Mary Lou Williams). The Weeksville, University of Michigan and UCLA transcripts in the Wikibase have no counterpart in the SQLite corpus.")
w(f"- The human layer on those transcripts holds **{tot['crowd']:,} crowdsourced relationship statements** (52nd Street game, {len(crowd)} distinct interviewee→person pairs) and **{tot['ner']:,} supervised name tags** (stored as *knows of*). The LLM pipeline holds **{tot['sqlite_rels']:,} relationship rows** in the same documents.")
w(f"- Of the {len(J)} crowd pairs that both sides classified, the LLM gives the **same relation in {pc(cv['agree'],len(J))}** and the same or a near-synonymous relation in **{pc(cv['agree']+cv['near'],len(J))}**. In {pc(cv['llm_weaker'],len(J))} the LLM only recorded *knows of* where a user asserted a tie, and **{pc(cv['differ'],len(J))} ({cv['differ']} pairs) are real disagreements**.")
c2 = [p for p in J if (p["consensus_max"] or 0) >= 2]; c3 = [p for p in J if (p["consensus_max"] or 0) >= 3]
w(f"- Agreement tracks crowd consensus: where at least two users agreed ({len(c2)} pairs) exact agreement is {pc(vc(c2)['agree'],len(c2))} and exact-or-near {pc(vc(c2)['agree']+vc(c2)['near'],len(c2))}; with three or more users ({len(c3)} pairs) it is {pc(vc(c3)['agree'],len(c3))} and {pc(vc(c3)['agree']+vc(c3)['near'],len(c3))}. Single-vote statements ({len([p for p in J if (p['consensus_max'] or 0)==1])} pairs) are where the two sides diverge.")
w(f"- Entity coverage: the LLM pipeline has a person entry for **{pc(sum(1 for p in crowd if p['sqlite_persons']),len(crowd))}** of the people the crowd tied to an interviewee and **{pc(sum(1 for p in ner if p['sqlite_persons']),len(ner))}** of the names the supervised tagger found. It also asserts ties for **{len(llm_only):,} people the human layer never tagged** ({sum(1 for p in llm_only if p['object_wd'])} of them reconciled to Wikidata; {sum(1 for p in llm_only if p['sqlite_relation']!='knows of')} with a relation stronger than *knows of*).")
w(f"- Both sides cite the same passage for {pc(sum(1 for p in J if p['same_passage']), len(J))} of judged pairs; {pc(A['totals']['aligned'], A['totals']['ref_blocks'])} of the human reference blocks could be located in the new transcript text.\n")
w("## Crowd-judged pairs\n")
w("| slice | judged pairs | exact | exact or near | LLM weaker (*knows of*) | differ |\n|---|---|---|---|---|---|")
w(rate_row("all", J))
for k in (1,2,3): w(rate_row(f"consensus {'= 1' if k==1 else '≥ '+str(k)}", [p for p in J if ((p["consensus_max"] or 0) == 1 if k==1 else (p["consensus_max"] or 0) >= k)]))
w(rate_row("one relation chosen by the crowd", [p for p in J if len(p["crowd_relations"])==1]))
w(rate_row("several relations chosen", [p for p in J if len(p["crowd_relations"])>1]))
for coll, name in (("hamilton","Hamilton College"),("si","Smithsonian"),("rutgers","Rutgers")): w(rate_row(name, [p for p in J if tcoll[p["transcript"]]["collection"]==coll]))
for lo, hi, name in ((0.9, 2, "LLM confidence ≥ 0.9"), (0.8, 0.9, "0.8–0.89"), (0, 0.8, "< 0.8")): w(rate_row(name, [p for p in J if p["sqlite_confidence"] is not None and lo <= p["sqlite_confidence"] < hi]))
w("")
w("Verdict definitions: **agree** = the LLM relation is one the crowd chose for the pair (users could pick several); **near** = same tier (working-musician ties: played with / in music group with / toured with / collaborated with / played under; casual ties: has met / acquaintance of / friend of; formative ties: mentor of / mentored by / influenced by); **LLM weaker** = the LLM row is *knows of*; **differ** = incompatible relations.\n")
w("### By human relation\n")
w("| crowd relation | statements judged | LLM exact | LLM near | LLM *knows of* | LLM differs |\n|---|---|---|---|---|---|")
per = defaultdict(Counter)
for p in J:
    for c in p["crowd_relations"]:
        per[c]["n"] += 1
        if p["sqlite_relation"] == c: per[c]["exact"] += 1
        elif p["verdict"] in ("agree","near"): per[c]["near"] += 1
        elif p["sqlite_relation"] == "knows of": per[c]["weaker"] += 1
        else: per[c]["differ"] += 1
for k, v in sorted(per.items(), key=lambda x: -x[1]["n"]): w(f"| {k} | {v['n']} | {pc(v['exact'],v['n'])} | {pc(v['near'],v['n'])} | {pc(v['weaker'],v['n'])} | {pc(v['differ'],v['n'])} |")
w("")
w("Reading the table: the crowd's *played with*, *played under*, *in music group with* and *collaborated with* are reproduced almost always (exact or near). *Has met*, *acquaintance of*, *friend of* and *influenced by* are the loose end. The crowd applied *influenced by* to passages such as hearing a record on the family Victrola, and *friend of* to people who merely lived nearby; the LLM calls those *knows of*. Human *mentor of* was applied in both directions (the 52nd Street property list had no *mentored by*), so it is matched against the LLM's *mentored by*.\n")
w("### Where the two sides disagree outright\n")
cc = Counter()
for p in P:
    if p["verdict"]=="differ":
        for c in p["crowd_relations"]: cc[(c, p["sqlite_relation"])] += 1
w("| crowd says | LLM says | pairs |\n|---|---|---|")
for (h, l), n in cc.most_common(12): w(f"| {h} | {l} | {n} |")
w("")
w(f"Most of the {cv['differ']} disagreements pit a casual human label (*has met*, *acquaintance of*, *friend of*) against a working relationship from the LLM (*played with*, *in music group with*, *collaborated with*), i.e. the LLM read the band membership out of the passage where a user picked the weakest safe option. The reverse (crowd asserts a formative or working tie, LLM finds only acquaintance) is rarer. Each pair, with both evidence passages, is listed under *Differ* in the explorer.\n")
w("### Human ties the LLM pipeline lacks\n")
hm = [p for p in P if p["verdict"]=="human_only_person_missing"]; hs = [p for p in P if p["verdict"]=="human_only_skipped"]
w(f"- **{len(hm)} crowd-tied people have no person entry** in the LLM document. They are mostly names the new pipeline spelled differently or left unlinked: " + ", ".join(sorted({p['object_label'] for p in hm}))[:900] + ".")
w(f"- **{len(hs)} were detected but skipped** by the LLM pipeline (reasons: {', '.join(sorted({p['sqlite'][0]['skipped'] for p in hs if p['sqlite']}))}); the Bill Berry / Buster Cooper joint interview accounts for the *co_subject_only* cases, where the crowd attributed Buster Cooper's bands to Bill Berry.")
w(f"- **{len([p for p in P if p['verdict']=='llm_weaker'])} LLM weaker** pairs: the LLM has the person as a bare *knows of*. {sum(1 for p in P if p['verdict']=='llm_weaker' and (p['consensus_max'] or 0)==1)} of them rest on a single user's vote; the {sum(1 for p in P if p['verdict']=='llm_weaker' and (p['consensus_max'] or 0)>=2)} with consensus ≥ 2 are the first place to look for LLM under-classification.\n")
w("## The name-tag layer (supervised NER)\n")
nv = vc(ner)
w(f"{len(ner):,} people appear in the human layer only as tagged names. The LLM pipeline has a person entry for {sum(1 for p in ner if p['sqlite_persons']):,} of them ({pc(sum(1 for p in ner if p['sqlite_persons']),len(ner))}); it keeps {nv['agree']:,} as *knows of* and asserts a real relationship for **{nv['llm_upgraded']:,}**. {nv['ner_only_person_missing']} tagged names have no LLM person entry and {nv['ner_only_skipped']} were skipped (host, not a person). The old tagger only recognised names from a fixed list of jazz musicians, which is why the LLM's {len(llm_only):,} additional people are mostly recall gains rather than errors; relation distribution of those LLM-only ties: " + ", ".join(f"{k} {v}" for k, v in Counter(p['sqlite_relation'] for p in llm_only).most_common(6)) + ".\n")
w("## Per transcript\n")
w("| transcript | archive | crowd pairs | exact | exact or near | weaker | differ | human only | LLM upgraded | LLM only | tags missed | blocks aligned |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
for t in sorted(T, key=lambda t: -(t["crowd_pairs"] or 0)):
    c = t["crowd_verdicts"]; v = t["verdicts"]
    w(f"| {t['label'].replace(' Interview','')} | {t['collection']} | {t['crowd_pairs']} | {('%d%%' % (100*t['crowd_exact_rate'])) if t['crowd_exact_rate'] is not None else '–'} | {('%d%%' % (100*t['crowd_agree_rate'])) if t['crowd_agree_rate'] is not None else '–'} | {c.get('llm_weaker',0)} | {c.get('differ',0)} | {c.get('human_only_person_missing',0)+c.get('human_only_skipped',0)+c.get('human_only_no_relation',0)} | {v.get('llm_upgraded',0)} | {v.get('llm_only',0)} | {v.get('ner_only_person_missing',0)+v.get('ner_only_skipped',0)} | {pc(t['n_aligned'], t['n_ref_blocks'])} |")
w("")
worst = sorted([t for t in T if (t["crowd_pairs"] or 0) >= 10], key=lambda t: t["crowd_agree_rate"] or 0)[:5]
w("Lowest agreement with at least ten crowd pairs: " + "; ".join(f"{t['label'].replace(' Interview','')} ({pc(t['crowd_verdicts'].get('agree',0)+t['crowd_verdicts'].get('near',0), sum(t['crowd_verdicts'].get(k,0) for k in ('agree','near','differ','llm_weaker')))})" for t in worst) + ". In these interviews a few users voted many loose ties (Ron Carter, Oscar Peterson, Benny Powell) on passages that only name a person; the LLM holds them at *knows of*.\n")
w("## Method\n")
w("""1. **Harvest (semlab).** `harvest_semlab.py` lists transcript items (`P1` = interview transcript) with source, interviewee and dates via SPARQL, then uses the `wbgetentities` API (batches of 20, `User-Agent: semlab-data-process`) to fetch each overlapping interviewee's item, every statement carrying a *relationship generation method* qualifier (`P25`: supervised NER `Q18800` / crowdsourced 52nd St `Q18801`) with its *user consensus* (`P40`) and *reference block* references (`P26`), the block items (parent transcript `P24`, local id `P17`, text `P19`, speaker `P23`) and the object persons (label, Wikidata `P8`, aliases). `harvest_reverse.py` checked object items for statements pointing back at the interviewee and found none. Bulk SPARQL over statements times out behind Cloudflare (524 after 100 s), hence the API route.
2. **Extract (SQLite).** `extract_sqlite.py` pulls documents, interviewees, participants, persons, relationships with their source blocks, and all blocks for the mapped documents.
3. **Compare.** `compare.py` aligns each human reference block to a SQLite block by word 5-gram containment (≥ 0.5; substring for short blocks), picks the SQLite session(s) the semlab transcript covers, matches subjects and object persons (Wikidata QID, then normalised name / surface forms / aliases), rewrites SQLite relation + direction into the interviewee's point of view (*played under*/interviewee → *bandleader of*; *mentor of*/target → *mentored by*; *influenced by*/interviewee → *influence on*), and assigns one verdict per interviewee→person pair.
4. **Outputs.** `data/comparison.json` (full detail), `site/index.html` + `site/data.js` (explorer: overview, per-transcript table, pair explorer with both evidence passages and deep links to the transcript reader, semlab and Wikidata, relation matrix, CSV export), this report.

Caveats: the crowd data is not a gold standard (mostly single votes; the 52nd Street interface showed a question/answer pair so references often point at the question turn); SQLite rows are the audited layer, so "LLM" here means LLM classification corrected by the Opus audit, not raw model output; agreement for pairs with several crowd relations is generous by construction.
""")
open("REPORT.md","w").write("\n".join(L))
print("REPORT.md written", len("\n".join(L)))
