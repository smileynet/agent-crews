---
name: document-formats
description: "Markup language selection for documentation. Covers Markdown, AsciiDoc, reStructuredText, and Typst. Trigger terms: asciidoc, restructuredtext, rst, typst, document format, multi-format, PDF output."
---

# Document Formats

## Decision Flow

1. Who is the audience?
2. What outputs are needed? (HTML only? PDF? EPUB?)
3. Where does it live? (GitHub, wiki, standalone?)
4. How complex? (prose? cross-refs? math?)

## Format Selection

| Need | Format | Why |
|------|--------|-----|
| README, GitHub docs, quick docs | **Markdown** | Universal, renders everywhere |
| Multi-format output (PDF + HTML + EPUB) | **AsciiDoc** | Single source, native features |
| Cross-referenced technical book | **AsciiDoc** | Includes, xrefs, conditionals |
| Python project API docs | **reStructuredText** | Sphinx autodoc integration |
| Academic paper with math | **Typst** | Modern LaTeX alternative, fast |
| Polished customer deliverable | **AsciiDoc** or **Typst** | Professional output, no LaTeX |
| Slides from same source | **AsciiDoc** (reveal.js) or **MARP** | One source → slides + docs |

## When to Leave Markdown

Switch when you need ANY of:
- PDF/EPUB output from same source
- Cross-file includes (`include::`)
- Numbered cross-references (`<<section-id>>`)
- Conditional content (ifdef/ifndef)
- Variables/attributes across documents

If you only need HTML rendering in GitHub — stay with Markdown.

## Integration with Diagrams

| Format | Diagram Support |
|--------|----------------|
| Markdown | Mermaid (native in GitHub/GitLab), images for others |
| AsciiDoc | Kroki integration (all formats), native diagram blocks |
| RST | Sphinx extensions (sphinxcontrib-mermaid, etc.) |
| Typst | Embedded via packages or images |
