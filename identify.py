import tarfile
import re
from pathlib import Path

SOURCE_DIR = Path("sources")
EXTRACT_DIR = Path("extracted")
DIAGRAM_DIR = Path("diagrams")

EXTRACT_DIR.mkdir(exist_ok=True)
DIAGRAM_DIR.mkdir(exist_ok=True)

def find_main_tex(files):
    for f in files:
        try:
            text = f.read_text(errors="ignore")
            if r"\begin{document}" in text:
                return f
        except Exception as e:
            print(f"[!] Could not read {f}: {e}")
    return None

def extract_figures(tex_path):
    try:
        content = tex_path.read_text(errors="ignore")
    except Exception as e:
        print(f"[!] Failed to read {tex_path}: {e}")
        return

    tikz_blocks = re.findall(r"\\begin{tikzpicture}.*?\\end{tikzpicture}", content, re.DOTALL)
    if not tikz_blocks:
        print(f"[-] No TikZ blocks found in {tex_path}")
        return

    for i, block in enumerate(tikz_blocks):
        diagram_tex = (
            "\\documentclass{standalone}\n"
            "\\usepackage{tikz}\n"
            "\\begin{document}\n" + block + "\n\\end{document}"
        )
        try:
            out_path = DIAGRAM_DIR / f"diag_{tex_path.stem}_{i}.tex"
            with open(out_path, "w") as f:
                f.write(diagram_tex)
            print(f"[OK] Extracted TikZ block to {out_path}")
        except Exception as e:
            print(f"[!] Failed to write diagram {i} from {tex_path}: {e}")

for tar_path in SOURCE_DIR.glob("*.tar.gz"):
    out_subdir = EXTRACT_DIR / tar_path.stem
    if out_subdir.exists() and list(out_subdir.glob("*.tex")):
        print(f"[-] Already extracted: {tar_path.name}")
        continue

    try:
        out_subdir.mkdir(exist_ok=True)
        with tarfile.open(tar_path) as tar:
            tar.extractall(out_subdir)
        print(f"[OK] Extracted {tar_path.name}")
    except Exception as e:
        print(f"[!] Failed to extract {tar_path.name}: {e}")
        continue

    tex_files = list(out_subdir.rglob("*.tex"))
    if not tex_files:
        print(f"[-] No .tex files found in {tar_path.name}")
        continue

    main_tex = find_main_tex(tex_files)
    if main_tex:
        print(f"[OK] Found main TeX file: {main_tex}")
        extract_figures(main_tex)
    else:
        print(f"[!] No main TeX file found in {tar_path.name}")
