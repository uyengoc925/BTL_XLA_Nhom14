# BÀI TẬP LỚN XỬ LÝ ẢNH (DIGITAL IMAGE PROCESSING)
## Đề tài: Nghiên Cứu & Thực Nghiệm Lọc Nhiễu Tuần Hoàn và Nhiễu Ngẫu Nhiên trong Miền Tần Số & Miền Không Gian (Python vs ImageJ/Fiji)

---

## 📑 MỤC LỤC
1. [Tổng Quan Dự Án](#1-tổng-quan-dự-án)
2. [Cấu Trúc Thư Mục Dự Án](#2-cấu-trúc-thư-mục-dự-án)
3. [Mô Tả Chi Tiết Các Thư Mục Lưu Trữ Ảnh](#3-mô-tả-chi-tiết-các-thư-mục-lưu-trữ-ảnh)
4. [Mô Tả Chi Tiết Các Script & File Dữ Liệu](#4-mô-tả-chi-tiết-các-script--file-dữ-liệu)
5. [Hướng Dẫn Cài Đặt & Chạy Thực Nghiệm](#5-hướng-dẫn-chạy-thử)

---

## 1. TỔNG QUAN DỰ ÁN
Dự án tập trung vào việc nghiên cứu, mô phỏng toán học và thực nghiệm so sánh các kỹ thuật lọc ảnh:
- **Lọc trong miền tần số (Frequency Domain Filtering):** Biến đổi Fourier 2D (FFT/DFT), bộ lọc chặn đỉnh tuần hoàn (Notch Reject Filter), bộ lọc triệt tiêu sọc (Suppress Stripes).
- **Lọc trong miền không gian (Spatial Domain Filtering):** Bộ lọc trung bình (Mean Filter) và bộ lọc trung vị (Median Filter).
- **So sánh đa nền tảng:** Đối chiếu triển khai thuật toán tùy biến bằng **Python** với các công cụ chuẩn công nghiệp trong **Fiji (ImageJ)**.

---

## 2. CẤU TRÚC THƯ MỤC DỰ ÁN

```text
BTL_XLA/
├── original_tif/                 # Ảnh gốc định dạng TIFF (DIP3E Gonzalez & Woods)
├── clean/                        # 5 ảnh sạch chuẩn hóa (Grayscale 8-bit PNG)
├── demo_theory/                  # 3 ảnh phục vụ minh họa lý thuyết biến đổi Fourier
├── real_noisy/                   # 2 ảnh có nhiễu thực tế (không có ảnh sạch đối chứng)
├── noisy_synthetic/              # Ảnh tổng hợp nhiễu nhân tạo có Ground Truth (24 ảnh)
│   ├── gaussian/                 # Nhiễu Gauss (sigma = 20)
│   ├── saltpepper/               # Nhiễu muối tiêu (mật độ 5%)
│   ├── sin_single/               # Nhiễu sin đơn 1 hướng chéo (chu kỳ 16 px)
│   ├── sin_multi/                # Nhiễu sin đa thành phần (chu kỳ 16 px & 8 px)
│   ├── stripes_h/                # Nhiễu sọc ngang (chu kỳ 16 px)
│   ├── stripes_v/                # Nhiễu sọc dọc (chu kỳ 16 px)
│   └── noise_params.csv          # Bảng thông số chi tiết của 24 cấu hình nhiễu
├── benchmark_sizes/              # Bộ ảnh các kích thước lũy thừa 2 (64x64 đến 2048x2048)
├── results/                      # Thư mục lưu kết quả xử lý và đánh giá
│   ├── filtered/                 # Ảnh sau khi lọc qua Python và Fiji
│   └── metrics/                  # Bảng số liệu đo lường chỉ số chất lượng
│       └── metrics_results.csv   # Kết quả đo đạc tự động (MSE, PSNR, SSIM, Eres,...)
├── dataset_table.csv             # Bảng danh mục metadata của toàn bộ ảnh gốc
├── TiffToPng.py                  # Script tiền xử lý: TIF -> PNG 8-bit Grayscale
├── make_ground_truth.py          # Script sinh nhiễu nhân tạo & tạo bộ ảnh benchmark
├── evaluate_metrics.py           # Script tự động tính toán các chỉ số đánh giá chất lượng
├── .gitignore                    # Cấu hình bỏ qua file tạm cho Git
└── README.md                     # Tài liệu hướng dẫn chi tiết dự án
```

---

## 3. MÔ TẢ CHI TIẾT CÁC THƯ MỤC LƯU TRỮ ẢNH

| Thư mục | Định dạng | Mục đích sử dụng | Danh sách ảnh & Mô tả |
| :--- | :--- | :--- | :--- |
| **`original_tif/`** | `.tif` | Lưu trữ file nguyên bản trích xuất từ đĩa kèm sách *Digital Image Processing (3rd Edition)* của tác giả Gonzalez & Woods. Giữ nguyên độ phân giải và thông số gốc. | • `Fig0222(b)(cameraman).tif`<br>• `Fig0222(c)(crowd).tif`<br>• `Fig0227(a)(washington_infrared).tif`<br>• `Fig0424(a)(rectangle).tif`<br>• `Fig0425(a)(translated_rectangle).tif`<br>• `Fig0427(a)(woman).tif`<br>• `Fig0429(a)(blown_ic).tif`<br>• `Fig0441(a)(characters_test_pattern).tif`<br>• `Fig0464(a)(car_75DPI_Moire).tif`<br>• `Fig0465(a)(cassini).tif` |
| **`clean/`** | `.png` | Bộ 5 ảnh sạch chuẩn hóa về định dạng **Grayscale 8-bit (uint8, thang độ xám [0, 255])**. Dùng làm ảnh chuẩn đối chứng (**Ground Truth**) để đo lường định lượng các chỉ số phục hồi ảnh. | • `clean_cameraman.png` ($256 \times 256$)<br>• `clean_crowd.png` ($512 \times 512$)<br>• `clean_woman.png` ($512 \times 512$)<br>• `clean_characters.png` ($688 \times 688$)<br>• `clean_washington_ir.png` ($1024 \times 1024$, ảnh hồng ngoại vệ tinh dùng làm nguồn benchmark) |
| **`noisy_synthetic/`** | `.png` | Chứa **24 ảnh** tổng hợp nhiễu nhân tạo có kiểm soát toán học chặt chẽ. Được chia thành 6 thư mục con theo từng loại nhiễu tác động lên 4 ảnh sạch (`cameraman`, `crowd`, `woman`, `characters`). | • `sin_single/`: Nhiễu sin đơn chéo 1 cặp đỉnh phổ đối xứng.<br>• `sin_multi/`: Nhiễu sin đa hướng gồm 2 cặp đỉnh đối xứng.<br>• `stripes_h/`: Nhiễu sọc ngang (1 cặp đỉnh trên trục dọc phổ).<br>• `stripes_v/`: Nhiễu sọc dọc (1 cặp đỉnh trên trục ngang phổ).<br>• `gaussian/`: Nhiễu Gauss ngẫu nhiên ($\mu=0, \sigma=20$).<br>• `saltpepper/`: Nhiễu muối tiêu ngẫu nhiên (mật độ 5%). |
| **`real_noisy/`** | `.png` | Chứa **2 ảnh** mang nhiễu thực tế thu thập từ thiết bị quét hoặc cảm biến ngoài không gian. Không có ảnh sạch đối chứng tương ứng. | • `real_car_moire.png` ($168 \times 246$): Nhiễu vân Moiré sinh ra khi quét lưới in nửa tông (halftone screen).<br>• `real_cassini.png` ($674 \times 674$): Nhiễu sọc tuần hoàn do lỗi phần cứng cảm biến từ tàu thăm dò Cassini khi chụp vành đai sao Thổ. |
| **`demo_theory/`** | `.png` | Chứa **3 ảnh** phục vụ việc phân tích các tính chất giải tích của phép biến đổi Fourier (DFT) trong báo cáo lý thuyết. | • `demo_rectangle.png` ($1024 \times 1024$): Hình chữ nhật căn giữa để khảo sát hàm sinc 2D.<br>• `demo_translated_rectangle.png` ($512 \times 512$): Hình chữ nhật bị tịnh tiến để chứng minh phổ biên độ bất biến với phép tịnh tiến.<br>• `demo_blown_ic.png` ($906 \times 678$): Ảnh mạch tích hợp vi mô bị lỗi tĩnh điện (chứng minh tính định hướng của phổ tần số). |
| **`benchmark_sizes/`** | `.png` | Bộ **6 ảnh** cùng nội dung nhưng được resize theo kích thước lũy thừa 2 chuẩn: $64\times64$, $128\times128$, $256\times256$, $512\times512$, $1024\times1024$, $2048\times2048$. Dùng độc lập cho bài toán đo thời gian chạy của thuật toán 2D FFT. | Nguồn gốc: Trích xuất và phóng to/thu nhỏ từ `clean_washington_ir.png` bằng thuật toán nội suy chất lượng cao **Lanczos** (PIL Image.Resampling.LANCZOS). |
| **`results/`** | Đa dạng | Nơi chứa sản phẩm đầu ra sau thực nghiệm. | • `results/filtered/`: Chứa các ảnh sau khi lọc bởi script Python (Gói 2) và macro Fiji (Gói 3).<br>• `results/metrics/`: Chứa các file bảng tổng kết số liệu đánh giá (`metrics_results.csv`). |

---

## 4. MÔ TẢ CHI TIẾT CÁC SCRIPT & FILE DỮ LIỆU

### 1. `TiffToPng.py`
- **Chức năng:** Tự động quét các ảnh gốc `.tif` từ thư mục `original_tif/`, chuẩn hóa định dạng ảnh sang ảnh xám 8-bit chuẩn (`uint8`, mode `L` trong PIL) và lưu trữ phân loại có tổ chức vào các thư mục tương ứng (`clean/`, `demo_theory/`, `real_noisy/`).
- **Xử lý đặc biệt:**
  - Kiểm tra số kênh màu, độ sâu bit và giải phóng kênh alpha nếu có.
  - Kiểm tra xem kích thước ảnh có phải là lũy thừa của 2 ($2^k$) hay không.
  - Tự động tạo và ghi chú chi tiết lịch sử chuyển đổi vào file `dataset_table.csv`.

### 2. `make_ground_truth.py`
- **Chức năng:** Tạo bộ dữ liệu tổng hợp nhiễu nhân tạo có kiểm soát (Ground Truth) và tạo bộ ảnh phục vụ đo kiểm benchmark.
- **Cơ chế hoạt động:**
  - Áp dụng 6 mô hình toán học của nhiễu lên 4 ảnh sạch (`clean_cameraman`, `clean_crowd`, `clean_woman`, `clean_characters`).
  - Thiết lập **Seed cố định** cho mỗi cặp `(ảnh, nhiễu)` nhằm đảm bảo khả năng tái lập kết quả thực nghiệm 100%.
  - Tự động tính toán vị trí tọa độ đỉnh lý thuyết trên phổ Fourier đã dịch tâm (`fftshift`), đồng thời xác minh kiểm tra đỉnh (`check_peaks`) xem đỉnh phổ thực tế có khớp vị trí kỳ vọng hay không.
  - Ép kiểu chuẩn: cắt ngưỡng `np.clip(..., 0, 255)` và làm tròn `np.rint(...)` sang `uint8`.
  - Tự động đo và ghi lại giá trị thực tế của MSE và PSNR vào file `noisy_synthetic/noise_params.csv`.
  - Sinh bộ ảnh 6 kích thước lũy thừa 2 vào `benchmark_sizes/` từ ảnh `clean_washington_ir`.

### 3. `evaluate_metrics.py`
- **Chức năng:** Bộ công cụ đánh giá chất lượng ảnh khách quan và độc lập. Đọc ảnh gốc (Ground Truth), ảnh nhiễu và ảnh kết quả sau lọc (từ cả Python Gói 2 và Fiji Gói 3) để tính toán toàn bộ các chỉ số chất lượng:
  - **MSE (Mean Squared Error):** Sai số bình phương trung bình.
  - **RMSE (Root Mean Squared Error):** Căn bậc hai sai số bình phương trung bình.
  - **SNR (Signal-to-Noise Ratio):** Tỷ số tín hiệu trên nhiễu (đơn vị dB).
  - **PSNR (Peak Signal-to-Noise Ratio):** Tỷ số tín hiệu cực đại trên nhiễu (đơn vị dB).
  - **SSIM (Structural Similarity Index):** Chỉ số tương đồng cấu trúc (sử dụng thư viện `scikit-image`).
  - **$E_{res}$ (Residual Peak Energy Percentage):** Tỷ lệ phần trăm năng lượng phổ còn sót lại tại các vùng lân cận đỉnh nhiễu với bán kính khảo sát $R$ (mặc định $R=2$ pixel).
- **Đầu ra:** Xuất dữ liệu thống kê bảng ra file `results/metrics/metrics_results.csv`.

### 4. `dataset_table.csv`
- Bảng nhật ký siêu dữ liệu chi tiết của 10 ảnh gốc từ giáo trình DIP3E: đường dẫn nguồn, chế độ màu ban đầu, kích thước ảnh, kiểu dữ liệu, khoảng giá trị mức xám `[min, max]`, thư mục đích và ghi chú kiểm tra lũy thừa 2.

### 5. `noisy_synthetic/noise_params.csv`
- Bảng tham số đầy đủ của 24 ảnh nhân tạo: tên ảnh sạch, kích thước, tên nhiễu, loại nhiễu, tham số chi tiết (biên độ, chu kỳ hàng/cột, độ lệch pha, sigma, tỉ lệ salt-pepper), giá trị seed, tọa độ đỉnh lý thuyết `(u0, v0)`, trạng thái kiểm tra đỉnh (OK/n-a), cùng giá trị chuẩn MSE và PSNR thực tế so với ảnh sạch.

---


# 5. HƯỚNG DẪN CHẠY THỬ 

## Đánh giá chất lượng ảnh bằng `evaluate_metrics.py`

### 1. Cài đặt thư viện

Mở Terminal tại thư mục gốc của dự án và cài các thư viện cần thiết:

```bash
python -m pip install numpy pillow scikit-image
```

### 2. Chuẩn bị ảnh và cấu hình thí nghiệm

Trước khi chạy, cần có ảnh gốc trong `clean/`, ảnh nhiễu tương ứng trong
`noisy_synthetic/<loại_nhiễu>/` và ảnh đã lọc trong `results/filtered/`.
Các ảnh phải có cùng kích thước. File `noisy_synthetic/noise_params.csv`
cũng cần có cấu hình tương ứng để script tra tọa độ đỉnh nhiễu khi tính
$E_{res}$.

Mở `evaluate_metrics.py` và cập nhật danh sách `EXPERIMENTS` cho các ảnh muốn
đánh giá. Mỗi mục gồm:

- `image`: tên ảnh gốc, không gồm phần mở rộng `.png` (ví dụ `clean_cameraman`).
- `noise`: tên thư mục loại nhiễu, đồng thời phải khớp giá trị `nhieu` trong
  `noise_params.csv` (ví dụ `sin_single`).
- `filtered_path`: đường dẫn ảnh đã lọc tương đối từ thư mục gốc dự án.

Ví dụ cấu hình mặc định:

```python
EXPERIMENTS = [
    {
        "image": "clean_cameraman",
        "noise": "sin_single",
        "filtered_path": "results/filtered/cameraman_notch.png"
    },
]
```

Để đánh giá nhiều ảnh, thêm các mục theo cùng định dạng vào danh sách.

### 3. Chạy chương trình

Từ thư mục gốc dự án, chạy:

```bash
python evaluate_metrics.py
```

Chương trình in các chỉ số MSE, RMSE, SNR, PSNR, SSIM và $E_{res}$ cho ảnh
nhiễu và ảnh đã lọc. Kết quả được ghi vào
`results/metrics/metrics_results.csv`; file này được tạo tự động và ghi đè ở
mỗi lần chạy. Nếu thiếu ảnh đầu vào hoặc không tìm thấy cấu hình nhiễu, script
sẽ báo lỗi và dừng.