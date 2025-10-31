# Sử dụng base image Python chính thức (ví dụ: Python 3.11)
FROM python:3.11-slim

# 1. Cài đặt FFmpeg và các thư viện cần thiết cho Voice (libopus-dev)
# FFmpeg là công cụ xử lý âm thanh chính.
RUN apt-get update && \
    apt-get install -y ffmpeg libopus-dev && \
    rm -rf /var/lib/apt/lists/*

# 2. Thiết lập thư mục làm việc
WORKDIR /usr/src/app

# 3. Sao chép và cài đặt các gói Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Sao chép toàn bộ mã nguồn bot vào thư mục làm việc
COPY . .

# 5. Thiết lập Biến môi trường (Railway sẽ tự động thêm TOKEN của bạn)
# Nếu bạn cần một biến môi trường khác, hãy thêm ở đây

# 6. Lệnh chạy bot (Đảm bảo tên file chính của bot là main.py hoặc bot.py)
# Tôi giả định file của bạn tên là 'bot_main.py' (hoặc tên file bạn dùng để chứa toàn bộ code)
CMD ["python3", "main.py"]
