"""Render REPORT.md (and SUPPLEMENT.md) into the organisers' .docx template.

The template carries fonts, margins, heading styles and a theme we do not want
to reproduce by hand. This keeps all of that and replaces only the body: it
opens the template, strips the placeholder paragraphs, and re-emits the
markdown using the template's own named styles. Nothing about the look is
invented here — every paragraph is assigned a style that already exists in the
document.

    python scripts/md_to_docx.py
    python scripts/md_to_docx.py --supplement       # append SUPPLEMENT.md too

Heading map, matched to how the template itself is laid out (numbered sections
are Heading 2 there, not Heading 1):

    # H1   -> Title            ### H3  -> Heading 3
    ## H2  -> Heading 2        #### H4 -> Heading 4

The first `###` line, when it directly follows the title, is treated as the
subtitle rather than a heading, which is how the report is written.

Inline `**bold**`, `*italic*` and `` `code` `` become real runs. Markdown tables
become real Word tables. Images are embedded at a width that fits the text
column. Anything it cannot map is emitted as plain body text rather than
silently dropped.
"""
import argparse
import os
import re

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

from common import ROOT

TEMPLATE = os.path.join(ROOT, "Copy of Secret Loytalties Hackathon submission template.docx")
REPORT = os.path.join(ROOT, "REPORT.md")
SUPPLEMENT = os.path.join(ROOT, "SUPPLEMENT.md")
OUT = os.path.join(ROOT, "submission.docx")

HEADING = {1: "Title", 2: "Heading 2", 3: "Heading 3", 4: "Heading 4"}
CODE_GREY = RGBColor(0x33, 0x33, 0x33)


def clear_body(doc):
    """Remove every placeholder block, keeping the section properties.

    sectPr holds page size, margins and headers. Deleting it would throw away
    the page setup, which is half of what the template is for.
    """
    body = doc.element.body
    for child in list(body):
        if not child.tag.endswith("}sectPr"):
            body.remove(child)


def add_runs(par, text):
    """Emit inline **bold**, *italic* and `code` as real runs."""
    # One pass, alternating between literal text and the marked-up spans.
    for piece in re.split(r"(\*\*[^*]+\*\*|(?<!\*)\*[^*]+\*(?!\*)|`[^`]+`)", text):
        if not piece:
            continue
        if piece.startswith("**") and piece.endswith("**"):
            par.add_run(piece[2:-2]).bold = True
        elif piece.startswith("`") and piece.endswith("`"):
            r = par.add_run(piece[1:-1])
            r.font.name = "Consolas"
            r.font.size = Pt(9.5)
            r.font.color.rgb = CODE_GREY
        elif piece.startswith("*") and piece.endswith("*"):
            par.add_run(piece[1:-1]).italic = True
        else:
            # Markdown link -> just the label; a live URL in a PDF adds nothing
            # a reader can click reliably, and the bare text stays readable.
            par.add_run(re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", piece))


def table_style(doc):
    for name in ("Table Grid", "Light Grid", "Normal Table"):
        try:
            doc.styles[name]
            return name
        except KeyError:
            continue
    return None


def add_table(doc, rows, style):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [c for c in cells if not all(re.fullmatch(r":?-{2,}:?", x or "-")
                                         for x in c)]
    if not cells:
        return
    width = max(len(r) for r in cells)
    t = doc.add_table(rows=len(cells), cols=width)
    if style:
        t.style = style
    for i, row in enumerate(cells):
        for j in range(width):
            cell = t.cell(i, j)
            cell.text = ""
            par = cell.paragraphs[0]
            add_runs(par, row[j] if j < len(row) else "")
            for run in par.runs:
                run.font.size = Pt(9)
                if i == 0:
                    run.bold = True


def convert(doc, md, seen_title):
    lines = md.split("\n")
    style = table_style(doc)
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if not line.strip():
            i += 1
            continue

        # Fenced code -> monospace block, one paragraph per line.
        if line.lstrip().startswith("```"):
            i += 1
            block = []
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            for b in block:
                p = doc.add_paragraph(style="normal")
                r = p.add_run(b)
                r.font.name = "Consolas"
                r.font.size = Pt(8.5)
                p.paragraph_format.space_after = Pt(0)
            continue

        # Image. The alt text wraps across lines in the source, so join the
        # run of lines up to the closing paren before matching.
        if line.lstrip().startswith("!["):
            joined, j = line.strip(), i
            while ")" not in joined and j + 1 < len(lines):
                j += 1
                joined += " " + lines[j].strip()
            i = j
            line = joined
        m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line.strip())
        if m:
            path = os.path.join(ROOT, m.group(2))
            if os.path.exists(path):
                doc.add_picture(path, width=Inches(6.0))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                print(f"   ! image not found, skipped: {m.group(2)}")
            i += 1
            continue

        # Table: a run of consecutive pipe rows.
        if line.strip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            add_table(doc, rows, style)
            doc.add_paragraph("", style="normal")
            continue

        # Headings.
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 3 and not seen_title["sub"] and seen_title["title"]:
                p = doc.add_paragraph(style="Subtitle")
                add_runs(p, text)
                seen_title["sub"] = True
            else:
                p = doc.add_paragraph(style=HEADING.get(level, "Heading 4"))
                add_runs(p, text)
                if level == 1:
                    seen_title["title"] = True
            i += 1
            continue

        # Horizontal rule.
        if re.fullmatch(r"[-*_]{3,}", line.strip()):
            i += 1
            continue

        # Blockquote.
        if line.lstrip().startswith(">"):
            block = []
            while i < len(lines) and (lines[i].lstrip().startswith(">")
                                      or not lines[i].strip()):
                if not lines[i].strip():
                    if block:
                        break
                    i += 1
                    continue
                block.append(lines[i].lstrip()[1:].strip())
                i += 1
            p = doc.add_paragraph(style="normal")
            p.paragraph_format.left_indent = Inches(0.4)
            add_runs(p, " ".join(block))
            for r in p.runs:
                r.italic = True
            continue

        # List item: gather its wrapped continuation lines.
        m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", line)
        if m:
            indent = len(m.group(1)) // 2
            text = m.group(3)
            i += 1
            while (i < len(lines) and lines[i].strip()
                   and not re.match(r"^(\s*)([-*+]|\d+\.)\s+", lines[i])
                   and not lines[i].startswith("#")
                   and not lines[i].strip().startswith("|")
                   and lines[i].startswith(" ")):
                text += " " + lines[i].strip()
                i += 1
            p = doc.add_paragraph(style="normal")
            p.paragraph_format.left_indent = Inches(0.25 + 0.25 * indent)
            bullet = m.group(2) if m.group(2)[0].isdigit() else "•"
            add_runs(p, f"{bullet}  {text}")
            continue

        # Body paragraph: join wrapped lines until a blank or a block starter.
        block = [line]
        i += 1
        while (i < len(lines) and lines[i].strip()
               and not lines[i].startswith(("#", "|", ">", "```", "!["))
               and not re.match(r"^(\s*)([-*+]|\d+\.)\s+", lines[i])):
            block.append(lines[i].strip())
            i += 1
        p = doc.add_paragraph(style="normal")
        add_runs(p, " ".join(x.strip() for x in block))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--supplement", action="store_true",
                    help="append SUPPLEMENT.md after the report, on a new page")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    if not os.path.exists(TEMPLATE):
        raise SystemExit(f"template not found: {TEMPLATE}")
    if not os.path.exists(REPORT):
        raise SystemExit("REPORT.md not found — run scripts/make_report.py first")

    doc = docx.Document(TEMPLATE)
    clear_body(doc)

    seen = {"title": False, "sub": False}
    convert(doc, open(REPORT, encoding="utf-8").read(), seen)

    if args.supplement and os.path.exists(SUPPLEMENT):
        doc.add_page_break()
        convert(doc, open(SUPPLEMENT, encoding="utf-8").read(), seen)

    doc.save(args.out)
    n_par = len(doc.paragraphs)
    print(f"wrote {args.out}")
    print(f"  {n_par} paragraphs, {len(doc.tables)} tables, "
          f"{len(doc.inline_shapes)} images")
    print("  Open it, check the first page, then File > Save as PDF.")


if __name__ == "__main__":
    main()
