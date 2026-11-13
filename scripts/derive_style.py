#!/usr/bin/env python3
# PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl.
"""Recreate the CC BY-SA 3.0 academic derivative from its preserved upstream."""
from pathlib import Path
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
NS = 'http://purl.org/net/xbiblio/csl'
E.register_namespace('', NS)
n = {'c': NS}
root = E.parse(ROOT / 'vendor/bluebook-law-review.csl').getroot()
info = root.find('c:info', n)
uri = 'https://github.com/tommyjohnsen/pandoc-legal-paper-build/academic-legal'
info.find('c:title', n).text = 'Academic Legal Notes (local derivative of Bluebook Law Review)'
info.find('c:id', n).text = uri
for link in info.findall('c:link', n):
    if link.get('rel') == 'self':
        link.set('href', uri)


def el(s):
    return E.fromstring(s.replace('xmlns="NS"', f'xmlns="{NS}"'))


source = root.find("c:macro[@name='source']/c:choose", n)
# The bar-opinion source branch prints its required authority exactly once,
# even when a reference manager also exports that institution as an author.
root.find("c:macro[@name='author']/c:choose/c:if", n).set('type', 'legal_case legislation report')
old = source.find("c:else-if[@type='legislation']", n)
ix = list(source).index(old)
source.remove(old)
source.insert(ix, el('''<else-if xmlns="NS" type="legislation">
  <group delimiter=" ">
    <text variable="title" suffix=","/>
    <text variable="volume"/><text variable="container-title"/>
    <choose><if variable="locator"><group delimiter=" "><label variable="locator" form="symbol"/><text variable="locator"/></group></if>
    <else><group delimiter=" "><text value="§"/><text variable="section"/></group></else></choose>
    <group prefix="(" suffix=")" delimiter=" "><text variable="edition"/><date variable="issued"><date-part name="year"/></date></group>
  </group>
</else-if>'''))
old = source.find("c:else-if[@type='book report']", n)
old.set('type', 'book')
edition = root.find("c:macro[@name='issuance']", n)
for text in edition.findall(".//c:text[@variable='edition']", n):
    text.tag = f'{{{NS}}}number'
    text.set('form', 'ordinal')
source.insert(list(source).index(old) + 1, el('''<else-if xmlns="NS" type="report">
  <group delimiter=", "><text variable="authority"/><text variable="title"/>
  <text variable="title-short" prefix="Formal Op. "/>
  <group delimiter=" "><group delimiter=" "><label variable="locator" form="short"/><text variable="locator"/></group>
  <date variable="issued" prefix="(" suffix=")"><date-part name="year"/></date></group></group>
</else-if>'''))
# Labels for non-page locators. Preserve bare page numbers in the full form.
for parent in list(source.iter()):
    for child in list(parent):
        if child.tag == f'{{{NS}}}text' and child.get('variable') == 'locator':
            at = list(parent).index(child)
            replacement = el('''<group xmlns="NS" delimiter=" "><choose><if locator="section"><label variable="locator" form="symbol"/></if><else-if locator="page" match="none"><label variable="locator" form="short"/></else-if></choose><text variable="locator"/></group>''')
            for k, v in child.attrib.items():
                if k != 'variable':
                    replacement.set(k, v)
            # Already explicitly labeled in statute/bar-opinion branches.
            if any(x.tag == f'{{{NS}}}label' and x.get('variable') == 'locator' for x in parent):
                continue
            parent.remove(child)
            parent.insert(at, replacement)
E.indent(root, space='  ')
(ROOT / 'vendor/academic-legal.csl').write_text(
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<!-- PROVENANCE: modified-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl. Derivative under CC BY-SA 3.0; see vendor/NOTICE.md. -->\n'
    + '\n'.join(line.rstrip() for line in E.tostring(root, encoding='unicode').splitlines()) + '\n')
