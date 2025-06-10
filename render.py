import subprocess
from pathlib import Path

DIAGRAM_DIR = Path("diagrams")
OUT_DIR = Path("rendered")
OUT_DIR.mkdir(exist_ok=True)

# Optional: enable SVG conversion
ENABLE_SVG = False  # Set to True to enable

for tex_file in DIAGRAM_DIR.glob("*.tex"):
    pdf_name = OUT_DIR / tex_file.with_suffix(".pdf").name
    if pdf_name.exists():
        print(f"[-] Already compiled: {pdf_name.name}")
        continue

    print(f"[OK] Compiling {tex_file.name}...")

    try:
        result = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory", OUT_DIR.as_posix(),
                tex_file.as_posix()
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if result.returncode != 0:
            print(f"[!] Failed to compile {tex_file.name}")
            continue
    except Exception as e:
        print(f"[!] Exception compiling {tex_file.name}: {e}")
        continue

    print(f"[OK] PDF created: {pdf_name.name}")

    if ENABLE_SVG:
        svg_name = pdf_name.with_suffix(".svg")
        try:
            subprocess.run(
                ["pdf2svg", pdf_name.as_posix(), svg_name.as_posix()],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"[OK] SVG created: {svg_name.name}")
        except Exception as e:
            print(f"[!] SVG conversion failed for {pdf_name.name}: {e}")
