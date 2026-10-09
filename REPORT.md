# Human judgments vs the LLM pipeline: Linked Jazz relationship QA

Generated 2026-10-08 from `linked_jazz.sqlite` (schema v2.1) and base.semlab.io. Explore every pair in `site/index.html`.

## Summary

- **46 transcripts** exist on both sides: 34 Hamilton College, 11 Smithsonian, 1 Rutgers (Mary Lou Williams). The Weeksville, University of Michigan and UCLA transcripts in the Wikibase have no counterpart in the SQLite corpus.
- The human layer on those transcripts holds **1,715 crowdsourced relationship statements** (52nd Street game, 924 distinct interviewee→person pairs) and **3,464 supervised name tags** (stored as *knows of*). The LLM pipeline holds **4,415 relationship rows** in the same documents.
- Of the 895 crowd pairs that both sides classified, the LLM gives the **same relation in 37%** and the same or a near-synonymous relation in **57%**. In 32% the LLM only recorded *knows of* where a user asserted a tie, and **11% (100 pairs) are real disagreements**.
- Agreement tracks crowd consensus: where at least two users agreed (237 pairs) exact agreement is 59% and exact-or-near 72%; with three or more users (94 pairs) it is 70% and 79%. Single-vote statements (658 pairs) are where the two sides diverge.
- Entity coverage: the LLM pipeline has a person entry for **98%** of the people the crowd tied to an interviewee and **96%** of the names the supervised tagger found. It also asserts ties for **1,106 people the human layer never tagged** (507 of them reconciled to Wikidata; 574 with a relation stronger than *knows of*).
- Both sides cite the same passage for 76% of judged pairs; 90% of the human reference blocks could be located in the new transcript text.

## Crowd-judged pairs

| slice | judged pairs | exact | exact or near | LLM weaker (*knows of*) | differ |
|---|---|---|---|---|---|
| all | 895 | 37% | 57% | 32% | 11% |
| consensus = 1 | 658 | 29% | 51% | 36% | 13% |
| consensus ≥ 2 | 237 | 59% | 72% | 22% | 6% |
| consensus ≥ 3 | 94 | 70% | 79% | 17% | 4% |
| one relation chosen by the crowd | 546 | 29% | 50% | 37% | 13% |
| several relations chosen | 349 | 49% | 67% | 25% | 8% |
| Hamilton College | 653 | 37% | 56% | 33% | 11% |
| Smithsonian | 220 | 36% | 58% | 32% | 10% |
| Rutgers | 22 | 41% | 64% | 18% | 18% |
| LLM confidence ≥ 0.9 | 404 | 30% | 48% | 47% | 5% |
| 0.8–0.89 | 269 | 41% | 62% | 25% | 13% |
| < 0.8 | 222 | 43% | 66% | 14% | 20% |

Verdict definitions: **agree** = the LLM relation is one the crowd chose for the pair (users could pick several); **near** = same tier (working-musician ties: played with / in music group with / toured with / collaborated with / played under; casual ties: has met / acquaintance of / friend of; formative ties: mentor of / mentored by / influenced by); **LLM weaker** = the LLM row is *knows of*; **differ** = incompatible relations.

### By human relation

| crowd relation | statements judged | LLM exact | LLM near | LLM *knows of* | LLM differs |
|---|---|---|---|---|---|
| influenced by | 278 | 19% | 30% | 42% | 8% |
| acquaintance of | 228 | 12% | 42% | 32% | 14% |
| collaborated with | 224 | 26% | 61% | 11% | 2% |
| has met | 216 | 9% | 38% | 38% | 15% |
| friend of | 184 | 14% | 49% | 24% | 13% |
| played with | 182 | 38% | 48% | 13% | 0% |
| mentor of | 140 | 0% | 46% | 34% | 20% |
| in music group with | 99 | 34% | 55% | 10% | 1% |
| toured with | 65 | 14% | 72% | 14% | 0% |
| played under | 50 | 62% | 24% | 12% | 2% |

Reading the table: the crowd's *played with*, *played under*, *in music group with* and *collaborated with* are reproduced almost always (exact or near). *Has met*, *acquaintance of*, *friend of* and *influenced by* are the loose end. The crowd applied *influenced by* to passages such as hearing a record on the family Victrola, and *friend of* to people who merely lived nearby; the LLM calls those *knows of*. Human *mentor of* was applied in both directions (the 52nd Street property list had no *mentored by*), so it is matched against the LLM's *mentored by*.

### Where the two sides disagree outright

| crowd says | LLM says | pairs |
|---|---|---|
| has met | played with | 9 |
| mentor of | played with | 8 |
| has met | collaborated with | 7 |
| acquaintance of | in music group with | 7 |
| has met | in music group with | 7 |
| mentor of | in music group with | 6 |
| friend of | played with | 6 |
| influenced by | played with | 6 |
| influenced by | in music group with | 6 |
| acquaintance of | mentored by | 5 |
| friend of | in music group with | 5 |
| acquaintance of | collaborated with | 5 |

Most of the 100 disagreements pit a casual human label (*has met*, *acquaintance of*, *friend of*) against a working relationship from the LLM (*played with*, *in music group with*, *collaborated with*), i.e. the LLM read the band membership out of the passage where a user picked the weakest safe option. The reverse (crowd asserts a formative or working tie, LLM finds only acquaintance) is rarer. Each pair, with both evidence passages, is listed under *Differ* in the explorer.

### Human ties the LLM pipeline lacks

- **23 crowd-tied people have no person entry** in the LLM document. They are mostly names the new pipeline spelled differently or left unlinked: Benny Green, Bix Beiderbecke, Blinky Allen, Butterbeans and Susie, Count Basie, Damita Jo DeBlanc, Ezra Charles, George Gershwin, George Treadwell, Howard Burley, Jesse Belvin, Louis Aladdin, Lovie Austin, Mel Lewis, Misa Watanabe, Reginald Buckner, Richard Jeweler, Steve Allen, Stumpy Brady, Terell Stafford, Tootie Boyd.
- **6 were detected but skipped** by the LLM pipeline (reasons: co_subject_only, not_a_person, self_or_host); the Bill Berry / Buster Cooper joint interview accounts for the *co_subject_only* cases, where the crowd attributed Buster Cooper's bands to Bill Berry.
- **289 LLM weaker** pairs: the LLM has the person as a bare *knows of*. 237 of them rest on a single user's vote; the 52 with consensus ≥ 2 are the first place to look for LLM under-classification.

## The name-tag layer (supervised NER)

2,532 people appear in the human layer only as tagged names. The LLM pipeline has a person entry for 2,426 of them (96%); it keeps 1,194 as *knows of* and asserts a real relationship for **1,220**. 106 tagged names have no LLM person entry and 12 were skipped (host, not a person). The old tagger only recognised names from a fixed list of jazz musicians, which is why the LLM's 1,106 additional people are mostly recall gains rather than errors; relation distribution of those LLM-only ties: knows of 532, has met 151, played with 83, acquaintance of 78, in music group with 70, collaborated with 65.

## Per transcript

| transcript | archive | crowd pairs | exact | exact or near | weaker | differ | human only | LLM upgraded | LLM only | tags missed | blocks aligned |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Jimmy Owens Hamilton College | hamilton | 61 | 57% | 77% | 9 | 5 | 0 | 1 | 6 | 1 | 90% |
| Slide Hampton Hamilton College | hamilton | 47 | 50% | 73% | 10 | 2 | 1 | 5 | 8 | 0 | 90% |
| Red Holloway Hamilton College | hamilton | 44 | 58% | 72% | 10 | 2 | 1 | 1 | 10 | 0 | 90% |
| Buddy DeFranco Hamilton College | hamilton | 43 | 66% | 73% | 9 | 2 | 1 | 1 | 10 | 0 | 93% |
| Jimmy Scott Smithsonian | si | 40 | 55% | 70% | 10 | 2 | 0 | 3 | 33 | 3 | 94% |
| Gerald Wiggins Hamilton College | hamilton | 34 | 15% | 65% | 7 | 4 | 2 | 1 | 12 | 0 | 84% |
| Roswell Rudd Hamilton College | hamilton | 34 | 52% | 52% | 16 | 0 | 0 | 2 | 14 | 1 | 95% |
| Abbey Lincoln Smithsonian | si | 33 | 43% | 66% | 8 | 2 | 3 | 48 | 68 | 7 | 99% |
| Danny Barker Smithsonian | si | 32 | 6% | 30% | 16 | 5 | 2 | 63 | 78 | 12 | 85% |
| Roy Haynes Smithsonian | si | 31 | 32% | 71% | 7 | 2 | 0 | 82 | 38 | 10 | 83% |
| Charles Davis (saxophonist) Hamilton College | hamilton | 30 | 37% | 75% | 7 | 0 | 1 | 3 | 3 | 0 | 89% |
| Benny Powell Hamilton College | hamilton | 29 | 10% | 10% | 14 | 11 | 1 | 2 | 13 | 0 | 100% |
| Doc Cheatham Hamilton College | hamilton | 29 | 14% | 53% | 8 | 5 | 1 | 2 | 17 | 2 | 86% |
| Mona Hinton Hamilton College | hamilton | 29 | 20% | 24% | 19 | 3 | 0 | 0 | 15 | 1 | 90% |
| Oscar Peterson Hamilton College | hamilton | 29 | 17% | 20% | 12 | 11 | 0 | 0 | 10 | 0 | 94% |
| Mary Lou Williams Rutgers | rutgers | 25 | 40% | 63% | 4 | 4 | 3 | 86 | 73 | 8 | 91% |
| David Murray Hamilton College | hamilton | 23 | 43% | 65% | 5 | 3 | 0 | 0 | 7 | 0 | 76% |
| Marian McPartland Hamilton College | hamilton | 22 | 40% | 77% | 5 | 0 | 0 | 18 | 16 | 1 | 95% |
| Nancy Wilson Smithsonian | si | 22 | 54% | 59% | 7 | 2 | 0 | 48 | 48 | 10 | 89% |
| Dave Brubeck Smithsonian | si | 18 | 29% | 47% | 5 | 4 | 1 | 45 | 86 | 5 | 83% |
| Ron Carter Hamilton College | hamilton | 18 | 0% | 22% | 13 | 1 | 0 | 1 | 6 | 0 | 100% |
| Jane Jarvis Hamilton College | hamilton | 17 | 58% | 70% | 5 | 0 | 0 | 0 | 3 | 0 | 93% |
| Buddy Tate Hamilton College | hamilton | 15 | 7% | 7% | 8 | 5 | 1 | 11 | 40 | 2 | 91% |
| Herbie Hancock Hamilton College | hamilton | 15 | 60% | 66% | 5 | 0 | 0 | 1 | 4 | 0 | 100% |
| Lionel Hampton Hamilton College | hamilton | 15 | 26% | 60% | 3 | 3 | 0 | 13 | 5 | 0 | 80% |
| Vi Redd Hamilton College | hamilton | 15 | 42% | 57% | 6 | 0 | 1 | 30 | 23 | 2 | 93% |
| Clark Terry Hamilton College | hamilton | 14 | 23% | 46% | 7 | 0 | 1 | 16 | 47 | 2 | 89% |
| Delfeayo Marsalis Smithsonian | si | 12 | 25% | 66% | 3 | 1 | 0 | 31 | 18 | 3 | 95% |
| Stanley Kay Hamilton College | hamilton | 12 | 8% | 25% | 8 | 1 | 0 | 36 | 20 | 1 | 84% |
| Toshiko Akiyoshi Smithsonian | si | 12 | 18% | 36% | 6 | 1 | 1 | 59 | 46 | 5 | 95% |
| Bob Haggart Hamilton College | hamilton | 11 | 50% | 80% | 2 | 0 | 1 | 16 | 7 | 0 | 82% |
| John Levy Smithsonian | si | 11 | 36% | 63% | 3 | 1 | 0 | 87 | 37 | 5 | 95% |
| Buster Williams Hamilton College | hamilton | 10 | 20% | 60% | 3 | 1 | 0 | 15 | 7 | 1 | 87% |
| Louie Bellson Smithsonian | si | 10 | 22% | 44% | 2 | 3 | 1 | 155 | 68 | 20 | 88% |
| Billy Taylor Hamilton College | hamilton | 9 | 0% | 11% | 5 | 3 | 0 | 9 | 11 | 0 | 96% |
| Milt Hinton Hamilton College | hamilton | 9 | 77% | 77% | 1 | 1 | 0 | 41 | 35 | 1 | 91% |
| Phil Woods Hamilton College | hamilton | 9 | 22% | 66% | 3 | 0 | 0 | 48 | 28 | 3 | 90% |
| Bill Berry and Buster Cooper Hamilton College | hamilton | 8 | 25% | 50% | 1 | 1 | 4 | 3 | 29 | 5 | 83% |
| Leslie Johnson Hamilton College | hamilton | 8 | 16% | 16% | 5 | 0 | 2 | 5 | 13 | 0 | 89% |
| Annie Ross Smithsonian | si | 7 | 57% | 57% | 3 | 0 | 0 | 98 | 32 | 3 | 90% |
| Benny Waters Hamilton College | hamilton | 6 | 0% | 33% | 2 | 2 | 0 | 14 | 6 | 1 | 87% |
| Charles McPherson Hamilton College | hamilton | 6 | 16% | 16% | 4 | 1 | 0 | 12 | 6 | 0 | 88% |
| Jimmy Lewis Hamilton College | hamilton | 6 | 16% | 50% | 1 | 2 | 0 | 29 | 12 | 1 | 96% |
| Ed Shaughnessy Hamilton College | hamilton | 5 | 20% | 40% | 2 | 1 | 0 | 29 | 7 | 0 | 100% |
| Joe Williams Hamilton College | hamilton | 5 | 60% | 80% | 0 | 1 | 0 | 33 | 14 | 2 | 96% |
| Harold Ousley Hamilton College | hamilton | 4 | 25% | 50% | 0 | 2 | 0 | 17 | 17 | 0 | 88% |

Lowest agreement with at least ten crowd pairs: Buddy Tate Hamilton College (7%); Benny Powell Hamilton College (11%); Oscar Peterson Hamilton College (21%); Ron Carter Hamilton College (22%); Mona Hinton Hamilton College (24%). In these interviews a few users voted many loose ties (Ron Carter, Oscar Peterson, Benny Powell) on passages that only name a person; the LLM holds them at *knows of*.

## Method

1. **Harvest (semlab).** `harvest_semlab.py` lists transcript items (`P1` = interview transcript) with source, interviewee and dates via SPARQL, then uses the `wbgetentities` API (batches of 20, `User-Agent: semlab-data-process`) to fetch each overlapping interviewee's item, every statement carrying a *relationship generation method* qualifier (`P25`: supervised NER `Q18800` / crowdsourced 52nd St `Q18801`) with its *user consensus* (`P40`) and *reference block* references (`P26`), the block items (parent transcript `P24`, local id `P17`, text `P19`, speaker `P23`) and the object persons (label, Wikidata `P8`, aliases). `harvest_reverse.py` checked object items for statements pointing back at the interviewee and found none. Bulk SPARQL over statements times out behind Cloudflare (524 after 100 s), hence the API route.
2. **Extract (SQLite).** `extract_sqlite.py` pulls documents, interviewees, participants, persons, relationships with their source blocks, and all blocks for the mapped documents.
3. **Compare.** `compare.py` aligns each human reference block to a SQLite block by word 5-gram containment (≥ 0.5; substring for short blocks), picks the SQLite session(s) the semlab transcript covers, matches subjects and object persons (Wikidata QID, then normalised name / surface forms / aliases), rewrites SQLite relation + direction into the interviewee's point of view (*played under*/interviewee → *bandleader of*; *mentor of*/target → *mentored by*; *influenced by*/interviewee → *influence on*), and assigns one verdict per interviewee→person pair.
4. **Outputs.** `data/comparison.json` (full detail), `site/index.html` + `site/data.js` (explorer: overview, per-transcript table, pair explorer with both evidence passages and deep links to the transcript reader, semlab and Wikidata, relation matrix, CSV export), this report.

Caveats: the crowd data is not a gold standard (mostly single votes; the 52nd Street interface showed a question/answer pair so references often point at the question turn); SQLite rows are the audited layer, so "LLM" here means LLM classification corrected by the Opus audit, not raw model output; agreement for pairs with several crowd relations is generous by construction.
