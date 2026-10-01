r"""Compile every standalone TikZ figure to PDF.

Figures live directly in Figures/ (and shared ones in Figures/Reusable_TikZ/);
any .tex file there that contains \documentclass is a figure.  Library files
(*-pic.tex, lab-style.tex) are not compiled but trigger rebuilds when changed.

    python build_figures.py            # rebuild figures that are out of date
    python build_figures.py --all      # rebuild everything
    python build_figures.py a.tex b.tex
"""
import pathlib
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent
LIB = ROOT / "Reusable_TikZ"


def is_figure(tex):
    text = tex.read_text(encoding="utf8", errors="ignore")
    return any(line.startswith(r"\documentclass") for line in text.splitlines())


def figure_sources():
    for folder in (ROOT, LIB):
        for tex in sorted(folder.glob("*.tex")):
            if is_figure(tex):
                yield tex


def compile_one(tex):
    cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name]
    r = subprocess.run(cmd, cwd=tex.parent, capture_output=True, text=True,
                       encoding="utf8", errors="ignore")
    tex.with_suffix(".aux").unlink(missing_ok=True)
    if r.returncode == 0:
        tex.with_suffix(".log").unlink(missing_ok=True)
    return tex, r.returncode, r.stdout


def main(argv):
    if argv and argv[0] != "--all":
        todo = [pathlib.Path(a).resolve() for a in argv]
    else:
        lib_time = max(p.stat().st_mtime for p in LIB.glob("*.tex") if not is_figure(p))
        todo = []
        for tex in figure_sources():
            pdf = tex.with_suffix(".pdf")
            if argv[:1] == ["--all"] or not pdf.exists() or \
               pdf.stat().st_mtime < max(tex.stat().st_mtime, lib_time):
                todo.append(tex)
    failed = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for tex, rc, out in pool.map(compile_one, todo):
            rel = tex.relative_to(ROOT)
            if rc == 0:
                print(f"ok      {rel}")
            else:
                failed.append(rel)
                err = [line for line in out.splitlines() if line.startswith("!")][:2]
                print(f"FAILED  {rel}  {' | '.join(err)}")
    print(f"\n{len(todo) - len(failed)} built, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
