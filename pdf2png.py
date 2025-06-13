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
from PIL import Image
from PIL.Image import DecompressionBombWarning

# Suppress display of decompression warnings
warnings.simplefilter("ignore", DecompressionBombWarning)

def extract_text_by_page(pdf_path):
    doc = fitz.open(pdf_path)
    return [page.get_text("words") for page in doc]

def main():
    parser = argparse.ArgumentParser(description="PDF to PNG + Text Extractor (non-OCR)")
    parser.add_argument("--input_dir", type=str, default="./rendered", help="PDF input folder")
    parser.add_argument("--output_dir", type=str, default="./images", help="Output folder for PNG and JSON")
    parser.add_argument("--skip_empty", action="store_true", help="Skip PDFs with no text content")
    parser.add_argument("--use_filename", action="store_true", help="Use original PDF filename instead of image_N")
    parser.add_argument("--log_path", type=str, default="log.txt", help="Path to save log file")
    parser.add_argument("--detect_blank", action="store_true", default=True, help="Skip nearly-white pages using histogram (enabled by default)")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = open(args.log_path, "w", encoding="utf-8")

    pdf_files = sorted(input_dir.glob("*.pdf"))

    for idx, pdf_path in enumerate(tqdm(pdf_files, desc="Processing PDFs"), start=1):
        filename_base = pdf_path.stem if args.use_filename else f"image_{idx}"
        log_lines = [f"[{idx}] {pdf_path.name}"]

        try:
            images = convert_from_path(str(pdf_path), dpi=300)
            text_by_page = extract_text_by_page(pdf_path)
        except Exception as e:
            log_lines.append(f"  [x] Error processing PDF: {e}")
            log_file.write("\n".join(log_lines) + "\n\n")
            continue

        total_pages = len(text_by_page)
        non_empty_pages = [i for i, page in enumerate(text_by_page) if any(w[4].strip() for w in page)]
        num_non_empty = len(non_empty_pages)

        log_lines.append(f"  → {num_non_empty} non-empty page(s) out of {total_pages}")

        if args.skip_empty and num_non_empty == 0:
            log_lines.append("  [!] Skipped due to empty content")
            log_file.write("\n".join(log_lines) + "\n\n")
            continue

        for i, (img, words) in enumerate(zip(images, text_by_page)):
            if args.skip_empty and i not in non_empty_pages:
                continue

            if total_pages == 1:
                image_name = f"{filename_base}.png"
                json_name = f"{filename_base}.json"
            else:
                image_name = f"{filename_base}_page{i+1}.png"
                json_name = f"{filename_base}_page{i+1}.json"

            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("error", category=DecompressionBombWarning)

                    if args.detect_blank:
                        gray_img = img.convert("L")
                        hist = gray_img.histogram()
                        total_pixels = gray_img.width * gray_img.height
                        non_white_pixels = sum(hist[j] for j in range(0, 250))
                        non_white_ratio = non_white_pixels / total_pixels

                        if non_white_ratio < 0.01:
                            log_lines.append(f"  [!] Skipped page {i+1} due to being nearly all white (via histogram)")
                            continue

                    img.save(output_dir / image_name)

            except DecompressionBombWarning:
                log_lines.append(f"  [!] Skipped page {i+1} due to DecompressionBombWarning")
                continue
            except Exception as e:
                log_lines.append(f"  [x] Error saving image for page {i+1}: {e}")
                continue

            page_text_data = [
                {
                    "text": word[4],
                    "bbox": word[:4],
                    "block": word[5],
                    "line": word[6],
                    "word_num": word[7]
                }
                for word in words if word[4].strip()
            ]
            with open(output_dir / json_name, "w", encoding="utf-8") as f:
                json.dump(page_text_data, f, indent=2, ensure_ascii=False)

        log_lines.append(f"  → Saved {num_non_empty} page(s) to {output_dir}")
        log_file.write("\n".join(log_lines) + "\n\n")

    log_file.close()

if __name__ == "__main__":
    main()
