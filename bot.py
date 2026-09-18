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


# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]


MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "/app/models/MyVoice.pth"
)


INDEX_PATH = os.getenv(
    "INDEX_PATH",
    "/app/models/MyVoice.index"
)


# ============================================================
# BURMESE TTS
# ============================================================

TTS_VOICE = os.getenv(
    "TTS_VOICE",
    "my-MM-ThihaNeural"
)


# ============================================================
# RVC DIRECTORY
# ============================================================

RVC_DIR = "/app/RVC"


# ============================================================
# WORK DIRECTORY
# ============================================================

WORK_DIR = Path("/app/work")

WORK_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# RVC SETTINGS
# ============================================================

# ------------------------------------------------------------
# Pitch
# ------------------------------------------------------------
# +8 = female direction
#
# +12 can make the voice female but may move too far
# away from the original trained MyVoice character.
#
# If +8 is still too masculine:
#     try 10
#
# If +8 sounds too high:
#     try 6
# ------------------------------------------------------------

PITCH = 8


# ------------------------------------------------------------
# F0 extraction
# ------------------------------------------------------------

F0_METHOD = "rmvpe"


# ------------------------------------------------------------
# Index influence
# ------------------------------------------------------------
#
# Higher:
#   More influence from MyVoice.index
#
# Lower:
#   More natural source characteristics
#
# 0.75 is a good starting point.
# ------------------------------------------------------------

INDEX_RATE = 0.75


# ------------------------------------------------------------
# Protect
# ------------------------------------------------------------
#
# Helps protect consonants / pronunciation.
#
# 0.33 = balanced
# ------------------------------------------------------------

PROTECT = 0.33


# ------------------------------------------------------------
# Speaker ID
# ------------------------------------------------------------

SPEAKER_ID = 0


# ============================================================
# /start
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "မင်္ဂလာပါ 👋\n\n"

        "မြန်မာစာသားပို့ပါ။\n\n"

        "MyVoice မိန်းကလေးအသံနဲ့\n"
        "320kbps MP3 ပြန်ပေးပါမယ်။"

    )


# ============================================================
# TEXT -> EDGE TTS
# ============================================================

async def text_to_speech(
    text: str,
    output_file: str
):

    communicate = edge_tts.Communicate(

        text=text,

        voice=TTS_VOICE,

        rate="+0%",

        volume="+0%",

        pitch="+0Hz",

    )


    await communicate.save(
        output_file
    )


# ============================================================
# MP3 -> WAV
# ============================================================

def convert_to_wav(
    input_file: str,
    output_file: str
):

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

            "WAV conversion failed:\n\n"
            + result.stdout

        )


# ============================================================
# RVC INFERENCE
# ============================================================

def run_rvc(
    input_file: str,
    output_file: str
):

    env = os.environ.copy()


    # --------------------------------------------------------
    # Make sure RVC can find infer module
    # --------------------------------------------------------

    env["PYTHONPATH"] = RVC_DIR


    cmd = [

        "python",

        "/app/RVC/infer/cli.py",


        # ----------------------------------------------------
        # MODEL
        # ----------------------------------------------------

        "--model",
        MODEL_PATH,


        # ----------------------------------------------------
        # INPUT
        # ----------------------------------------------------

        "--input",
        input_file,


        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        "--output",
        output_file,


        # ----------------------------------------------------
        # INDEX
        # ----------------------------------------------------

        "--index",
        INDEX_PATH,


        # ----------------------------------------------------
        # PITCH
        # ----------------------------------------------------

        "--pitch",
        str(PITCH),


        # ----------------------------------------------------
        # F0 METHOD
        # ----------------------------------------------------

        "--f0-method",
        F0_METHOD,


        # ----------------------------------------------------
        # INDEX RATE
        # ----------------------------------------------------

        "--index-rate",
        str(INDEX_RATE),


        # ----------------------------------------------------
        # PROTECT
        # ----------------------------------------------------

        "--protect",
        str(PROTECT),


        # ----------------------------------------------------
        # SPEAKER
        # ----------------------------------------------------

        "--speaker-id",
        str(SPEAKER_ID),


        # ----------------------------------------------------
        # OVERWRITE
        # ----------------------------------------------------

        "--overwrite",

    ]


    # ========================================================
    # PRINT SETTINGS
    # ========================================================

    print("")
    print("========================================")
    print("RVC SETTINGS")
    print("========================================")

    print(
        f"Model       : {MODEL_PATH}"
    )

    print(
        f"Index       : {INDEX_PATH}"
    )

    print(
        f"Pitch       : +{PITCH}"
    )

    print(
        f"F0 method   : {F0_METHOD}"
    )

    print(
        f"Index rate  : {INDEX_RATE}"
    )

    print(
        f"Protect     : {PROTECT}"
    )

    print(
        f"Speaker ID  : {SPEAKER_ID}"
    )

    print("========================================")
    print("")


    # ========================================================
    # RUN RVC
    # ========================================================

    result = subprocess.run(

        cmd,

        stdout=subprocess.PIPE,

        stderr=subprocess.STDOUT,

        text=True,

        cwd=RVC_DIR,

        env=env,

    )


    # ========================================================
    # PRINT RVC OUTPUT
    # ========================================================

    print("")
    print("========== RVC OUTPUT ==========")

    print(
        result.stdout
    )

    print(
        "================================"
    )
    print("")


    # ========================================================
    # ERROR
    # ========================================================

    if result.returncode != 0:

        raise RuntimeError(

            "RVC failed:\n\n"
            + result.stdout

        )


# ============================================================
# WAV -> 320kbps MP3
# ============================================================

def convert_to_mp3(
    input_file: str,
    output_file: str
):

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

            "MP3 conversion failed:\n\n"
            + result.stdout

        )


# ============================================================
# TEXT MESSAGE HANDLER
# ============================================================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    # --------------------------------------------------------
    # Validate message
    # --------------------------------------------------------

    if not update.message:
        return


    if not update.message.text:
        return


    text = update.message.text.strip()


    if not text:
        return


    # --------------------------------------------------------
    # Ignore commands
    # --------------------------------------------------------

    if text.startswith("/"):
        return


    # --------------------------------------------------------
    # Unique Job ID
    # --------------------------------------------------------

    job_id = uuid.uuid4().hex


    # --------------------------------------------------------
    # Temporary files
    # --------------------------------------------------------

    tts_mp3 = (

        WORK_DIR
        /
        f"{job_id}_tts.mp3"

    )


    tts_wav = (

        WORK_DIR
        /
        f"{job_id}_tts.wav"

    )


    rvc_wav = (

        WORK_DIR
        /
        f"{job_id}_rvc.wav"

    )


    final_mp3 = (

        WORK_DIR
        /
        f"{job_id}_MyVoice.mp3"

    )


    status = None


    try:

        # ====================================================
        # RECORDING INDICATOR
        # ====================================================

        await update.message.chat.send_action(

            action=ChatAction.RECORD_VOICE

        )


        # ====================================================
        # STATUS MESSAGE
        # ====================================================

        status = await update.message.reply_text(

            "⏳ MyVoice အသံထုတ်နေပါတယ်..."

        )


        # ====================================================
        # 1. BURMESE TEXT -> EDGE TTS
        # ====================================================

        await text_to_speech(

            text,

            str(tts_mp3)

        )


        # ====================================================
        # 2. TTS MP3 -> WAV
        # ====================================================

        await asyncio.to_thread(

            convert_to_wav,

            str(tts_mp3),

            str(tts_wav),

        )


        # ====================================================
        # 3. WAV -> RVC MyVoice
        # ====================================================

        await asyncio.to_thread(

            run_rvc,

            str(tts_wav),

            str(rvc_wav),

        )


        # ====================================================
        # 4. RVC WAV -> 320kbps MP3
        # ====================================================

        await asyncio.to_thread(

            convert_to_mp3,

            str(rvc_wav),

            str(final_mp3),

        )


        # ====================================================
        # DELETE STATUS
        # ====================================================

        if status:

            try:

                await status.delete()

            except Exception:

                pass


        # ====================================================
        # SEND MP3
        # ====================================================

        with open(

            final_mp3,

            "rb"

        ) as audio:

            await update.message.reply_audio(

                audio=audio,

                filename="MyVoice.mp3",

                title="MyVoice",

                performer="MyVoice",

            )


    except Exception as e:

        # ====================================================
        # ERROR LOG
        # ====================================================

        print("")
        print("================================")
        print("BOT ERROR")
        print("================================")

        print(
            str(e)
        )

        print("================================")
        print("")


        # ====================================================
        # DELETE STATUS
        # ====================================================

        if status:

            try:

                await status.delete()

            except Exception:

                pass


        # ====================================================
        # SEND ERROR
        # ====================================================

        await update.message.reply_text(

            "❌ အသံထုတ်ရာမှာ Error ဖြစ်ပါတယ်။\n\n"

            f"{str(e)[:2000]}"

        )


    finally:

        # ====================================================
        # CLEANUP
        # ====================================================

        for file in [

            tts_mp3,

            tts_wav,

            rvc_wav,

            final_mp3,

        ]:

            try:

                file.unlink(
                    missing_ok=True
                )

            except Exception:

                pass


# ============================================================
# MAIN
# ============================================================

def main():

    # ========================================================
    # CREATE TELEGRAM APP
    # ========================================================

    app = (

        Application

        .builder()

        .token(BOT_TOKEN)

        .build()

    )


    # ========================================================
    # /start
    # ========================================================

    app.add_handler(

        CommandHandler(

            "start",

            start

        )

    )


    # ========================================================
    # TEXT MESSAGE
    # ========================================================

    app.add_handler(

        MessageHandler(

            filters.TEXT

            &

            ~filters.COMMAND,

            text_handler

        )

    )


    # ========================================================
    # START LOG
    # ========================================================

    print("")
    print("========================================")

    print(
        "MyVoice Telegram Bot started."
    )

    print(
        f"Model      : {MODEL_PATH}"
    )

    print(
        f"Index      : {INDEX_PATH}"
    )

    print(
        f"TTS        : {TTS_VOICE}"
    )

    print(
        f"Pitch      : +{PITCH}"
    )

    print(
        f"F0         : {F0_METHOD}"
    )

    print(
        f"Index Rate : {INDEX_RATE}"
    )

    print(
        f"Protect    : {PROTECT}"
    )

    print(
        "Output     : 320kbps MP3"
    )

    print("========================================")
    print("")


    # ========================================================
    # POLLING
    # ========================================================

    app.run_polling(

        drop_pending_updates=True

    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
