import re
import subprocess
from pathlib import Path

# Setup paths
DIAGRAM_DIR = Path("diagrams")
MASK_DIR = Path("masks")
RENDER_DIR = Path("mask_renders")
MASK_DIR.mkdir(exist_ok=True)
RENDER_DIR.mkdir(exist_ok=True)

# Helper to color only node contents
def color_node_content(match):
    pre, content = match.group(1), match.group(2)
    return f"{pre}{{\\textcolor{{red}}{{{content}}}}}"

for tex_file in DIAGRAM_DIR.glob("*.tex"):
    text = tex_file.read_text()

    # Color the text inside nodes
    text = re.sub(r"(\\node(?:\[[^\]]*\])?)\s*{(.*?)}", color_node_content, text)

    # Also wrap \textbf and \textit
    text = re.sub(r"\\text(bf|it)\s*{(.*?)}", r"\\text\1{\\textcolor{red}{\2}}", text)

    # Wrap in standalone LaTeX boilerplate
    wrapped = (
        "\\documentclass{standalone}\n"
        "\\usepackage{tikz}\n"
        "\\usepackage{xcolor}\n"
        "\\begin{document}\n"
        f"{text}\n"
        "\\end{document}"
    )

    out_path = MASK_DIR / tex_file.name
    out_path.write_text(wrapped)
    print(f"[OK] Created masked tex: {out_path.name}")

    # Compile .tex to PDF
    try:
        subprocess.run([
            "pdflatex",
            "-interaction=nonstopmode",
            "-output-directory", MASK_DIR.as_posix(),
            out_path.as_posix()
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[!] pdflatex failed: {e}")
        continue

    pdf_path = out_path.with_suffix(".pdf")
    if not pdf_path.exists():
        print(f"[!] PDF not generated: {pdf_path.name}")
        continue

    # Convert PDF to PNG
    png_path = RENDER_DIR / pdf_path.with_suffix(".png").name
    try:
        subprocess.run([
            "convert", "-density", "300",
            pdf_path.as_posix(),
            "-quality", "100",
            png_path.as_posix()
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[OK] Rendered mask PNG: {png_path.name}")
    except Exception as e:
        print(f"[!] convert failed: {e}")
