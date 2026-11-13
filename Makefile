# PROVENANCE: modified-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl.
# Default: validated academic footnotes. Legacy comparisons remain explicit.
#   A: plain Zotero export (CSL-JSON or BibLaTeX) -> pandoc citeproc (CSL 1.0 style)
#   B: Juris-M CSL-JSON export -> citeproc-js with the Juris-M IndigoBook CSL-M style
# Style files are downloaded at build time from pinned commits and never committed.

SRC      ?= sample/paper.md
A_BIB    ?= sample/references-zotero.json
B_JSON   ?= sample/references-jurism.json
BUILD    ?= build
PANDOC   ?= pandoc
NODE     ?= node
ACADEMIC_SRC ?= sample/academic.md
ACADEMIC_BIB ?= sample/academic-references.json
OUT ?= $(BUILD)/academic
FONT ?= Times New Roman
SIZE ?= 12
NOTE_SIZE ?= 10
MARGIN ?= 1
ifneq ($(origin STYLE_A),undefined)
$(error STYLE_A overrides are not checksum-locked; deliberately update tools/styles.lock.json and rerun tests)
endif

# Download sources and checksums live in tools/styles.lock.json.
S := $(BUILD)/styles
COMMON := --standalone --metadata link-citations=false

.PHONY: all academic demo legacy zotero jurism compare styles test integration legacy-test clean
all: academic
academic:
	PANDOC=$(PANDOC) python3 scripts/build_academic.py --source "$(ACADEMIC_SRC)" --bib "$(ACADEMIC_BIB)" --output "$(OUT)" --font "$(FONT)" --size "$(SIZE)" --note-size "$(NOTE_SIZE)" --margin "$(MARGIN)"
demo:
	$(MAKE) academic OUT="$(BUILD)/demo" FONT="Liberation Serif"
legacy: zotero jurism compare

styles: $(S)/a.csl $(S)/jm-indigobook.csl $(S)/locales-en-US.xml $(S)/modules/.ok
	python3 scripts/fetch_styles.py "$(S)"
$(S)/a.csl $(S)/jm-indigobook.csl $(S)/locales-en-US.xml $(S)/modules/.ok &: tools/styles.lock.json scripts/fetch_styles.py
	python3 scripts/fetch_styles.py "$(S)"

# ---- A: plain Zotero export + pandoc citeproc ----
zotero: $(BUILD)/zotero/paper.docx $(BUILD)/zotero/paper.pdf
$(BUILD)/zotero/paper.%: $(SRC) $(A_BIB) $(S)/a.csl defaults.yaml
	@mkdir -p $(@D)
	@test ! -e "$@" || (echo "Refusing to overwrite $@; choose a fresh BUILD directory" >&2; exit 1)
	$(PANDOC) $(SRC) -d defaults.yaml $(COMMON) --citeproc --csl $(S)/a.csl --bibliography $(A_BIB) -o $@

# ---- B: Juris-M export + citeproc-js (CSL-M) ----
jurism: $(BUILD)/jurism/paper.docx $(BUILD)/jurism/paper.pdf
$(BUILD)/jurism/ast.json: $(SRC)
	@mkdir -p $(@D) && $(PANDOC) $(SRC) -t json -o $@
$(BUILD)/jurism/citations.json: $(BUILD)/jurism/ast.json $(B_JSON) styles node_modules/.package-lock.json
	$(NODE) scripts/render-cslm.mjs $< $(B_JSON) $(S)/jm-indigobook.csl $(S)/locales-en-US.xml $(S)/modules $@
$(BUILD)/jurism/paper.%: $(SRC) $(BUILD)/jurism/citations.json defaults.yaml
	@test ! -e "$@" || (echo "Refusing to overwrite $@; choose a fresh BUILD directory" >&2; exit 1)
	$(PANDOC) $(SRC) -d defaults.yaml $(COMMON) -M rendered=$(BUILD)/jurism/citations.json --lua-filter filters/inject-citations.lua -o $@
node_modules/.package-lock.json: package.json package-lock.json
	npm ci --no-audit --no-fund

# ---- Compare the rendered citations of A and B ----
compare: $(BUILD)/compare/citations.diff
$(BUILD)/compare/zotero.txt: $(SRC) $(A_BIB) $(S)/a.csl
	@mkdir -p $(@D)
	$(PANDOC) $(SRC) --citeproc --csl $(S)/a.csl --bibliography $(A_BIB) --lua-filter filters/list-cites.lua -t plain --wrap=none -o $@
$(BUILD)/compare/jurism.txt: $(BUILD)/jurism/citations.json
	@mkdir -p $(@D)
	$(NODE) -e 'const t=JSON.parse(require("fs").readFileSync(process.argv[1])).text;t.forEach((s,i)=>console.log(`[$${String(i+1).padStart(2,"0")}] $${s}`))' $< > $@
$(BUILD)/compare/citations.diff: $(BUILD)/compare/zotero.txt $(BUILD)/compare/jurism.txt
	diff -u --label zotero --label jurism $^ > $@ || true
	diff -y -W 200 $^ > $(BUILD)/compare/side-by-side.txt || true
	@echo "wrote $@ and $(BUILD)/compare/side-by-side.txt"

test:
	$(NODE) tests/academic.test.mjs
	python3 -m unittest discover -s tests -p 'test_*.py' -v
	python3 scripts/check_vendor.py
integration:
	python3 tests/integration.py
legacy-test: $(BUILD)/jurism/paper.pdf
	test -s $<
	@mkdir -p $(BUILD)/test
	$(PANDOC) $(SRC) -d defaults.yaml $(COMMON) -M rendered=$(BUILD)/jurism/citations.json --lua-filter filters/inject-citations.lua -t latex -o $(BUILD)/test/jurism.tex
	grep -Fq '\bibitem' $(BUILD)/test/jurism.tex
	$(PANDOC) $(SRC) -d defaults.yaml $(COMMON) -M rendered=tests/empty-bibliography.json --lua-filter filters/inject-citations.lua -t latex -o $(BUILD)/test/empty.tex
	! grep -q CSLReferences $(BUILD)/test/empty.tex
	$(PANDOC) $(SRC) -d defaults.yaml $(COMMON) -M rendered=tests/empty-bibliography.json --lua-filter filters/inject-citations.lua -o $(BUILD)/test/empty.pdf
	test -s $(BUILD)/test/empty.pdf

clean:
	rm -rf $(BUILD)
