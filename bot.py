import asyncio
import os
import subprocess
import uuid
from pathlib import Path

import edge_tts
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "/app/models/MyVoice.pth"
)

INDEX_PATH = os.getenv(
    "INDEX_PATH",
    "/app/models/MyVoice.index"
)

TTS_VOICE = os.getenv(
    "TTS_VOICE",
    "my-MM-ThihaNeural"
)

WORK_DIR = Path("/app/work")
WORK_DIR.mkdir(parents=True, exist_ok=True)

RVC_DIR = "/app/RVC"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ 👋\n\n"
        "စာသားပို့ပါ။\n"
        "MyVoice အသံနဲ့ 320kbps MP3 ပြန်ပေးပါမယ်။"
    )


async def text_to_speech(text: str, output_file: str):
    communicate = edge_tts.Communicate(
        text=text,
        voice=TTS_VOICE,
        rate="+0%",
        volume="+0%",
        pitch="+0Hz",
    )

    await communicate.save(output_file)


def convert_to_wav(input_file: str, output_file: str):
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-ar",
        "40000",
        "-ac",
        "1",
        "-sample_fmt",
        "s16",
        output_file,
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "WAV conversion failed:\n\n" + result.stdout
        )


def run_rvc(input_file: str, output_file: str):
    cmd = [
        "python",
        f"{RVC_DIR}/infer/cli.py",

        "--model",
        MODEL_PATH,

        "--input",
        input_file,

        "--output",
        output_file,

        "--index",
        INDEX_PATH,

        "--pitch",
        "0",

        "--f0-method",
        "rmvpe",

        "--index-rate",
        "0.75",

        "--protect",
        "0.33",

        "--overwrite",
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "RVC failed:\n\n" + result.stdout
        )


def convert_to_mp3(input_file: str, output_file: str):
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "320k",
        output_file,
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "MP3 conversion failed:\n\n" + result.stdout
        )


async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if not text:
        return

    if text.startswith("/"):
        return

    job_id = uuid.uuid4().hex

    tts_mp3 = WORK_DIR / f"{job_id}_tts.mp3"
    tts_wav = WORK_DIR / f"{job_id}_tts.wav"
    rvc_wav = WORK_DIR / f"{job_id}_rvc.wav"
    final_mp3 = WORK_DIR / f"{job_id}_MyVoice.mp3"

    try:
        await update.message.chat.send_action(
            action=ChatAction.RECORD_VOICE
        )

        status = await update.message.reply_text(
            "⏳ MyVoice အသံထုတ်နေပါတယ်..."
        )

        # TTS
        await text_to_speech(
            text,
            str(tts_mp3)
        )

        # MP3 -> WAV
        await asyncio.to_thread(
            convert_to_wav,
            str(tts_mp3),
            str(tts_wav)
        )

        # RVC
        await asyncio.to_thread(
            run_rvc,
            str(tts_wav),
            str(rvc_wav)
        )

        # WAV -> 320kbps MP3
        await asyncio.to_thread(
            convert_to_mp3,
            str(rvc_wav),
            str(final_mp3)
        )

        await status.delete()

        with open(final_mp3, "rb") as audio:
            await update.message.reply_audio(
                audio=audio,
                filename="MyVoice.mp3",
                title="MyVoice",
                performer="MyVoice",
            )

    except Exception as e:
        print("ERROR:", e)

        await update.message.reply_text(
            "❌ အသံထုတ်ရာမှာ Error ဖြစ်ပါတယ်။\n\n"
            f"{str(e)[:1500]}"
        )

    finally:
        for file in [
            tts_mp3,
            tts_wav,
            rvc_wav,
            final_mp3,
        ]:
            try:
                file.unlink(missing_ok=True)
            except Exception:
                pass


def main():
    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    print("MyVoice Telegram Bot started.")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
