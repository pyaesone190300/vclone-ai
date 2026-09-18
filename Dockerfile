# Python 3.9 ကို ပြောင်းလဲအသုံးပြုခြင်း
FROM python:3.9-slim

WORKDIR /app

# C++ Compile tools များ
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    g++ \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Dependency Conflict မဖြစ်စေရန် PyTorch ကို requirements.txt ထက် အရင်သွင်းခြင်း
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# ထို့နောက်မှ ကျန်ရှိသော libraries များကို သွင်းခြင်း
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p downloads models

CMD ["python", "main.py"]
