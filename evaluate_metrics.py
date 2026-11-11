
from pathlib import Path
import csv
import ast
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity


# ==============================
# 1. CẤU HÌNH
# ==============================

ROOT = Path(__file__).resolve().parent

CLEAN_DIR = ROOT / "clean"
NOISY_DIR = ROOT / "noisy_synthetic"

RESULT_DIR = ROOT / "results" / "metrics"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = RESULT_DIR / "metrics_results.csv"

L = 256
PEAK_RADIUS = 2


# Khai báo các thí nghiệm cần đánh giá.
# Thay filtered_path bằng đường dẫn ảnh đầu ra thực tế
# do Hoàng cung cấp.

EXPERIMENTS = [
    {
        "image": "clean_cameraman",
        "noise": "sin_single",
        "filtered_path": "results/filtered/cameraman_notch.png"
    },
]


# ==============================
# 2. ĐỌC ẢNH
# ==============================

def load_gray(path):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy ảnh: {path}")

    return np.array(
        Image.open(path).convert("L"),
        dtype=np.float64
    )


def check_images(a, b):
    if a.shape != b.shape:
        raise ValueError(
            f"Kích thước ảnh không khớp: {a.shape} và {b.shape}"
        )


# ==============================
# 3. MSE
# ==============================

def calculate_mse(original, restored):
    check_images(original, restored)

    error = original - restored

    return np.mean(error ** 2)


# ==============================
# 4. RMSE
# ==============================

def calculate_rmse(original, restored):
    mse = calculate_mse(original, restored)

    return np.sqrt(mse)


# ==============================
# 5. SNR
# ==============================

def calculate_snr(original, restored):
    check_images(original, restored)

    signal_power = np.sum(original ** 2)

    noise_power = np.sum((original - restored) ** 2)

    if noise_power == 0:
        return float("inf")

    if signal_power == 0:
        return float("-inf")

    return 10 * np.log10(signal_power / noise_power)


# ==============================
# 6. PSNR
# ==============================

def calculate_psnr(original, restored):
    mse = calculate_mse(original, restored)

    if mse == 0:
        return float("inf")

    return 10 * np.log10((L - 1) ** 2 / mse)


# ==============================
# 7. SSIM
# ==============================

def calculate_ssim(original, restored):
    check_images(original, restored)

    return structural_similarity(
        original.astype(np.uint8),
        restored.astype(np.uint8),
        data_range=L - 1
    )


# ==============================
# 8. ERES
# ==============================

def calculate_eres(noisy, restored, peaks, radius=2):
    """
    peaks: danh sách tọa độ đỉnh trên phổ đã dịch tâm.
           Ví dụ: [(136, 136), (120, 120)]

    radius: bán kính vùng khảo sát quanh mỗi đỉnh.
    """

    check_images(noisy, restored)

    if not peaks:
        return None

    H, W = noisy.shape

    # FFT và dịch tâm phổ
    F_in = np.fft.fftshift(np.fft.fft2(noisy))
    F_out = np.fft.fftshift(np.fft.fft2(restored))

    # Tạo mặt nạ vùng đỉnh nhiễu
    y, x = np.ogrid[:H, :W]

    mask = np.zeros((H, W), dtype=bool)

    for py, px in peaks:

        distance = (y - py) ** 2 + (x - px) ** 2

        mask |= distance <= radius ** 2

    # Tổng năng lượng trước và sau lọc
    energy_in = np.sum(np.abs(F_in[mask]) ** 2)

    energy_out = np.sum(np.abs(F_out[mask]) ** 2)

    if energy_in == 0:
        return None

    return energy_out / energy_in * 100


# ==============================
# 9. ĐỌC TỌA ĐỘ ĐỈNH TỪ CSV
# ==============================

def load_noise_peaks(noise_name, image_name):
    csv_path = NOISY_DIR / "noise_params.csv"

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:

            if (row["anh_sach"] == image_name
                    and row["nhieu"] == noise_name):

                value = row[
                    "dinh_ky_vong_(hang,cot)_0based_pho_dich_tam"
                ]

                if not value:
                    return []

                return [
                    tuple(p) for p in ast.literal_eval(value)
                ]

    raise ValueError(
        f"Không tìm thấy cấu hình {image_name}, {noise_name}"
    )


# ==============================
# 10. ĐÁNH GIÁ MỘT ẢNH
# ==============================

def evaluate_one(original, restored):

    return {
        "MSE": calculate_mse(original, restored),
        "RMSE": calculate_rmse(original, restored),
        "SNR_dB": calculate_snr(original, restored),
        "PSNR_dB": calculate_psnr(original, restored),
        "SSIM": calculate_ssim(original, restored)
    }


# ==============================
# 11. CHẠY THỰC NGHIỆM
# ==============================

def main():

    rows = []

    for exp in EXPERIMENTS:

        image_name = exp["image"]
        noise_name = exp["noise"]

        clean_path = CLEAN_DIR / f"{image_name}.png"

        noisy_path = (
            NOISY_DIR / noise_name /
            f"{image_name}__{noise_name}.png"
        )

        filtered_path = ROOT / exp["filtered_path"]

        clean = load_gray(clean_path)
        noisy = load_gray(noisy_path)
        filtered = load_gray(filtered_path)

        check_images(clean, noisy)
        check_images(clean, filtered)

        # Đọc các đỉnh nhiễu đã biết
        peaks = load_noise_peaks(noise_name, image_name)

        # Đánh giá ảnh nhiễu và ảnh sau lọc
        for method, result in [
            ("Noisy", noisy),
            ("Filtered", filtered)
        ]:

            metrics = evaluate_one(clean, result)

            if method == "Filtered" and peaks:
                eres = calculate_eres(
                    noisy, filtered, peaks, PEAK_RADIUS
                )
            elif method == "Noisy" and peaks:
                eres = 100.0
            else:
                eres = None

            row = {
                "Image": image_name,
                "Noise": noise_name,
                "Method": method,
                **metrics,
                "Eres_percent": eres
            }

            rows.append(row)

            print(
                f"{image_name} | {noise_name} | {method}"
            )

            print(metrics)
            print("Eres:", eres)
            print("-" * 50)

    # Xuất CSV
    if rows:

        with open(
            OUTPUT_CSV,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=rows[0].keys()
            )

            writer.writeheader()
            writer.writerows(rows)

        print("Đã lưu kết quả:", OUTPUT_CSV)

if __name__ == "__main__":

    clean = load_gray(
        CLEAN_DIR / "clean_cameraman.png"
    )

    noisy = load_gray(
        NOISY_DIR / "sin_single" /
        "clean_cameraman__sin_single.png"
    )

    print("MSE:", calculate_mse(clean, noisy))
    print("RMSE:", calculate_rmse(clean, noisy))
    print("SNR:", calculate_snr(clean, noisy))
    print("PSNR:", calculate_psnr(clean, noisy))
    print("SSIM:", calculate_ssim(clean, noisy))