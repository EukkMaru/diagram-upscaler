import subprocess
from pathlib import Path

DIAGRAM_DIR = Path("diagrams")
OUT_DIR = Path("rendered")
OUT_DIR.mkdir(exist_ok=True)

for tex_file in DIAGRAM_DIR.glob("*.tex"):
    pdf_name = OUT_DIR / tex_file.with_suffix(".pdf").name
    print(f"[+] Compiling {tex_file.name}")
    subprocess.run([
        "pdflatex",
        "-interaction=nonstopmode",
        "-output-directory", OUT_DIR.as_posix(),
        tex_file.as_posix()
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    #? Optional SVG conversion
    # subprocess.run(["pdf2svg", pdf_name, pdf_name.with_suffix(".svg")])
