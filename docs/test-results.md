<!-- PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl. -->
# Validation evidence — 2026-11-13

These are author-run implementation checks, not an independent exact-commit
review and not a legal citation approval. No Capstone draft or research library
was used. All fixtures are fictional or openly licensed.

## Commands and outcomes

Setup: `python3 tools/setup.py`, then `source tools/env.sh`. Tested on Linux
x86_64 with Python 3.12.3, Node 22.14.0, Pandoc 3.6.4, Tectonic 0.15.0,
citeproc npm 2.4.63 (processor 1.4.63), PyMuPDF 1.26.6 and the locked v33 bundle.
The bootstrap was actually executed, not merely documented.

| Check | Result |
|---|---|
| make test | **29 Node tests + 4 Python tests passed**, zero skipped; vendor hashes matched. TAP/unittest evidence in ../demonstration/unit-tests.txt. |
| INTEGRATION_OUT=build/release-candidate make test integration | **PASS** for three actual DOCX/PDF builds; full numbers/content, native relationships, main-reference sequence, continuation-page notes, bounds/dimensions and preserved source hashes. All 33 unit checks also passed in the final make test invocation. The curated demo was rebuilt after the nonsemantic style whitespace/provenance updates. |
| make legacy legacy-test BUILD=build/legacy-acceptance | **PASS**: both existing engines' DOCX/PDF, citation comparison and empty-bibliography PDF regression. Missing TeX metrics required network access to the pinned bundle. |
| Plain commentary note with italic main text | **PASS**: additional actual DOCX/PDF build, one native note, 2 body words, 2 note words, 1 PDF page; prevents body typography from creating false footnote-format requirements. |
| git diff --check | Passed before commit. |
| Docker image / GitHub Actions | Configuration prepared with immutable base/action digests; Docker was unavailable on the author host. Container execution/remote CI must be assessed separately; no green-CI claim is made here. |
| Times New Roman rendering / Microsoft Word pagination | **NOT RUN**: font and Word unavailable. Missing-font failure is tested; demo explicitly uses Liberation Serif. |
| Human Bluebook / authority currency / proposition support | **PENDING**, intentionally outside formatting automation. |

## Rendered results

| Synthetic build | Body / note size; margins | Native notes | Main words | Note words | PDF pages |
|---|---|---:|---:|---:|---:|
| Academic demonstration | 12 / 10pt; 1in | 20 | 204 | 281 | 2 |
| Same source, alternative layout | 11 / 9pt; 0.8in | 20 | 204 | 281 | 2 |
| Long-note stress source | 12 / 10pt; 1in | 3 | 2,453 | 1,232 | 8 |

Both ordinary layouts contain all seven source types, citation-only/explanatory
notes, several clusters in a note, repeated authorities, changed and unchanged
Id., book/journal supra, case short forms, signals, suffixes and varied locators.
The long note actually continues across pages 1–2; supra thereafter points to note
1. DOCX footnote references and ids are one-to-one and continuous. The PDF main
references and complete ordered note text match the DOCX after documented
whitespace/ligature/dash and explicit-smallCaps normalization.

Checks include missing court/jurisdiction/reporter/year/section/edition metadata,
unknown/duplicate keys, malformed dates, unsupported source types, narrative and
suppressed-author modes, rich affixes, compound/ambiguous locators, disallowed
placements and legacy mapping failures. Same-author ambiguity and intervening
prose/multiple/explanatory notes prevent unsafe automatic short forms. Tests
also verify exact known main/note counts independent of note length, font-size/
margin settings, explicit missing-font failure and preserved edited-output bytes.

## Visual observations and practical limits

All 12 actual acceptance pages were rendered and inspected as a contact sheet.
Both demo pages and dense altered/first/continued/final stress pages were inspected
at full size. Italics and true PDF small capitals were visible, footnote separators
and page numbers were intact, and no clipping, replacement glyphs or note/body
overlap was observed. The long-note region intentionally occupies most of its
first page. TeX's justified short web note has wide spacing, and the demo has
substantial whitespace on its last page; neither is a legal-format approval.

PDF small-cap glyphs extract uppercase, whereas DOCX stores the original spelling
with smallCaps properties. The verifier transforms only those expected runs.
Note-text parity does not prove identical Word page breaks or line wrapping;
Word's rendering was not exercised. The verifier relies on this template's
standard TeX footnote separator; heavily customized layouts require new checks.
PDF accessibility and all Unicode font coverage are not certified.

TeX warns about absolute font access. The chosen family files and vendored
small-cap font are explicit inputs with recorded hashes. The versioned bundle
identity is checked, and the OS/container recipe is pinned; native installations
with other font versions can paginate differently. Binary-identical exports
across operating systems are not promised. Initial offline attempts failed when
metrics were absent; the documented first-run network population resolved that.

No independent APPROVE verdict is recorded by the author. Before merge/release,
Claude Code and Grok Build must review the exact proposed SHA under the mandatory
provenance policy. Those software reviews do not replace the human checklist.
