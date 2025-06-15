# sudo apt install poppler-utils
# pip install pdf2image pymupdf tqdm pillow

import argparse
import os
from pathlib import Path
import json
import warnings
from pdf2image import convert_from_path
import fitz
from tqdm import tqdm
from PIL import Image, ImageDraw                    # ← NEW: add ImageDraw
from PIL.Image import DecompressionBombWarning

# ------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------
DPI = 300                                           # ← keep DPI in one place
SCALE = DPI / 72.0                                  # PDF points → pixel scale
# ------------------------------------------------------------------------

warnings.simplefilter("ignore", DecompressionBombWarning)

def extract_text_by_page(pdf_path):
    doc = fitz.open(pdf_path)
    return [page.get_text("words") for page in doc]

def main():
    parser = argparse.ArgumentParser(
        description="PDF → PNG + text JSON + text-mask PNG (non-OCR)")
    parser.add_argument("--input_dir",  type=str, default="./rendered",
                        help="PDF input folder")
    parser.add_argument("--output_dir", type=str, default="./images",
                        help="Output folder for PNG / JSON / mask")
    parser.add_argument("--skip_empty", action="store_true",
                        help="Skip PDFs with no text content")
    parser.add_argument("--use_filename", action="store_true",
                        help="Use original PDF filename instead of image_N")
    parser.add_argument("--log_path", type=str, default="log.txt",
                        help="Path to save log file")
    parser.add_argument("--detect_blank", action="store_true", default=True,
                        help="Skip nearly-white pages (enabled by default)")
    args = parser.parse_args()

    input_dir  = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = open(args.log_path, "w", encoding="utf-8")

    pdf_files = sorted(input_dir.glob("*.pdf"))

    for idx, pdf_path in enumerate(tqdm(pdf_files, desc="Processing PDFs"), 1):
        filename_base = pdf_path.stem if args.use_filename else f"image_{idx}"
        log_lines = [f"[{idx}] {pdf_path.name}"]

        try:
            images = convert_from_path(str(pdf_path), dpi=DPI)  # ← use DPI
            text_by_page = extract_text_by_page(pdf_path)
        except Exception as e:
            log_lines.append(f"  [x] Error processing PDF: {e}")
            log_file.write("\n".join(log_lines) + "\n\n")
            continue

        total_pages    = len(text_by_page)
        non_empty_pages = [i for i, p in enumerate(text_by_page)
                           if any(w[4].strip() for w in p)]
        num_non_empty  = len(non_empty_pages)
        log_lines.append(f"  → {num_non_empty} non-empty page(s) / {total_pages}")

        if args.skip_empty and num_non_empty == 0:
            log_lines.append("  [!] Skipped (no text)")
            log_file.write("\n".join(log_lines) + "\n\n")
            continue

        for i, (img, words) in enumerate(zip(images, text_by_page)):
            if args.skip_empty and i not in non_empty_pages:
                continue

            suffix   = "" if total_pages == 1 else f"_page{i+1}"
            img_name = f"{filename_base}{suffix}.png"
            json_name = f"{filename_base}{suffix}.json"
            mask_name = f"{filename_base}{suffix}_mask.png"     # ← mask file

            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("error",
                                            category=DecompressionBombWarning)

                    if args.detect_blank:
                        gray  = img.convert("L")
                        hist  = gray.histogram()
                        total = gray.width * gray.height
                        non_white = sum(hist[j] for j in range(0, 250))
                        if non_white / total < 0.01:
                            log_lines.append(f"  [!] Skipped page {i+1} (blank)")
                            continue

                    img.save(output_dir / img_name)

            except DecompressionBombWarning:
                log_lines.append(f"  [!] Skipped page {i+1} (DecompressionBomb)")
                continue
            except Exception as e:
                log_lines.append(f"  [x] Error saving image p{i+1}: {e}")
                continue

            page_text_data = [{
                    "text": word[4],
                    "bbox": word[:4],          # (x0,y0,x1,y1) in PDF pts
                    "block": word[5],
                    "line":  word[6],
                    "word_num": word[7]
                } for word in words if word[4].strip()]
            with open(output_dir / json_name, "w", encoding="utf-8") as f:
                json.dump(page_text_data, f, indent=2, ensure_ascii=False)

            gray_page = img.convert("L")                 # reuse for all words
            mask = Image.new("L", img.size, 0)

            THRESH = 220 # 0-255

            for w in words:
                if not w[4].strip():
                    continue
                # word bbox → pixel coords
                x0, y0, x1, y1 = (int(c * SCALE) for c in w[:4])
                crop = gray_page.crop((x0, y0, x1, y1)) 

                # binarise: text pixels (<THRESH) → 255, else 0
                bw = crop.point(lambda p: 255 if p < THRESH else 0)

                # paste into mask; use itself as the alpha so only white pixels land
                mask.paste(bw, (x0, y0), bw)

            mask_name = f"{filename_base}{suffix}_mask.png"
            mask.save(output_dir / mask_name)

        log_lines.append(f"  → Saved {num_non_empty} page(s) to {output_dir}")
        log_file.write("\n".join(log_lines) + "\n\n")

    log_file.close()

if __name__ == "__main__":
    main()
