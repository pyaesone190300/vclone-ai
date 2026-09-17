import os
import asyncio
import torch
import librosa
import soundfile as sf
from gtts import gTTS
from pyrogram import Client, filters
from pyrogram.types import Message

# Render Environment Variables မှ ရယူခြင်း
API_ID = int(os.environ.get("API_ID", 12345678))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client("myanmar_voice_clone_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_voices = {}

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "👋 **မင်္ဂလာပါ။ မြန်မာစာ Voice Cloning Bot မှ ကြိုဆိုပါတယ်။**\n\n"
        "၁။ Clone လုပ်ချင်သော **အသံဖိုင် (Voice Note/MP3)** ကို ပို့ပေးပါ။\n"
        "၂။ ထို့နောက် ပြောစေချင်သည့် **မြန်မာစာ** ကို ရိုက်ပို့ပေးပါ။"
    )

@app.on_message((filters.voice | filters.audio) & filters.private)
async def handle_audio(client: Client, message: Message):
    status_msg = await message.reply_text("📥 အသံဖိုင်ကို ပြင်ဆင်နေပါသည်...")
    
    user_id = message.from_user.id
    ref_file_path = f"ref_{user_id}.wav"
    
    if os.path.exists(ref_file_path):
        os.remove(ref_file_path)

    downloaded_file = await message.download(file_name=ref_file_path)
    
    y, sr = librosa.load(downloaded_file, sr=16000)
    sf.write(ref_file_path, y, sr)
    
    user_voices[user_id] = ref_file_path
    await status_msg.edit_text("✅ **အသံဖိုင် မှတ်သားပြီးပါပြီ!** ယခု မြန်မာစာ ရိုက်ပို့နိုင်ပါပြီ။")

def convert_voice(base_myanmar_audio: str, reference_audio: str, output_path: str):
    y_base, sr = librosa.load(base_myanmar_audio, sr=16000)
    y_ref, _ = librosa.load(reference_audio, sr=16000)
    
    pitch_ref = librosa.feature.chroma_stft(y=y_ref, sr=sr)
    pitch_base = librosa.feature.chroma_stft(y=y_base, sr=sr)
    
    n_steps = float((pitch_ref.mean() - pitch_base.mean()) * 10)
    y_shifted = librosa.effects.pitch_shift(y=y_base, sr=sr, n_steps=n_steps)
    sf.write(output_path, y_shifted, sr)

@app.on_message(filters.text & filters.private)
async def process_myanmar_tts(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in user_voices or not os.path.exists(user_voices[user_id]):
        await message.reply_text("⚠️ ကျေးဇူးပြု၍ စာမပို့မီ အသံဖိုင်ကို အရင် ပို့ပေးပါ။")
        return

    status_msg = await message.reply_text("⏳ Voice Clone ပြုလုပ်နေပါသည်...")
    text_input = message.text
    ref_audio = user_voices[user_id]
    
    temp_base_audio = f"base_{user_id}.mp3"
    output_audio = f"voice_{user_id}_{message.id}.wav"

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: gTTS(text=text_input, lang='my', slow=False).save(temp_base_audio))
        await loop.run_in_executor(None, lambda: convert_voice(temp_base_audio, ref_audio, output_audio))

        await message.reply_voice(voice=output_audio, caption=f"🗣 **Text:** {text_input[:50]}...")
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

    finally:
        for temp_file in [temp_base_audio, output_audio]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

if __name__ == "__main__":
    print("Render Web Service/Worker - Bot Started")
    app.run()
