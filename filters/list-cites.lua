-- Emit only the rendered citations of a document, one per line, so two builds
-- can be compared. Run after --citeproc.
function Pandoc(doc)
  local out = pandoc.Inlines{}
  local n = 0
  doc:walk({
    Cite = function(c)
      n = n + 1
      if n > 1 then out:insert(pandoc.LineBreak()) end
      out:insert(pandoc.Str(string.format('[%02d] ', n)))
      out:extend(c.content)
    end,
  })
  return pandoc.Pandoc({ pandoc.Plain(out) })
end
