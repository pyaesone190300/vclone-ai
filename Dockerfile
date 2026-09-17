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
# PYTHON PACKAGE INDEX FIX
# ============================================================

RUN sed -i \
    's#https://mirrors.pku.edu.cn/pypi/simple#https://pypi.org/simple#g' \
    requirments_cpu_py312.txt

RUN sed -i \
    's#https://mirrors.nju.edu.cn/pytorch/whl/cpu#https://download.pytorch.org/whl/cpu#g' \
    requirments_cpu_py312.txt


# ============================================================
# PYTHON / PIP
# ============================================================

RUN python -m pip install --upgrade \
    pip \
    setuptools \
    wheel


# ============================================================
# INSTALL RVC DEPENDENCIES
# ============================================================

RUN python -m pip install \
    -r requirments_cpu_py312.txt


# ============================================================
# HUGGING FACE DOWNLOAD TOOL
# ============================================================

RUN python -m pip install \
    --upgrade \
    huggingface_hub


# ============================================================
# DOWNLOAD RVC HU BERT MODEL
#
# Required by:
# /app/RVC/assets/hubert_base
# ============================================================

RUN mkdir -p /app/RVC/assets

RUN hf download \
    lj1995/VoiceConversionWebUI \
    --revision main \
    --include "hubert_base/*" \
    --local-dir /app/RVC/assets


# ============================================================
# DOWNLOAD RMVPE MODEL
#
# Required by:
# /app/RVC/assets/rmvpe/rmvpe.pt
# ============================================================

RUN mkdir -p /app/RVC/assets/rmvpe

RUN hf download \
    lj1995/VoiceConversionWebUI \
    rmvpe.pt \
    --revision main \
    --local-dir /app/RVC/assets/rmvpe


# ============================================================
# VERIFY HU BERT
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
#
# Render provides these as build arguments.
# ============================================================

ARG MODEL_FILE_ID
ARG INDEX_FILE_ID


# ============================================================
# DOWNLOAD MyVoice.pth
# ============================================================

RUN if [ -n "$MODEL_FILE_ID" ]; then \
        echo "Downloading MyVoice.pth..." && \
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
        echo "Downloading MyVoice.index..." && \
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
# SHOW MODEL FILES
# ============================================================

RUN ls -lh /app/models/

RUN ls -lh /app/RVC/assets/hubert_base/

RUN ls -lh /app/RVC/assets/rmvpe/


# ============================================================
# COPY TELEGRAM BOT
# ============================================================

COPY bot.py /app/bot.py


# ============================================================
# ENVIRONMENT
# ============================================================

ENV MODEL_PATH=/app/models/MyVoice.pth

ENV INDEX_PATH=/app/models/MyVoice.index

ENV TTS_VOICE=my-MM-ThihaNeural


# ============================================================
# START BOT
# ============================================================

CMD ["python", "/app/bot.py"]
