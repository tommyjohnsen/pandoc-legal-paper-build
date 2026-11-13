<!-- PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl. -->
# Metadata handoff to the paper builder

Status: **interface requirements for planned ledger/snapshot adapters**, not a
shipped or tested cross-tool integration. The current builder consumes a private,
user-supplied CSL-JSON array and Pandoc Markdown. It does not ingest research
files, retrieve snapshots, assess clearance, run agent-guard, or verify claims.
The shared evidence contract remains owned/versioned by the source-and-claim
ledger; adapters must pin its actual schema revision before implementation.

Required mappings for an adapter:

- Preserve source_id, snapshot_id, immutable snapshot/version hash and the
  source record revision in an explicit citation-key mapping. CSL id is the
  unique citation key used in Markdown. Keep identity separate from version:
  different editions/versions must not silently share a mutable reference item.
- Export only explicitly selected, permitted bibliographic metadata. Include
  type, title, personal/institutional author, dates and relevant edition,
  jurisdiction, court/issuing body, reporter/volume/first page, code/section,
  opinion number, publication/site and URL. See academic.md for required fields.
  Missing legal fields must remain missing and fail validation; do not invent them.
- Tag **printed-page**, **paragraph**, **section** and **clause/normalized-section**
  locators separately from a **physical PDF page index**. A physical PDF page is
  a navigation aid, never an automatically substituted legal pinpoint. Record
  its index base explicitly. Preserve printed labels exactly, including prefixes
  and Roman numerals; unsupported printed labels fail the current citation grammar
  and need explanatory prose or a future tested adapter.
- Map reviewed printed numeric page/range values to Pandoc p./pp. locators;
  numeric paragraphs to para.; numeric sections/subsections to §. Current grammar
  does not accept arbitrary normalized HTML section ids or clause identifiers.
  Keep those references as evidence pointers, not fabricated page numbers.
- Preserve claim/outline-section ids and the human source-to-proposition relation
  separately. Citation rendering must not promote supported/verified/current
  status, infer legal weight, convert a classification into clearance or merge
  distinct snapshots. A pretty footnote makes no claim about proposition support.
- Keep clearance records/reviewer/date and reading/pinpoint/later-treatment
  statuses with the evidence system. Pass metadata only through an explicitly
  scoped adapter. No source text, research extracts, credential-bearing paths or
  personal reference library belongs in this repository or public fixtures.

The builder preserves extra fields in citations.json.sourceMetadata, but does
not validate their evidence-contract semantics. That preservation alone is not
integration or access enforcement. Future integration tests must use fictional
sources and prove stable citation-key/version mapping, typed locator handling,
rejection of physical-page substitution, and unchanged original evidence ids.
