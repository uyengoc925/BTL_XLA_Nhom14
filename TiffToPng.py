from pathlib import Path
import csv
import numpy as np
from PIL import Image

ROOT = Path("D:\\UYEN\\Nam4\\XLA\\BT CODE\\BTL_XLA").resolve().parent                 # BTL_XLA
SEARCH_DIRS = [ROOT, ROOT / "original_tif"] + sorted(ROOT.parent.glob("DIP3E_*"))

# tên file gốc -> (thư mục đích, tên mới không dấu ngoặc)
PLAN = {
    "Fig0222(b)(cameraman).tif":              ("clean",       "clean_cameraman"),
    "Fig0222(c)(crowd).tif":                  ("clean",       "clean_crowd"),
    "Fig0427(a)(woman).tif":                  ("clean",       "clean_woman"),
    "Fig0441(a)(characters_test_pattern).tif":("clean",       "clean_characters"),
    "Fig0227(a)(washington_infrared).tif":    ("clean",       "clean_washington_ir"),
    "Fig0429(a)(blown_ic).tif":               ("demo_theory", "demo_blown_ic"),
    "Fig0424(a)(rectangle).tif":              ("demo_theory", "demo_rectangle"),
    "Fig0425(a)(translated_rectangle).tif":   ("demo_theory", "demo_translated_rectangle"),
    "Fig0464(a)(car_75DPI_Moire).tif":        ("real_noisy",  "real_car_moire"),
    "Fig0465(a)(cassini).tif":                ("real_noisy",  "real_cassini"),
}

def find_file(name):
    target = name.lower()
    for d in SEARCH_DIRS:
        if d.exists():
            for p in d.rglob("*.tif"):
                if p.name.lower() == target:
                    return p
    return None

def to_gray8(im):
    """Trả về (mảng uint8 2D, ghi chú)."""
    mode = im.mode
    if mode == "L":
        return np.array(im), ""
    if mode == "1":
        return np.array(im, dtype=np.uint8) * 255, "nhị phân -> 0/255"
    if mode == "LA":
        return np.array(im.convert("L")), "bỏ kênh alpha"
    if mode in ("RGB", "RGBA", "P"):
        rgb = np.array(im.convert("RGB"))
        same = np.array_equal(rgb[..., 0], rgb[..., 1]) and np.array_equal(rgb[..., 1], rgb[..., 2])
        if same:
            return rgb[..., 0], f"{mode} nhưng 3 kênh giống nhau (thực chất là xám)"
        return np.array(im.convert("RGB").convert("L")), f"!!! {mode} MÀU THẬT, đã đổi bằng công thức độ sáng"
    # 16-bit, 32-bit, float
    a = np.array(im).astype(np.float64)
    if a.ndim == 3:
        a = a[..., 0]
    if a.min() >= 0 and a.max() <= 255:
        return a.astype(np.uint8), f"{mode} nhưng giá trị trong 0-255, ép kiểu trực tiếp"
    lo, hi = a.min(), a.max()
    out = np.round((a - lo) / (hi - lo) * 255).astype(np.uint8)
    return out, f"{mode}: co giãn tuyến tính [{lo:g},{hi:g}] -> [0,255]"

rows = []
for name, (folder, new) in PLAN.items():
    src = find_file(name)
    if src is None:
        print(f"[KHÔNG TÌM THẤY] {name}")
        rows.append([name, "", "", "", "", "", "", folder, new, "không tìm thấy"])
        continue
    im = Image.open(src)                 # nếu TIFF nhiều trang, chỉ lấy trang đầu
    raw = np.array(im)
    gray, note = to_gray8(im)
    h, w = gray.shape
    pow2 = (h & (h - 1) == 0) and (w & (w - 1) == 0)
    if not pow2:
        note = (note + "; " if note else "") + "kích thước không phải lũy thừa 2"
    out_dir = ROOT / folder
    out_dir.mkdir(exist_ok=True)
    Image.fromarray(gray, mode="L").save(out_dir / f"{new}.png")
    print(f"[OK] {name:45s} mode={im.mode:6s} {w}x{h}  -> {folder}/{new}.png  {note}")
    rows.append([name, str(src), im.mode, f"{w}x{h}", raw.dtype, raw.min(), raw.max(),
                 folder, new, note])

with open(ROOT / "dataset_table.csv", "w", newline="", encoding="utf-8-sig") as f:
    wr = csv.writer(f)
    wr.writerow(["file_goc", "duong_dan", "mode_goc", "kich_thuoc", "dtype_goc",
                 "min_goc", "max_goc", "thu_muc_dich", "ten_moi", "ghi_chu"])
    wr.writerows(rows)
print("\nĐã ghi dataset_table.csv " )