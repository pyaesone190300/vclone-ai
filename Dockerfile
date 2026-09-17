FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/RVC

# ============================================================
# SYSTEM PACKAGES
# ============================================================

RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    ffmpeg \
    libsndfile1 \
    libportaudio2 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


# ============================================================
# APP DIRECTORY
# ============================================================

WORKDIR /app


# ============================================================
# CLONE RVC
# ============================================================

RUN git clone \
    --depth 1 \
    https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git \
    /app/RVC

WORKDIR /app/RVC


# ============================================================
# FIX PYPI MIRRORS
# ============================================================

RUN sed -i \
    's#https://mirrors.pku.edu.cn/pypi/simple#https://pypi.org/simple#g' \
    requirments_cpu_py312.txt

RUN sed -i \
    's#https://mirrors.nju.edu.cn/pytorch/whl/cpu#https://download.pytorch.org/whl/cpu#g' \
    requirments_cpu_py312.txt


# ============================================================
# PIP
# ============================================================

RUN python -m pip install --upgrade \
    pip \
    setuptools \
    wheel


# ============================================================
# RVC DEPENDENCIES
# ============================================================

RUN python -m pip install \
    -r requirments_cpu_py312.txt


# ============================================================
# HUGGINGFACE HUB
#
# IMPORTANT:
# RVC requires huggingface-hub < 1.0
# ============================================================

RUN python -m pip install \
    "huggingface_hub>=0.26.0,<1.0"


# ============================================================
# VERIFY HUGGINGFACE VERSION
# ============================================================

RUN python -c "import huggingface_hub; print('huggingface_hub:', huggingface_hub.__version__)"


# ============================================================
# DOWNLOAD HUBERT
# ============================================================

RUN mkdir -p /app/RVC/assets

RUN huggingface-cli download \
    lj1995/VoiceConversionWebUI \
    --revision main \
    --include "hubert_base/*" \
    --local-dir /app/RVC/assets


# ============================================================
# DOWNLOAD RMVPE
# ============================================================

RUN mkdir -p /app/RVC/assets/rmvpe

RUN huggingface-cli download \
    lj1995/VoiceConversionWebUI \
    rmvpe.pt \
    --revision main \
    --local-dir /app/RVC/assets/rmvpe


# ============================================================
# VERIFY HUBERT
# ============================================================

RUN test -f /app/RVC/assets/hubert_base/config.json

RUN test -f /app/RVC/assets/hubert_base/preprocessor_config.json

RUN test -f /app/RVC/assets/hubert_base/pytorch_model.bin


# ============================================================
# VERIFY RMVPE
# ============================================================

RUN test -f /app/RVC/assets/rmvpe/rmvpe.pt


# ============================================================
# BACK TO APP
# ============================================================

WORKDIR /app


# ============================================================
# BOT REQUIREMENTS
# ============================================================

COPY requirements.txt .

RUN python -m pip install \
    --no-cache-dir \
    -r requirements.txt


# ============================================================
# DIRECTORIES
# ============================================================

RUN mkdir -p /app/models

RUN mkdir -p /app/work


# ============================================================
# GOOGLE DRIVE FILE IDs
# ============================================================

ARG MODEL_FILE_ID
ARG INDEX_FILE_ID


# ============================================================
# DOWNLOAD MyVoice.pth
# ============================================================

RUN if [ -n "$MODEL_FILE_ID" ]; then \
        echo "========================================"; \
        echo "Downloading MyVoice.pth"; \
        echo "========================================"; \
        gdown "$MODEL_FILE_ID" \
        -O /app/models/MyVoice.pth; \
    else \
        echo "ERROR: MODEL_FILE_ID is not set"; \
        exit 1; \
    fi


# ============================================================
# DOWNLOAD MyVoice.index
# ============================================================

RUN if [ -n "$INDEX_FILE_ID" ]; then \
        echo "========================================"; \
        echo "Downloading MyVoice.index"; \
        echo "========================================"; \
        gdown "$INDEX_FILE_ID" \
        -O /app/models/MyVoice.index; \
    else \
        echo "ERROR: INDEX_FILE_ID is not set"; \
        exit 1; \
    fi


# ============================================================
# VERIFY USER MODEL
# ============================================================

RUN test -f /app/models/MyVoice.pth

RUN test -f /app/models/MyVoice.index


# ============================================================
# SHOW FILES
# ============================================================

RUN echo "========================================"

RUN echo "MyVoice model files:"

RUN ls -lh /app/models/

RUN echo "========================================"

RUN echo "HuBERT files:"

RUN ls -lh /app/RVC/assets/hubert_base/

RUN echo "========================================"

RUN echo "RMVPE files:"

RUN ls -lh /app/RVC/assets/rmvpe/

RUN echo "========================================"


# ============================================================
# COPY BOT
# ============================================================

COPY bot.py /app/bot.py


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

ENV MODEL_PATH=/app/models/MyVoice.pth

ENV INDEX_PATH=/app/models/MyVoice.index

ENV TTS_VOICE=my-MM-ThihaNeural


# ============================================================
# START TELEGRAM BOT
# ============================================================

CMD ["python", "/app/bot.py"]
