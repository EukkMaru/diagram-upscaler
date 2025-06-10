import tarfile
import re
from pathlib import Path

SOURCE_DIR = Path("sources")
EXTRACT_DIR = Path("extracted")
EXTRACT_DIR.mkdir(exist_ok=True)

def find_main_tex(files):
    for f in files:
        text = f.read_text(errors="ignore")
        if r"\begin{document}" in text:
            return f
    return None

def extract_figures(tex_path):
    content = tex_path.read_text(errors="ignore")
    tikz_blocks = re.findall(r"\\begin{tikzpicture}.*?\\end{tikzpicture}", content, re.DOTALL)
    Path("diagrams").mkdir(exist_ok=True)
    for i, block in enumerate(tikz_blocks):
        diagram_tex = (
            "\\documentclass{standalone}\n"
            "\\usepackage{tikz}\n"
            "\\begin{document}\n" + block + "\n\\end{document}"
        )
        with open(f"diagrams/diag_{tex_path.stem}_{i}.tex", "w") as f:
            f.write(diagram_tex)

for tar_path in SOURCE_DIR.glob("*.tar.gz"):
    out_subdir = EXTRACT_DIR / tar_path.stem
    out_subdir.mkdir(exist_ok=True)
    with tarfile.open(tar_path) as tar:
        tar.extractall(out_subdir)
    
    tex_files = list(out_subdir.rglob("*.tex"))
    main_tex = find_main_tex(tex_files)
    if main_tex:
        print(f"[+] Found main TeX: {main_tex}")
        extract_figures(main_tex)
