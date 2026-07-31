import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()
if not WEBHOOK_URL and os.getenv("RAILWAY_PUBLIC_DOMAIN"):
    WEBHOOK_URL = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN').strip()}/webhook"
elif not WEBHOOK_URL and os.getenv("RENDER_EXTERNAL_URL"):
    WEBHOOK_URL = f"{os.getenv('RENDER_EXTERNAL_URL').rstrip('/')}/webhook"

SECRET_KEY = os.getenv("SECRET_KEY", "doikita-secret-key-ubah")
FLASK_PORT = int(os.getenv("PORT", os.getenv("FLASK_PORT", 5000)))
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

USERS = ["LUIS", "HESTI"]
CATEGORIES = ["bisnis", "pribadi"]
TYPES = ["pemasukan", "pengeluaran"]

APPS_SCRIPT_URL = os.getenv("APPS_SCRIPT_URL", "")
