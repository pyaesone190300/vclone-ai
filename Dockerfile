FROM python:3.10-slim

WORKDIR /app

# fairseq နှင့် pyworld အား compile လုပ်ရန် လိုအပ်သော C++ tools များ ထပ်မံထည့်သွင်းခြင်း
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    g++ \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# pip ကို update လုပ်ပြီး wheel နှင့် setuptools အား အရင်သွင်းခြင်း
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

COPY . .

RUN mkdir -p downloads models

CMD ["python", "main.py"]
