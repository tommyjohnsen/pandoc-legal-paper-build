# pandoc-legal-paper-build

A reusable Pandoc build template for legal and academic papers. Write once in
Markdown, cite with keys from a reference manager, and build DOCX and PDF with
two citation pipelines side by side:

| Pipeline | Input | Citation engine | Style |
|---|---|---|---|
| **A: Zotero** | Zotero CSL-JSON (or BibLaTeX) export | Pandoc's built-in citeproc | a CSL 1.0 style from the official CSL repository (default `bluebook-inline`, override with `STYLE_A=`) |
| **B: Juris-M** | Juris-M CSL-JSON export | [citeproc-js](https://github.com/Juris-M/citeproc-js) (Node) | Juris-M **JM Indigo Book** CSL-M style plus Juris-M jurisdiction style modules |

`make compare` extracts the rendered citations from both pipelines and writes a
unified diff and a side-by-side file, so you can see exactly where the two
disagree.

## Quick start

```sh
docker build -t paper-build .
docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD":/work paper-build make all
```

Outputs:

```
build/zotero/paper.docx  build/zotero/paper.pdf
build/jurism/paper.docx  build/jurism/paper.pdf  build/jurism/citations.json
build/compare/citations.diff  build/compare/side-by-side.txt
```

Without Docker you need `pandoc` (3.x), a LaTeX engine (`xelatex`), Node 18+,
`make`, `curl` and `diff`. Targets: `make zotero`, `make jurism`, `make compare`,
`make clean`. Point at your own files with
`make SRC=paper.md A_BIB=my-zotero.json B_JSON=my-jurism.json`.

The `sample/` folder holds a short invented paper and invented references in
three formats: `references-zotero.json` (CSL-JSON), `references-zotero.bib`
(BibLaTeX, usable as `A_BIB`) and `references-jurism.json` (CSL-JSON with
Juris-M `jurisdiction` fields). All parties, courts, reporters, statutes,
authors and works in the sample are fictional.

## Why two engines

The Indigo Book style published by the Juris-M project is a **CSL-M** style
(`version="1.1mlz1"`). CSL-M extends CSL with features Pandoc's citeproc does
not implement, including `<conditions>` blocks, jurisdiction-specific style
modules (`juris-us-IndigoTemp.csl` and friends), and multilingual and
court-hierarchy handling. Pandoc refuses the file outright
(`CiteprocParseError: unknown element "conditions"`).

So:

* Pipeline A uses Pandoc citeproc with the best available CSL 1.0 style. No
  CSL 1.0 Indigo Book style exists in the official CSL repository, so the
  default is the community `bluebook-inline` style. It is approximate: for
  example it omits the court and year for cases and the code name for statutes.
* Pipeline B renders citations with citeproc-js, the engine Juris-M itself
  uses, which loads the CSL-M style and its jurisdiction modules. The rendered
  citations are injected into the Pandoc document by
  `filters/inject-citations.lua`. This pipeline handles in-text citations and
  the bibliography; footnote styles and Pandoc-specific citation syntax such as
  author-suppression are not mapped yet. Locators are read from the citation
  suffix (`p.`, `sec.`, `§`, `para.`, `n.`; plain numbers default to pages).

**Neither pipeline produces publication-ready legal citations.** Always do a
manual citation-format review pass against the style guide you are required to
follow.

## Exporting from Zotero / Juris-M

* **Zotero:** select the collection, choose *Export Collection…*, pick the
  *CSL JSON* format and save it as your `A_BIB` file. A *BibLaTeX* export also
  works for pipeline A. If you use the Better BibTeX plugin, its *Better CSL
  JSON* format gives stable citation keys and can keep the export updated
  automatically.
* **Juris-M:** export the same way with the *CSL JSON* format and use the file
  as `B_JSON`. Juris-M keeps legal metadata (jurisdiction, court) in fields
  that only its own export writes; a plain Zotero export of the same items will
  not contain them, which is one source of differences in `make compare`.
* Citation keys in the Markdown (`[@key, 214]`) must match the `id` field of the
  exported entries.

## Third-party styles and licenses

The style files are downloaded at build time from pinned commits and are
**not** part of this repository:

* **JM Indigo Book** (`jm-indigobook.csl`) from
  [Juris-M/jm-styles](https://github.com/Juris-M/jm-styles), and US
  jurisdiction modules from
  [Juris-M/style-modules](https://github.com/Juris-M/style-modules), by Frank
  Bennett and Juris-M contributors. Licensed under
  [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). The style
  implements rules from [The Indigo Book](https://indigobook.github.io/),
  a community-made, openly licensed restatement of US legal citation rules.
* **Pipeline A style** (default `bluebook-inline.csl`) from the
  [CSL styles repository](https://github.com/citation-style-language/styles),
  community-made, licensed under
  [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).
* **en-US locale** from the
  [CSL locales repository](https://github.com/citation-style-language/locales),
  CC BY-SA 3.0.
* **citeproc-js** (npm package `citeproc`) is installed at build time; it is
  dual licensed CPAL-1.0 / AGPL-1.0 and is not distributed with this template.

These styles are community-maintained and not official publications of any
citation manual.

## License

The template itself (Makefile, filters, scripts, sample, CI) is licensed under
the Apache License 2.0. See `LICENSE`.
