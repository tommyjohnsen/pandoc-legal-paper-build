# Pandoc build template: one markdown source, two citation pipelines.
#   A: plain Zotero export (CSL-JSON or BibLaTeX) -> pandoc citeproc (CSL 1.0 style)
#   B: Juris-M CSL-JSON export -> citeproc-js with the Juris-M IndigoBook CSL-M style
# Style files are downloaded at build time from pinned commits and never committed.

SRC      ?= sample/paper.md
A_BIB    ?= sample/references-zotero.json
B_JSON   ?= sample/references-jurism.json
BUILD    ?= build
PANDOC   ?= pandoc
NODE     ?= node

# Pinned upstream sources (bump deliberately).
CSL_STYLES_REV    ?= 6ba2e9c6aa6e0dab87d3a20b833ed8ff6500f698
JM_STYLES_REV     ?= 15214e48b1b4e584c8ec0054724f9f51b4f58cd2
JM_MODULES_REV    ?= 11b9c4ca5ed8aebea66e1ab1ead12761a32d7c84
CSL_LOCALES_REV   ?= a89adece41013402236e2c9020972d7e931fbab8
# Pipeline A style: pandoc citeproc cannot parse CSL-M, so A uses a CSL 1.0 style
# from the official CSL repository. Override STYLE_A with any style name there.
STYLE_A           ?= bluebook-inline
STYLE_A_URL       ?= https://raw.githubusercontent.com/citation-style-language/styles/$(CSL_STYLES_REV)/$(STYLE_A).csl
STYLE_B_URL       ?= https://raw.githubusercontent.com/Juris-M/jm-styles/$(JM_STYLES_REV)/jm-indigobook.csl
MODULES_URL       ?= https://codeload.github.com/Juris-M/style-modules/tar.gz/$(JM_MODULES_REV)
LOCALE_URL        ?= https://raw.githubusercontent.com/citation-style-language/locales/$(CSL_LOCALES_REV)/locales-en-US.xml

S := $(BUILD)/styles
COMMON := --standalone --metadata link-citations=false

.PHONY: all zotero jurism compare styles test clean
all: zotero jurism compare

styles: $(S)/a.csl $(S)/jm-indigobook.csl $(S)/locales-en-US.xml $(S)/modules/.ok
$(S)/a.csl:             ; @mkdir -p $(@D) && curl -fsSL -o $@ $(STYLE_A_URL)
$(S)/jm-indigobook.csl: ; @mkdir -p $(@D) && curl -fsSL -o $@ $(STYLE_B_URL)
$(S)/locales-en-US.xml: ; @mkdir -p $(@D) && curl -fsSL -o $@ $(LOCALE_URL)
$(S)/modules/.ok:
	@mkdir -p $(@D) && curl -fsSL $(MODULES_URL) | tar xz -C $(@D) --strip-components=1 --wildcards '*/juris-us*.csl' && touch $@

# ---- A: plain Zotero export + pandoc citeproc ----
zotero: $(BUILD)/zotero/paper.docx $(BUILD)/zotero/paper.pdf
$(BUILD)/zotero/paper.%: $(SRC) $(A_BIB) $(S)/a.csl defaults.yaml
	@mkdir -p $(@D)
	$(PANDOC) $(SRC) -d defaults.yaml $(COMMON) --citeproc --csl $(S)/a.csl --bibliography $(A_BIB) -o $@

# ---- B: Juris-M export + citeproc-js (CSL-M) ----
jurism: $(BUILD)/jurism/paper.docx $(BUILD)/jurism/paper.pdf
$(BUILD)/jurism/ast.json: $(SRC)
	@mkdir -p $(@D) && $(PANDOC) $(SRC) -t json -o $@
$(BUILD)/jurism/citations.json: $(BUILD)/jurism/ast.json $(B_JSON) styles node_modules/.package-lock.json
	$(NODE) scripts/render-cslm.mjs $< $(B_JSON) $(S)/jm-indigobook.csl $(S)/locales-en-US.xml $(S)/modules $@
$(BUILD)/jurism/paper.%: $(SRC) $(BUILD)/jurism/citations.json defaults.yaml
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

test: $(BUILD)/jurism/paper.pdf
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
