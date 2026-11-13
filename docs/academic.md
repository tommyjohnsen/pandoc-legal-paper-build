<!-- PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl. -->
# Academic footnotes: supported syntax and limits

The pinned community Bluebook Law Review style, with the documented local
CC BY-SA derivative, is the selected academic style. It creates an academic
footnote structure and typography; it is not a complete Bluebook implementation.

## Syntax contract

Pandoc 3.6.4 parses Markdown. The renderer walks the AST in document order,
wraps each body citation cluster in a Note, and retains each existing Markdown
note as one note. Numbering includes prose-only notes. Citations are rendered
once into resolved.json, preserving semantic emphasis/small capitals. Both
writers consume that document. No bibliography or endnotes are added.

| Input | Supported behavior / diagnostic |
|---|---|
| `Text.[@case]` | New citation-only footnote; first full form. Put the marker after punctuation as required by your style. |
| `[@case, 214]`, `[@case, p. 214]` | Page locator; a bare number defaults to page. |
| `[@journal, pp. 88--90]` | Range; Pandoc smart punctuation becomes an en dash. Numeric locators can include a letter, dotted numbers and parenthesized subsections. |
| `[@statute, § 4(a)(2)]` | Section locator. sec., secs., §§ also mapped; code, section and edition retained in full citations. |
| `[@case, para. 24]`, `[@case, ¶ 24]` | Paragraph locator; visible label in full form. paras./¶¶ also mapped. |
| `[@journal, n. 4]`, `[@book, ch. 2]` | Labeled note/chapter locator, full form. |
| `[see @case, 214, discussing timing]` | Plain prefix and comma-delimited trailing prose suffix preserved. Signals are **not** automatically italicized; use explanatory notes for formatted signals. |
| `[@case, 214; @journal, 88]` | Multiple authorities, one note, input order retained; conservative full forms. |
| `[^explanation]` and definition `[^explanation]: Prose. [@case, 214]` | One editable footnote with prose and citation; no nested citation note. |
| `^[Prose. [@case, 214]]` | Inline Markdown footnote; same behavior. |
| `^[*See* [@case, 214] More prose. [@book, 12]]` | Several clusters in one explanatory note, full forms; surrounding Markdown formatting preserved. Sentence continuation suppresses the generated terminal period; an explicit following period is not duplicated. |
| Repeated case with explicit page locator | Style-generated case short form after intervening authorities; requires title-short. |
| Immediately repeated eligible single-authority citation-only note | Id. / Id. at a changed page. Cases, books and journals only, explicit page pinpoints and no affixes. Human review required. |
| Repeated unambiguous book/journal with page pinpoint | Supra targets the actual first-note number, including intervening prose-only notes. |
| Narrative `@case` / `[-@case]` | **Error**: author modes are not legal short-form instructions. Use bracketed normal citations; narrative names go in prose. |
| Rich affix `[*see* @case]` | **Error**: put the formatted signal outside the citation inside a Markdown note. |
| `[@case, appendix A]`, compound `12, 14`, Roman numeral or combined page/note locator | **Error**: one supported numeric locator/range; additional pinpoints belong in explanatory prose. |
| Unknown/duplicate ids or missing metadata | **Error** naming the key/field; repair the export. |
| Notes/citations in YAML, headings, table/figure/image captions or table cells; nested notes; raw HTML/TeX | **Error**: move to a body paragraph or native Markdown note. These placements are outside the tested cross-format contract. |
| Treaties, unpublished/parallel reporters, administrative dockets, multilingual/jurisdiction-specific CSL-M forms, custom supra/infra | Outside the contract. Unmodeled source types fail validation; extra fields on a supported type are preserved but are not guaranteed to render. Human review must detect unmodeled subtypes. |

Suffix grammar is deliberately bounded: one numeric locator/range with optional
label, then optional comma-delimited prose. Numeric lists and ambiguous unlabeled
text are rejected. Use metadata for a statutory base section and the citation
locator for the provision cited. Pandoc warnings (including unresolved note
references) fail the source parse. Normal text/code can contain literal @ signs;
a malformed construct Pandoc reads as ordinary text cannot be assumed to request
a citation. Use the documented bracketed forms and inspect the output.

## Metadata contract

Every item needs a unique nonempty string id, type, title, and issued.date-parts
with a numeric year. Metadata validation checks presence/shape, not truth.

| Type | Additional required fields | Rendering scope |
|---|---|---|
| legal_case | jurisdiction, authority (court), container-title (reporter), volume, page, title-short | Single-reporter published case, supplied court/year. No automatic abbreviation, parallel reporters or subsequent history. |
| legislation | jurisdiction, container-title (code), section, edition | Codified statute with cited section and source edition/year. Session laws, constitutions, bills and supplements need other modeling/human review. |
| regulation | Same fields as legislation | Original type retained in audit; processor copy explicitly mapped to legislation for CSL 1.0. Supply code volume where applicable. No agency/docket/Federal Register automation. |
| report, genre=bar-opinion | jurisdiction, authority, number | Institutional formal bar opinion with year and locator. Opinion identifier preserves its hyphen. Other report genres fail. |
| article-journal | author, container-title, volume, page | Italic article title, small-cap journal, first page and pinpoint. |
| book | author, publisher, edition | Small-cap author/title; numeric edition becomes ordinal. Publisher retained in audit even when style omits it. Explicitly identify first editions too. |
| webpage | author (personal or literal institution), URL, accessed | Title/site/date/URL. Upstream prints last-visited only without issued date; this workflow requires issued year, so access date remains in the audit for human review. No archive, persistence or currency checking. |

Original records, including all extra legal fields, remain unmodified in
citations.json.sourceMetadata. Only the processor copy is adapted. Jurisdiction
is retained but does not select a module. Supply verified abbreviations. Export
the cited collection: validation intentionally checks all exported items.

## Short forms and diagnostics

Real note indices go to citeproc-js. Hidden context barriers prevent ibid across
prose-only/explanatory notes, multi-authority clusters and full-form fallbacks;
barriers never appear in the document. Explanatory clusters render full forms
in a fresh engine while the main engine retains first-reference positions for
later supra. Prior citation updates are applied with full-form overrides retained.

Every repetition produces REPEAT_REVIEW. FULL_FORM explains conservative
fallbacks: complex context/affix, same-author ambiguity, non-page locator,
repeat without explicit pinpoint, or unsupported short-form source type.
Statutes, regulations, bar opinions and webpages always retain full forms.
Books/articles sharing an author key retain full forms to avoid ambiguous supra.
No automatic hereinafter/infra or manual short-form override syntax exists.
Human exceptions belong in a separately preserved, reviewed final copy.

## Output, counts and reproducibility

DOCX uses native w:footnotes, w:footnoteReference and w:footnoteRef with connected
ids/relationships. PDF uses TeX footnotes. The verifier checks main-text reference
order, all notes beneath the separators (including continuation pages), and
complete note text against DOCX. It normalizes whitespace, ligatures/dash glyphs,
and uppercases **only** explicit DOCX smallCaps runs because PDF small-cap glyphs
extract as uppercase. It does not ignore arbitrary case changes. Dimensions,
replacement glyphs and page-bound text are checked, not every possible overlap.

PDF uses true TeX Gyre Termes small-cap glyphs as an explicitly named companion
font. Word retains editable smallCaps in the chosen manuscript font. Glyph
shapes, wrapping, heading sizes and page breaks can differ. Word page count is
not measured. PDF accessibility tagging and every non-Latin font are not certified.
Inspect every page in both formats after final edits.

Word counting converts main blocks and each footnote independently to Pandoc
plain text, then counts Unicode word tokens: numbers included, internal
apostrophes/hyphens part of a token. YAML title/author/date are excluded; headings,
tables and main quotations are included. Rendered citations/explanations count
only in notes. This definition can differ from Word's counter; confirm the
program's counting convention. Word counts never predict pages.

Archive hashes and TeX bundle identity are locked; manifests record input/output
hashes, runtime versions, chosen font hashes and layout. Retain/pin your own
lawfully installed Times New Roman version too. This is a reproducible rendering
recipe, not a promise of identical ZIP/PDF bytes across operating systems;
container timestamps and font versions can affect bytes.

Parser/processor references: [Pandoc citations](https://pandoc.org/MANUAL.html#citations),
[Pandoc footnotes](https://pandoc.org/MANUAL.html#footnotes), and
[CSL citation options](https://docs.citationstyles.org/en/stable/specification.html#citation-specific-options).
See [style notices](../vendor/NOTICE.md) for authorship and licenses.
