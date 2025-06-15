import os
import argparse
import csv
from glob import glob
from PIL import Image
import numpy as np
import torch
import lpips
import cv2
from skimage.metrics import peak_signal_noise_ratio, structural_similarity
import easyocr
from tqdm import tqdm
import json
import difflib

def load_image(path):
    return np.array(Image.open(path).convert('RGB'))

def compute_global_metrics(gt, pred, lpips_model=None, use_psnr=True, use_ssim=True, use_lpips=True):
    results = {}
    if use_psnr:
        psnr = peak_signal_noise_ratio(gt, pred, data_range=255)
        results["psnr"] = psnr
    if use_ssim:
        ssim = structural_similarity(gt, pred, channel_axis=2, data_range=255)
        results["ssim"] = ssim
    if use_lpips and lpips_model is not None:
        t_gt = torch.tensor(gt).permute(2,0,1).unsqueeze(0).float() / 255 * 2 - 1
        t_pred = torch.tensor(pred).permute(2,0,1).unsqueeze(0).float() / 255 * 2 - 1
        if torch.cuda.is_available():
            t_gt = t_gt.cuda()
            t_pred = t_pred.cuda()
        with torch.no_grad():
            lpips_val = lpips_model(t_gt, t_pred).item()
        results["lpips"] = lpips_val
    return results

def compute_box_metrics(gt, pred, boxes, lpips_model=None, use_psnr=True, use_ssim=True, use_lpips=True):
    psnrs, ssims, lpips_vals = [], [], []
    for box in boxes:
        x1, y1, x2, y2 = map(int, box)
        gt_crop = gt[y1:y2, x1:x2]
        pred_crop = pred[y1:y2, x1:x2]
        if gt_crop.shape[0] == 0 or gt_crop.shape[1] == 0:
            continue
        if use_psnr:
            psnrs.append(peak_signal_noise_ratio(gt_crop, pred_crop, data_range=255))
        if use_ssim:
            ssims.append(structural_similarity(gt_crop, pred_crop, channel_axis=2, data_range=255))
        if use_lpips and lpips_model is not None:
            t_gt = torch.tensor(gt_crop).permute(2,0,1).unsqueeze(0).float() / 255 * 2 - 1
            t_pred = torch.tensor(pred_crop).permute(2,0,1).unsqueeze(0).float() / 255 * 2 - 1
            if torch.cuda.is_available():
                t_gt = t_gt.cuda()
                t_pred = t_pred.cuda()
            with torch.no_grad():
                lp = lpips_model(t_gt, t_pred).item()
            lpips_vals.append(lp)
    return psnrs, ssims, lpips_vals

def compute_ocr_accuracy(gt_img, pred_img, boxes, ocr_reader):
    accs = []
    for box in boxes:
        x1, y1, x2, y2 = map(int, box)
        gt_crop = gt_img[y1:y2, x1:x2]
        pred_crop = pred_img[y1:y2, x1:x2]

        gt_result = ocr_reader.readtext(gt_crop, detail=0, paragraph=False)
        pred_result = ocr_reader.readtext(pred_crop, detail=0, paragraph=False)

        gt_text = ''.join(gt_result).strip()
        pred_text = ''.join(pred_result).strip()

        sm = difflib.SequenceMatcher(None, pred_text, gt_text)
        accs.append(sm.ratio())
    return accs

def levenshtein_accuracy(pred, gt):
    sm = difflib.SequenceMatcher(None, pred, gt)
    return sm.ratio()

def parse_boxes_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    boxes, texts = [], []
    for item in data:
        x1, y1, x2, y2 = map(int, item['bbox'])
        boxes.append((x1, y1, x2, y2))
        texts.append(item['text'])
    return boxes, texts

def get_lpips_model(model_name='alex'):
    model = lpips.LPIPS(net=model_name)
    if torch.cuda.is_available():
        model = model.cuda()
    return model

def main(args):
    lpips_model = get_lpips_model(args.lpips_model) if args.lpips else None
    ocr_reader = easyocr.Reader(['en', 'latin']) if args.ocr else None

    image_pairs = sorted(zip(
        sorted(glob(os.path.join(args.gt_dir, "*.png"))),
        sorted(glob(os.path.join(args.pred_dir, "*.png")))
    ))

    with open(args.output_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        headers = ['index']
        if args.psnr: headers += ['global_psnr']
        if args.ssim: headers += ['global_ssim']
        if args.lpips: headers += ['global_lpips']
        if args.psnr: headers += ['box_psnr_list']
        if args.ssim: headers += ['box_ssim_list']
        if args.lpips: headers += ['box_lpips_list']
        if args.ocr: headers += ['ocr_accuracy_list']
        writer.writerow(headers)

        for idx, (gt_path, pred_path) in enumerate(tqdm(image_pairs)):
            gt_img = load_image(gt_path)
            pred_img = load_image(pred_path).astype(np.uint8)
            pred_img = np.array(Image.fromarray(pred_img).resize(gt_img.shape[1::-1], Image.BICUBIC))
            base_name = os.path.splitext(os.path.basename(gt_path))[0]
            box_file = os.path.join(args.box_dir, base_name + ".json")

            row = [idx]
            global_metrics = compute_global_metrics(gt_img, pred_img, lpips_model, args.psnr, args.ssim, args.lpips)
            if args.psnr: row.append(global_metrics.get("psnr", ""))
            if args.ssim: row.append(global_metrics.get("ssim", ""))
            if args.lpips: row.append(global_metrics.get("lpips", ""))

            boxes, texts = parse_boxes_json(box_file)
            box_psnr, box_ssim, box_lpips = compute_box_metrics(gt_img, pred_img, boxes, lpips_model, args.psnr, args.ssim, args.lpips)
            if args.psnr: row.append(box_psnr)
            if args.ssim: row.append(box_ssim)
            if args.lpips: row.append(box_lpips)

            if args.ocr:
                ocr_acc = compute_ocr_accuracy(pred_img, boxes, texts, ocr_reader)
                row.append(ocr_acc)

            writer.writerow(row)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--gt_dir', required=True, help='Ground truth image directory')
    parser.add_argument('--pred_dir', required=True, help='Upscaled image directory')
    parser.add_argument('--box_dir', required=True, help='Bounding box JSON file directory')
    parser.add_argument('--output_csv', default='evaluation_results.csv', help='Output CSV path')
    parser.add_argument('--psnr', action='store_true', help='Include PSNR')
    parser.add_argument('--ssim', action='store_true', help='Include SSIM')
    parser.add_argument('--lpips', action='store_true', help='Include LPIPS')
    parser.add_argument('--lpips_model', default='alex', choices=['alex', 'vgg', 'squeeze'], help='Backbone for LPIPS')
    parser.add_argument('--ocr', action='store_true', help='Include OCR accuracy')
    args = parser.parse_args()
    main(args)
