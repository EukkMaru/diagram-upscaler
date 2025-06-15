page = img.convert("L")                 # reuse for all words
            mask = Image.new("L", img.size, 0)           # black background

            THRESH = 220                                 # 0-255, tweak if needed

            for w in words:
                if not w[4].strip():                     # ignore empty strings
                    continue
                # word bbox → pixel coords
                x0, y0, x1, y1 = (int(c * SCALE) for c in w[:4])
                crop = gray_page.crop((x0, y0, x1, y1))  # grayscale crop

                # binarise: text pixels (<THRESH) → 255, else 0
                bw = crop.point(lambda p: 255 if p < THRESH else 0)

                # paste into mask; use itself as the alpha so only white pixels land
                mask.paste(bw, (x0, y0), bw)

            mask_name = f"{filename_base}{suffix}_mask.png"
            mask.save(output_dir / mask_name)