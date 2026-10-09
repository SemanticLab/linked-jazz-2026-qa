# linked-jazz-2026-qa

Compares the relationships people asserted in the original Linked Jazz project
(base.semlab.io Wikibase: 52nd Street crowdsourcing + supervised name tagging)
with the LLM/audit relationships in `~/git/ch-jazz-mashup/linked_jazz.sqlite`,
on the 46 transcripts both corpora share (Hamilton College, Smithsonian, Rutgers).

- `REPORT.md` — findings.
- `site/index.html` — explorer (open directly in a browser; data embedded in `site/data.js`).
  Published at <https://semanticlab.github.io/linked-jazz-2026-qa/> via GitHub Pages
  (`.github/workflows/pages.yml` deploys `site/` on every push to `main`).

## Rebuild

```bash
# 1. transcript list + property labels (SPARQL; small queries only, bulk ones 524 behind Cloudflare)
curl -sG -A semlab-data-process "https://query.semlab.io/proxy/wdqs/bigdata/namespace/wdq/sparql" -H "Accept: text/csv" --data-urlencode 'query=...' > semlab_transcripts.csv
# 2. SQLite interviewees of the three archives (sqlite_interviewees_rhs.txt), then:
uv run python harvest_semlab.py     # wbgetentities API, cached in raw/entities/ -> data/semlab_harvest.json
uv run python harvest_reverse.py    # statements on object items (found none)
uv run python extract_sqlite.py     # -> data/sqlite_side.json
uv run python compare.py            # -> data/comparison.json
uv run python build_site.py         # -> site/data.js
uv run python write_report.py       # -> REPORT.md
```

All requests to base.semlab.io need `User-Agent: semlab-data-process` (Cloudflare rule).

## Wikibase layout (for reference)

- transcript item: `P1` instance of `Q1960` (interview transcript), `P13` interviewee, `P14` interviewer, `P15` source (Q2031 Hamilton College, Q2033 Smithsonian, Q2034 Rutgers, Q2032 U. Michigan, Q21579 Weeksville), `P16` legacy MD5, `P7` slug, `P98` date.
- block item: `P1` = `Q2013`, `P24` parent transcript, `P17` local id, `P19` text, `P20` text URL (`semlab.s3.amazonaws.com/texts/<md5>/<n>.txt`), `P23` speaker, `P21` associated entities.
- relationship statements live on the interviewee's person item (`P29` knows of … `P39` influenced by), qualified by `P25` generation method (`Q18800` supervised NER, `Q18801` crowdsourced 52nd St) and `P40` user consensus, referenced by `P26` block items.

## License

[MIT](LICENSE)
