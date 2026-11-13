<!-- PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl. -->
# Third-party sources

These assets retain their own licenses; the repository's Apache-2.0 license
does not replace them. `checksums.json` records the exact preserved bytes.

| File | Origin and revision | License |
|---|---|---|
| `bluebook-law-review.csl` | citation-style-language/styles, commit `6ba2e9c6aa6e0dab87d3a20b833ed8ff6500f698`, file `bluebook-law-review.csl`; authors Bruce D'Arcus and Nancy Sims, contributors listed in the file | CC BY-SA 3.0, as stated in the style's rights element |
| `academic-legal.csl` | Local derivative of the preceding file; reproduce with `python3 scripts/derive_style.py` | CC BY-SA 3.0; modifications attributed to codex/gpt-6, 2026-11-13 |
| `locales-en-US.xml` | citation-style-language/locales, commit `a89adece41013402236e2c9020972d7e931fbab8` | CC BY-SA 3.0, locale author contributions retained |
| `texgyretermes-regular.otf` | TeX Gyre Termes 2.004, from Ubuntu/Debian `fonts-texgyre` 20180621-6; package SHA-256 `dc743718ece939f4a868e15012e383aa9bf6501ed6857c895835911053ef250a`; font hash in checksums.json | GUST Font License; copyright Bogusław Jackowski and Janusz M. Nowacki. See preserved `tex-gyre-LICENSE.txt` for the complete package notices |

The derivative adds full statute/regulation forms with code, section and edition,
a bounded bar-opinion form, section/paragraph/note/chapter labels, and ordinal
book editions. It does not implement the entire Bluebook or jurisdiction modules.
Upstream author attribution is retained. Original upstream files are unmodified.
No text from a licensed citation manual is included.

[CC BY-SA 3.0 license](https://creativecommons.org/licenses/by-sa/3.0/)
and [GUST Font License](https://www.gust.org.pl/projects/e-foundry/licenses/GUST-FONT-LICENSE.txt).

Legacy style URLs, immutable commits and SHA-256 values are in
`tools/styles.lock.json`: JM Indigo Book by Frank Bennett and Juris-M
contributors, US jurisdiction modules, the community `bluebook-inline` style,
and the en-US locale (CC BY-SA 3.0). They remain downloads in ignored build
directories; `scripts/fetch_styles.py` validates every download and cache hit.

The npm processor `citeproc` 2.4.63 is pinned by package-lock.json and npm integrity
hash. Its **packaged LICENSE** permits CPAL 1.0 or later, or AGPL 3 or later;
the npm manifest's AGPL-1.0 label conflicts with that text. Inspect that license
before redistribution; this repository does not relicense or vendor the engine.
PyMuPDF 1.26.6 is AGPL/commercial dual licensed; it is installed as a verification
tool. Pandoc is GPL; Tectonic is MIT; Node is MIT with bundled notices. See their
downloaded distributions for notices. The demo Liberation fonts are SIL OFL 1.1;
their complete notices are preserved by setup under `.tools/fonts/usr/share/doc`.
Times New Roman is neither supplied nor licensed by this repository.
