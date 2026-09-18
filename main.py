import os
import gdown
from core import app

def download_model():
    if not os.path.exists("models"):
        os.makedirs("models")
    
    model_path = "models/my_voice_clone.pth"
    drive_file_id = os.environ.get("MODEL_DRIVE_ID")
    
    if not drive_file_id:
        print("⚠️ MODEL_DRIVE_ID မတွေ့ပါ။")
        return

    if not os.path.exists(model_path):
        print("📥 Google Drive မှ Model အား Download ရယူနေပါသည်...")
        download_url = f"https://drive.google.com/uc?id={drive_file_id}"
        gdown.download(download_url, model_path, quiet=False)
        print("✅ Model Download ရယူခြင်း အောင်မြင်ပါသည်။")
    else:
        print("✅ Model ဖိုင် ရှိပြီးသားဖြစ်ပါသည်။")

if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    download_model()
    
    print("🚀 Bot is starting...")
    app.run()
