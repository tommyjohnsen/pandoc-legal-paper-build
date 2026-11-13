<!-- PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl. -->
# Fictional academic footnote demonstration

[Editable DOCX](paper.docx) · [PDF](paper.pdf) · [page 1](page-1.png) ·
[page 2](page-2.png) · [all acceptance pages](contact-sheet.png)

This short test paper has **20 native footnotes**, **204 main-text words**,
**281 footnote words**, and **2 rendered PDF pages**. It is not a Capstone-length
manuscript. Every source, court, person and institution is fictional; the web
address uses example.org. Sources: ../sample/academic.md and
../sample/academic-references.json.

The demo explicitly uses Liberation Serif, not the guide's required Times New
Roman. The body is double spaced; notes are single spaced. The 12pt body, 10pt
notes and one-inch margins are example choices, not school requirements.
PDF small capitals use TeX Gyre Termes; DOCX uses native smallCaps run properties.

verification.json records connected DOCX footnote ids, PDF reference sequence,
complete note-text comparison and actual page count. PDF text extraction returns
small capitals as uppercase; only those explicitly marked DOCX runs are normalized
for comparison. Line breaks/heading sizes/pagination can differ in Word. Word
pagination/editing was not exercised in Microsoft Word on this host.

The as-built manifest is preserved. Its output list also covers private-build
intermediates not copied into this public packet. packet-checksums.json covers
the curated packet; visual observations are recorded separately below and in
../docs/test-results.md. The verifier intentionally leaves visual_review PENDING;
that field is not overwritten to manufacture an automated visual approval.

All 12 acceptance pages were inspected in a contact sheet. Both demo pages and
the dense altered/continuation/last pages were inspected at full size. No clipping,
missing glyphs or note/body overlap was observed. The continued note spans pages
1–2 of an eight-page stress paper. Its large note region and the demo's whitespace
are deliberate consequences of the synthetic content and TeX page composition.
This is a layout observation by the author, not independent code review or a
human Bluebook review.

Rebuild with `source tools/env.sh; make demo` in a fresh build directory.
Run `make test` and `make integration` for the complete acceptance suite.
Human review remains required under ../docs/citation-review.md. No automatic
Bluebook compliance, proposition support, current authority or publication
readiness is claimed.
