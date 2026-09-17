FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    libsndfile1 \
    libportaudio2 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# RVC
RUN git clone \
    https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git \
    /app/RVC

WORKDIR /app/RVC

# Official PyPI / PyTorch CPU indexes
RUN sed -i \
    's#https://mirrors.pku.edu.cn/pypi/simple#https://pypi.org/simple#g' \
    requirments_cpu_py312.txt

RUN sed -i \
    's#https://mirrors.nju.edu.cn/pytorch/whl/cpu#https://download.pytorch.org/whl/cpu#g' \
    requirments_cpu_py312.txt

RUN python -m pip install --upgrade \
    pip setuptools wheel

RUN python -m pip install \
    -r requirments_cpu_py312.txt

WORKDIR /app

COPY requirements.txt .

RUN pip install \
    -r requirements.txt

COPY bot.py .

COPY models ./models

RUN mkdir -p /app/work

ENV MODEL_PATH=/app/models/MyVoice.pth
ENV INDEX_PATH=/app/models/MyVoice.index
ENV TTS_VOICE=my-MM-ThihaNeural

CMD ["python", "bot.py"]
