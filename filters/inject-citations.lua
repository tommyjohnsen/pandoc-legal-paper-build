-- Replace each Cite with citations pre-rendered by scripts/render-cslm.mjs
-- (in document order) and fill the #refs div with its bibliography.
-- Usage: pandoc -M rendered=build/jurism/citations.json --lua-filter inject-citations.lua
local rendered, i = nil, 0

local function html_inlines(s)
  local blocks = pandoc.read(s, 'html').blocks
  local out = pandoc.Inlines{}
  for _, b in ipairs(blocks) do
    if b.content then out:extend(b.content) end
  end
  return out
end

local function load(m)
  local f = assert(io.open(pandoc.utils.stringify(m.rendered), 'r'))
  rendered = pandoc.json.decode(f:read('a')); f:close()
end

local function replace_cite(c)
  i = i + 1
  return html_inlines(rendered.html[i] or '[missing citation]')
end

function Pandoc(doc)
  load(doc.meta)
  doc = doc:walk({ Cite = replace_cite })
  local bib = pandoc.Blocks{}
  for _, entry in ipairs(rendered.bibliography_html or {}) do
    bib:extend(pandoc.read(entry, 'html').blocks)
  end
  local placed = false
  doc = doc:walk({ Div = function(d) if d.identifier == 'refs' then placed = true; d.content = bib; return d end end })
  if not placed then doc.blocks:insert(pandoc.Div(bib, pandoc.Attr('refs'))) end
  return doc
end
