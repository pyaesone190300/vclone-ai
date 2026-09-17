FROM python:3.10-slim

# librosa & soundfile အတွက် လိုအပ်သော ffmpeg, sndfile စသည်တို့ ထည့်သွင်းခြင်း
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
