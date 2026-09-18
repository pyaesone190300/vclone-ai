import os
import time
from pyrogram import Client, filters
import edge_tts
from rvc_python.infer import RVCInference

rvc = RVCInference(device="cpu")
model_loaded = False

def load_rvc_model():
    global model_loaded
    model_path = "models/my_voice_clone.pth"
    if os.path.exists(model_path) and not model_loaded:
        rvc.load_model(model_path)
        model_loaded = True

@Client.on_message(filters.text & filters.private)
async def handle_tts(client, message):
    user_text = message.text
    chat_id = message.chat.id
    
    base_audio = f"downloads/base_{chat_id}_{int(time.time())}.wav"
    cloned_audio = f"downloads/cloned_{chat_id}_{int(time.time())}.wav"

    msg = await message.reply_text("⏳ အသံပြောင်းလဲနေပါသည်...")

    try:
        load_rvc_model()
        if not model_loaded:
            await msg.edit_text("❌ Model ဖိုင် မရှိသေးပါ။ System ကို စစ်ဆေးပါ။")
            return

        # မိန်းကလေး TTS အသံဖြင့် ရိုးရိုးအသံဖန်တီးခြင်း
        communicate = edge_tts.Communicate(user_text, "en-US-JennyNeural")
        await communicate.save(base_audio)

        # RVC ဖြင့် မိန်းကလေးအသံသို့ Clone လုပ်ခြင်း (Pitch 0)
        rvc.infer_file(
            input_path=base_audio,
            output_path=cloned_audio,
            f0_up_key=0, 
            f0_method="rmvpe"
        )

        await message.reply_voice(voice=cloned_audio)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ အမှားအယွင်းဖြစ်ပေါ်ခဲ့ပါသည်: {str(e)}")
    
    finally:
        if os.path.exists(base_audio):
            os.remove(base_audio)
        if os.path.exists(cloned_audio):
            os.remove(cloned_audio)
