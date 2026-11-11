from pathlib import Path
import csv
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
CLEAN_DIR = ROOT / "clean"
OUT_DIR = ROOT / "noisy_synthetic"
BENCH_DIR = ROOT / "benchmark_sizes"
BASE_SEED = 2026

CLEAN_IMAGES = ["clean_cameraman", "clean_crowd", "clean_woman", "clean_characters"]

# periods = [(chu kỳ theo hàng, chu kỳ theo cột)] tính bằng pixel; None = không đổi theo trục đó
NOISES = [
    {"name": "sin_single", "kind": "sine", "amp": 30, "periods": [(16, 16)], "phase": 0.6},
    {"name": "sin_multi",  "kind": "sine", "amp": 20, "periods": [(16, 16), (8, 16)], "phase": 0.6},
    {"name": "stripes_h",  "kind": "sine", "amp": 25, "periods": [(16, None)], "phase": 0.6},
    {"name": "stripes_v",  "kind": "sine", "amp": 25, "periods": [(None, 16)], "phase": 0.6},
    {"name": "gaussian",   "kind": "gaussian", "sigma": 20},
    {"name": "saltpepper", "kind": "saltpepper", "p": 0.05},
]

BENCH_SOURCE = "clean_washington_ir"
BENCH_SIZES = [64, 128, 256, 512, 1024, 2048]


def load_gray(path):
    return np.array(Image.open(path).convert("L"))


def sine_noise(shape, spec):
    """Nhiễu sin/sọc với tần số nguyên (chu kỳ/ảnh). Trả về (nhiễu float, tập đỉnh trong phổ đã dịch tâm)."""
    H, W = shape
    r = np.arange(H)[:, None]
    c = np.arange(W)[None, :]
    noise = np.zeros((H, W))
    peaks = set()
    for pu, pv in spec["periods"]:
        if pu is not None:
            assert H % pu == 0, f"H={H} không chia hết cho chu kỳ {pu}"
        if pv is not None:
            assert W % pv == 0, f"W={W} không chia hết cho chu kỳ {pv}"
        u0 = 0 if pu is None else H // pu     # số chu kỳ theo hàng
        v0 = 0 if pv is None else W // pv     # số chu kỳ theo cột
        noise += spec["amp"] * np.sin(2 * np.pi * (u0 * r / H + v0 * c / W) + spec["phase"])
        # phổ dịch tâm: DC ở (H//2, W//2), đỉnh đối xứng liên hợp
        peaks.add((H // 2 + u0, W // 2 + v0))
        peaks.add((H // 2 - u0, W // 2 - v0))
    return noise, peaks


def make_noisy(clean, spec, rng):
    f = clean.astype(np.float64)
    peaks = set()
    if spec["kind"] == "sine":
        noise, peaks = sine_noise(f.shape, spec)
        noisy = f + noise
    elif spec["kind"] == "gaussian":
        noisy = f + rng.normal(0, spec["sigma"], f.shape)
    else:  # saltpepper
        noisy = f.copy()
        m = rng.random(f.shape)
        noisy[m < spec["p"] / 2] = 0
        noisy[m >= 1 - spec["p"] / 2] = 255
    noisy = np.clip(np.rint(noisy), 0, 255).astype(np.uint8)
    return noisy, peaks


def check_peaks(clean, noisy, peaks):
    """Kiểm tra: các đỉnh lớn nhất của phổ (nhiễu - sạch) có đúng vị trí dự kiến không."""
    if not peaks:
        return "n/a"
    d = noisy.astype(np.float64) - clean.astype(np.float64)
    d -= d.mean()
    mag = np.abs(np.fft.fftshift(np.fft.fft2(d)))
    k = len(peaks)
    idx = np.argpartition(mag.ravel(), -k)[-k:]
    found = {tuple(int(v) for v in np.unravel_index(i, mag.shape)) for i in idx}
    return "OK" if found == peaks else "LECH"


def mse_psnr(a, b):
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    psnr = float("inf") if mse == 0 else 10 * np.log10(255.0 ** 2 / mse)
    return mse, psnr


def part_noisy():
    rows = []
    for i, name in enumerate(CLEAN_IMAGES):
        clean = load_gray(CLEAN_DIR / f"{name}.png")
        H, W = clean.shape
        for j, spec in enumerate(NOISES):
            seed = BASE_SEED + 100 * i + j
            rng = np.random.default_rng(seed)
            noisy, peaks = make_noisy(clean, spec, rng)
            out_dir = OUT_DIR / spec["name"]
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{name}__{spec['name']}.png"
            Image.fromarray(noisy).save(out_path)
            mse, psnr = mse_psnr(noisy, clean)
            check = check_peaks(clean, noisy, peaks)
            params = {k: v for k, v in spec.items() if k not in ("name", "kind")}
            rows.append([name, f"{W}x{H}", spec["name"], spec["kind"], str(params), seed,
                         sorted(peaks) if peaks else "", check,
                         round(mse, 3), round(psnr, 3), str(out_path.relative_to(ROOT))])
            print(f"[OK] {out_path.name:42s} MSE={mse:8.2f} PSNR={psnr:6.2f} dB  peak={check}")
    with open(OUT_DIR / "noise_params.csv", "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f)
        wr.writerow(["anh_sach", "kich_thuoc", "nhieu", "loai", "tham_so", "seed",
                     "dinh_ky_vong_(hang,cot)_0based_pho_dich_tam", "kiem_tra_dinh",
                     "MSE_vs_sach", "PSNR_vs_sach_dB", "file"])
        wr.writerows(rows)
    print("\nĐã ghi", OUT_DIR / "noise_params.csv")


def part_benchmark():
    BENCH_DIR.mkdir(exist_ok=True)
    src = Image.open(CLEAN_DIR / f"{BENCH_SOURCE}.png").convert("L")
    for s in BENCH_SIZES:
        im = src.resize((s, s), Image.Resampling.LANCZOS)
        im.save(BENCH_DIR / f"{BENCH_SOURCE}_{s}.png")
        print(f"[OK] benchmark {s}x{s}")


if __name__ == "__main__":
    part_noisy()
    part_benchmark()