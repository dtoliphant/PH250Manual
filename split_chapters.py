#!/usr/bin/env python3
"""Split PH250_Lab_Manual_1.0.pdf into per-chapter PDFs using its outline bookmarks.

Run from the repo root (or pass the PDF path as an argument):
    python split_chapters.py

Writes Chapters/pdf/*.pdf. Each chapter PDF keeps its section bookmarks
and gets page labels matching the printed manual (arabic in \\mainmatter,
roman in front matter). Part divider pages are skipped.

Requires: pypdf >= 3.9  (pip install pypdf)
"""
import re
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "PH250_Lab_Manual_1.0.pdf")
OUT = SRC.parent / "Chapters" / "pdf"
MAIN_OFFSET = 10  # in \mainmatter, printed page = pdf page (1-based) - 10


def slugify(t):
    t = re.sub(r"[^\w\s-]", "", t).strip()
    return re.sub(r"\s+", "_", t)


def roman_to_int(s):
    vals = {"i": 1, "v": 5, "x": 10}
    total = 0
    for a, b in zip(s, s[1:]):
        total += -vals[a] if vals[a] < vals[b] else vals[a]
    return total + vals[s[-1]]


def flatten_outline(reader):
    """Return [(title, 0-based page, depth), ...] in document order."""
    flat = []

    def walk(items, depth=0):
        for it in items:
            if isinstance(it, list):
                walk(it, depth + 1)
            else:
                flat.append((it.title, reader.get_destination_page_number(it), depth))

    walk(reader.outline)
    return flat


def build(name, title, meta, pages, flat, label):
    """Write one PDF: pages = (start0, end0) 0-based, label = (style, start_value)."""
    w = PdfWriter()
    for pg in range(*pages):
        w.add_page(reader.pages[pg])

    # Rebuild nested bookmarks for entries inside this range.
    inside = [e for e in flat if pages[0] <= e[1] < pages[1]]
    base = min((d for _, _, d in inside), default=0)
    parents = {}
    for t, pg, d in inside:
        nd = d - base
        try:
            parents[nd] = w.add_outline_item(t, pg - pages[0], parent=parents.get(nd - 1))
        except Exception as e:  # bookmark problems must not kill the split
            print(f"  ! bookmark '{t}': {e}")

    m = {k: v for k, v in (reader.metadata or {}).items()}
    m["/Title"] = title
    w.add_metadata(m)
    if label:
        try:
            w.set_page_label(0, pages[1] - pages[0] - 1, style=label[0], start=label[1])
        except Exception as e:
            print(f"  ! page label: {e}")

    dest = OUT / name
    with dest.open("wb") as f:
        w.write(f)
    return dest


reader = PdfReader(SRC)
N = len(reader.pages)
flat = flatten_outline(reader)

tops = [e for e in flat if e[2] == 0]          # Introduction + the 4 parts
chapters = [e for e in flat if e[2] == 1]      # the 10 numbered chapters
assert len(tops) == 5 and len(chapters) == 10, (len(tops), len(chapters))

# Detect the printed roman number of the Introduction's first page (0-based 8).
intro_txt = reader.pages[tops[0][1]].extract_text() or ""
romans = [roman_to_int(t) for t in re.findall(r"\b([ivxl]{1,6})\b", intro_txt.lower())
          if set(t) <= set("ivxl") and roman_to_int(t) <= 12]
intro_start = romans[-1] if romans else tops[0][1] + 1
print(f"Manual: {N} pages | front matter -> p{tops[0][1]}, "
      f"Introduction printed no. detected: {intro_start}")

OUT.mkdir(parents=True, exist_ok=True)
for f in OUT.glob("*.pdf"):
    f.unlink()  # clear previous splits

results = []
results.append(build("00_Front_Matter.pdf", "PH 250 Lab Manual - Front Matter",
                     None, (0, tops[0][1]), flat, ("/r", 1)))
results.append(build("01_Introduction.pdf", "PH 250 Lab Manual - Introduction",
                     None, (tops[0][1], tops[1][1]), flat, ("/r", intro_start)))

for i, (t, pg, _) in enumerate(chapters, start=1):
    nxt_top = min((p for _, p, _ in tops if p > pg), default=N)
    nxt_ch = chapters[i][1] if i < len(chapters) else N
    end = min(nxt_top, nxt_ch, N)
    printed_start = pg + 1 - MAIN_OFFSET
    results.append(build(f"Chapter_{i:02d}_{slugify(t)}.pdf",
                         f"PH 250 Lab Manual - Chapter {i}: {t}",
                         None, (pg, end), flat, ("/D", printed_start)))

# ---- verify: re-read every output and report ----
print(f"\n{'file':<58} {'pages':>11}  label-range  bk  first-page text")
total = 0
for f in sorted(results, key=lambda p: p.name):
    r = PdfReader(f)
    n = len(r.pages)
    total += n
    try:
        labels = r.page_labels
        lr = f"{labels[0]}..{labels[-1]}"
    except Exception:
        lr = "?"
    nb = len(flatten_outline(r))
    first = (r.pages[0].extract_text() or "").strip().replace("\n", " ")[:45]
    print(f"{f.name:<58} {n:>4} ({f.stat().st_size // 1024} KB)  {lr:>11}  {nb:>2}  {first}")
print(f"\nTotal pages across files: {total} (manual has {N}; "
      f"difference = skipped part-divider/blank pages)")