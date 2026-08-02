import asyncio
import json
import re
import os
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from service.database import get_db, add_transaction, init_saldo_if_not_exists, get_saldo_by_kategori, update_saldo, get_telegram_auth, save_telegram_auth
from config import BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY
from service.sheets import append_transaction

user_data_store = {}
AUTH_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "authorized_users.json")


def _load_auth() -> dict:
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            return get_telegram_auth(get_db())
        except Exception:
            pass
    if not os.path.exists(AUTH_FILE):
        return {}
    try:
        with open(AUTH_FILE) as f:
            data = json.load(f)
        if isinstance(data, list):
            return {}
        return data
    except (json.JSONDecodeError, OSError):
        return {}


def _save_auth(users: dict):
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            save_telegram_auth(get_db(), users)
        except Exception:
            pass
    os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
    with open(AUTH_FILE, "w") as f:
        json.dump(users, f, indent=2)


def is_authorized(update: Update) -> bool:
    user_id = update.effective_user.id
    return str(user_id) in _load_auth()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store.pop(user_id, None)

    auth = _load_auth()
    user_data = auth.get(str(user_id))

    if user_data and user_data.get("mode"):
        mode = user_data["mode"]
        kategori = "pribadi" if mode in ["LUIS", "HESTI"] else "bisnis"
        user_data_store[user_id] = {"mode": mode, "kategori": kategori}

        text, reply_markup = _build_mode_menu(mode)
        await update.message.reply_text(text, reply_markup=reply_markup)
        return

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Luis", callback_data="mode_LUIS")],
        [InlineKeyboardButton("Hesti", callback_data="mode_HESTI")],
        [InlineKeyboardButton("Bisnis", callback_data="mode_bisnis")],
    ])
    await update.message.reply_text(
        "Pilih user:",
        reply_markup=reply_markup,
    )


async def batal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store.pop(user_id, None)
    await update.message.reply_text("Sesi dibatalkan. Ketik /start untuk menu.")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store.pop(user_id, None)
    auth = _load_auth()
    auth.pop(str(user_id), None)
    _save_auth(auth)
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Luis", callback_data="mode_LUIS")],
        [InlineKeyboardButton("Hesti", callback_data="mode_HESTI")],
        [InlineKeyboardButton("Bisnis", callback_data="mode_bisnis")],
    ])
    await update.message.reply_text(
        "Akun direset. Pilih user:",
        reply_markup=reply_markup,
    )


def _build_mode_menu(mode: str) -> tuple[str, InlineKeyboardMarkup]:
    if mode == "LUIS":
        text = "Hai Luis, mau catat apa?"
    elif mode == "HESTI":
        text = "Hai Hestiku sayangkuuu \U0001f618\u2764\ufe0f\U0001f339\U0001f970\U0001f497\U0001f49b, mau catat apa?"
    else:
        text = "Mode Bisnis aktif, mau catat apa?"

    keyboard = [
        [InlineKeyboardButton("Pemasukan", callback_data="tx_pemasukan"),
         InlineKeyboardButton("Pengeluaran", callback_data="tx_pengeluaran")],
    ]
    keyboard.append([InlineKeyboardButton("Ganti User", callback_data="action_ganti_user")])

    return text, InlineKeyboardMarkup(keyboard)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    data = query.data

    if data == "mode_LUIS":
        user_data_store[user_id] = {"mode": "LUIS", "kategori": "pribadi"}
        auth = _load_auth()
        auth[str(user_id)] = {"mode": "LUIS", "chat_id": chat_id}
        _save_auth(auth)
        text, reply_markup = _build_mode_menu("LUIS")
        await query.edit_message_text(text, reply_markup=reply_markup)
    elif data == "mode_HESTI":
        user_data_store[user_id] = {"mode": "HESTI", "kategori": "pribadi"}
        auth = _load_auth()
        auth[str(user_id)] = {"mode": "HESTI", "chat_id": chat_id}
        _save_auth(auth)
        text, reply_markup = _build_mode_menu("HESTI")
        await query.edit_message_text(text, reply_markup=reply_markup)
    elif data == "mode_bisnis":
        user_data_store[user_id] = {"mode": "bisnis", "kategori": "bisnis"}
        auth = _load_auth()
        auth[str(user_id)] = {"mode": "bisnis", "chat_id": chat_id}
        _save_auth(auth)
        text, reply_markup = _build_mode_menu("bisnis")
        await query.edit_message_text(text, reply_markup=reply_markup)
    elif data.startswith("tx_"):
        mode = user_data_store.get(user_id, {}).get("mode", "")
        if data == "tx_pemasukan":
            user_data_store[user_id]["pending_type"] = "pemasukan"
            if mode == "HESTI":
                await query.edit_message_text("Ketik nominal dan deskripsinya sayangkuu \U0001f60a\nContoh: gaji 5000000")
            else:
                await query.edit_message_text("Ketik nominal dan deskripsinya.\nContoh: gaji 5000000")
        elif data == "tx_pengeluaran":
            user_data_store[user_id]["pending_type"] = "pengeluaran"
            if mode == "HESTI":
                await query.edit_message_text("Ketik nominal dan deskripsinya sayangkuu \U0001f60a\nContoh: kopi 10000")
            else:
                await query.edit_message_text("Ketik nominal dan deskripsinya.\nContoh: kopi 10000")
    elif data == "action_ganti_user":
        user_data_store[user_id] = {}
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Luis", callback_data="mode_LUIS")],
            [InlineKeyboardButton("Hesti", callback_data="mode_HESTI")],
            [InlineKeyboardButton("Bisnis", callback_data="mode_bisnis")],
        ])
        await query.edit_message_text("Pilih user:", reply_markup=reply_markup)
    elif data == "method_cash":
        ud = user_data_store.get(user_id, {})
        if "pending" not in ud:
            mk = InlineKeyboardMarkup([
                [InlineKeyboardButton("Ada lagi", callback_data="after_again"),
                 InlineKeyboardButton("Ganti user", callback_data="after_change")]
            ])
            await query.edit_message_text("Tidak ada transaksi pending.", reply_markup=mk)
            return
        msg, reply_markup = _execute_save_transaction(ud, metode="cash")
        await query.edit_message_text(msg, reply_markup=reply_markup)
    elif data == "method_transfer":
        ud = user_data_store.get(user_id, {})
        if "pending" not in ud:
            mk = InlineKeyboardMarkup([
                [InlineKeyboardButton("Ada lagi", callback_data="after_again"),
                 InlineKeyboardButton("Ganti user", callback_data="after_change")]
            ])
            await query.edit_message_text("Tidak ada transaksi pending.", reply_markup=mk)
            return
        msg, reply_markup = _execute_save_transaction(ud, metode="transfer")
        await query.edit_message_text(msg, reply_markup=reply_markup)
    elif data == "method_batal":
        ud = user_data_store.get(user_id, {})
        if "pending" in ud:
            del ud["pending"]
        await query.edit_message_text("Dibatalkan.")
    elif data.startswith("after_"):
        if data == "after_again":
            pass
        elif data == "after_change":
            user_data_store[user_id] = {}
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("Luis", callback_data="mode_LUIS")],
                [InlineKeyboardButton("Hesti", callback_data="mode_HESTI")],
                [InlineKeyboardButton("Bisnis", callback_data="mode_bisnis")],
            ])
            await query.edit_message_text("Pilih user:", reply_markup=reply_markup)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(update):
        await update.message.reply_text("Ketik /start dulu untuk pilih user.")
        return

    data = user_data_store.get(user_id, {})
    if not data.get("mode"):
        await update.message.reply_text("Ketik /start dulu untuk pilih user.")
        return

    file = await update.message.effective_photo[-1].get_file()
    photo_dir = os.path.join(os.path.dirname(__file__), "..", "bill")
    os.makedirs(photo_dir, exist_ok=True)
    fname = f"bill_{user_id}_{int(time.time())}.jpg"
    fpath = os.path.join(photo_dir, fname)
    await file.download_to_drive(fpath)

    user_data_store[user_id] = {**data, "bill_path": fpath}

    mode = data.get("mode", "")
    if mode == "HESTI":
        await update.message.reply_text(
            "Foto struk udah kusimpan sayangkuu \U0001f60a\nSekarang ketik transaksinya ya. Contoh: beli kopi 10000 \U0001f618"
        )
    else:
        await update.message.reply_text(
            "Foto struk diterima. Sekarang ketik transaksinya.\nContoh: beli kopi 10000"
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if not is_authorized(update):
        await update.message.reply_text("Ketik /start dulu untuk pilih user.")
        return

    data = user_data_store.get(user_id, {})

    if "pending" in data:
        await _handle_confirmation(update, user_id, data, text)
        return

    if text.lower() in ["selesai", "back", "menu"]:
        user_data_store.pop(user_id, None)
        await update.message.reply_text("Ketik /start untuk menu utama.")
        return

    if data.get("mode"):
        await _handle_transaction_input(update, user_id, data, text)
        return

    await update.message.reply_text("Ketik /start untuk memilih.")


async def _handle_transaction_input(update: Update, user_id: int, data: dict, text: str):
    t = text.lower().strip()
    mode = data.get("mode", "bisnis")

    if t.startswith("beli "):
        tipe = "pengeluaran"
        raw_desc = text[5:]
    elif t.startswith("tf "):
        tipe = "pengeluaran"
        raw_desc = text[3:]
    elif t.startswith("transfer "):
        tipe = "pengeluaran"
        raw_desc = text[9:]
    elif t.startswith("dapat "):
        tipe = "pemasukan"
        raw_desc = text[6:]
    elif t.startswith("terima "):
        tipe = "pemasukan"
        raw_desc = text[7:]
    elif data.get("pending_type"):
        tipe = data.pop("pending_type")
        raw_desc = text
    else:
        await update.message.reply_text("Gunakan 'beli'/'TF'/'transfer' untuk pengeluaran atau 'dapat'/'terima' untuk pemasukan.")
        return

    angka = re.findall(r"\b\d+\b", t)
    if not angka:
        await update.message.reply_text("Sertakan nominalnya. Contoh: beli kopi 10000")
        return
    amount = int(angka[-1])
    if amount <= 0:
        await update.message.reply_text("Nominal harus lebih dari 0.")
        return

    desc = re.sub(r"\b\d+\b\s*$", "", raw_desc).strip()
    if not desc:
        desc = tipe

    emoji = "\U0001f534" if tipe == "pengeluaran" else "\U0001f7e2"

    tipe_label = "pengeluaran" if tipe == "pengeluaran" else "pemasukan"
    if mode == "HESTI":
        text_confirm = f"{emoji} Sayangku mau catat {tipe_label} Rp{amount:,} ({desc})? Via apa? \U0001f60a"
    else:
        text_confirm = f"Mau catat: {tipe_label} Rp{amount:,} ({desc}) untuk {mode}? Via apa?"

    method_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Cash", callback_data="method_cash"),
         InlineKeyboardButton("Transfer", callback_data="method_transfer")],
        [InlineKeyboardButton("Batal", callback_data="method_batal")],
    ])

    user_data_store[user_id] = {**data, "pending": {"type": tipe, "amount": amount, "description": desc}}
    await update.message.reply_text(text_confirm, reply_markup=method_keyboard)


def _execute_save_transaction(ud: dict, metode: str = "") -> tuple[str, InlineKeyboardMarkup]:
    pending = ud["pending"]
    mode = ud.get("mode", "bisnis")
    kategori = ud.get("kategori", "bisnis")

    owner = mode if mode in ["LUIS", "HESTI"] else None
    if mode == "bisnis":
        kategori_saldo = "bisnis"
    elif mode == "LUIS":
        kategori_saldo = "pribadi_LUIS"
    else:
        kategori_saldo = "pribadi_HESTI"

    db = get_db()
    init_saldo_if_not_exists(db)
    try:
        add_transaction(
            db,
            user=mode if mode in ["LUIS", "HESTI"] else owner or "LUIS",
            ttype=pending["type"],
            category=kategori,
            amount=pending["amount"],
            description=pending["description"],
            owner_pribadi=owner,
        )
    except Exception:
        pass

    nominal = pending["amount"] if pending["type"] == "pemasukan" else -pending["amount"]
    update_saldo(db, kategori_saldo, nominal)
    saldo_baru = get_saldo_by_kategori(db, kategori_saldo)
    label = kategori_saldo.replace("_", " ").title()

    del ud["pending"]

    saldo_sheets = None
    try:
        saldo_sheets = append_transaction({
            "tanggal": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "user": mode.upper(),
            "type": pending["type"],
            "description": pending["description"],
            "amount": pending["amount"],
            "metode": metode,
        })
    except Exception:
        pass

    if mode == "bisnis":
        saldo_tampil = saldo_sheets if saldo_sheets is not None else saldo_baru
        msg = f"Tersimpan! Saldo {label}: Rp {saldo_tampil:,}"
    elif mode == "HESTI":
        msg = "Sudah tersimpan sayangkuuu \U0001f497\U0001f497 \U0001f618\U0001f970"
    else:
        msg = "Tersimpan!"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Ada lagi", callback_data="after_again"),
         InlineKeyboardButton("Ganti user", callback_data="after_change")]
    ])
    return msg, reply_markup


async def _handle_confirmation(update: Update, user_id: int, data: dict, text: str):
    t = text.lower().strip()
    if t == "ya":
        msg, reply_markup = _execute_save_transaction(data, metode="")
        await update.message.reply_text(msg, reply_markup=reply_markup)
    elif t == "tidak":
        del data["pending"]
        await update.message.reply_text("Dibatalkan.")
    elif t in ["selesai", "back", "menu"]:
        user_data_store.pop(user_id, None)
        await update.message.reply_text("Ketik /start untuk menu utama.")
    else:
        await update.message.reply_text("Klik Cash, Transfer, atau Batal di atas.")


async def _send_reminder():
    auth = _load_auth()
    if not auth:
        return
    app = get_application()
    for uid_str, data in auth.items():
        chat_id = data.get("chat_id", int(uid_str))
        mode = data.get("mode", "")
        try:
            if mode == "HESTI":
                text = "Jangan lupa catat transaksi Doikita hari ini ya sayangkuu \U0001f60a\nKetik beli atau dapat ya \U0001f618"
            else:
                text = "Jangan lupa catat transaksi Doikita hari ini!\nKetik beli atau dapat ya."
            await app.bot.send_message(chat_id=chat_id, text=text)
        except Exception:
            pass


async def _send_monthly_recap():
    from datetime import datetime
    from service.rekapan import generate_rekapan_pdf
    from service.database import get_transactions_by_month, get_saldo_by_kategori

    now = datetime.now()
    bulan = now.month - 1
    tahun = now.year
    if bulan == 0:
        bulan = 12
        tahun -= 1

    auth = _load_auth()
    if not auth:
        return
    app = get_application()

    for uid_str, data in auth.items():
        mode = data.get("mode")
        if mode not in ("LUIS", "HESTI"):
            continue
        chat_id = data.get("chat_id", int(uid_str))
        try:
            db = get_db()
            kategori = "pribadi_LUIS" if mode == "LUIS" else "pribadi_HESTI"
            transactions = get_transactions_by_month(db, bulan, tahun, user=mode)
            saldo_bisnis = get_saldo_by_kategori(db, "bisnis")
            saldo_pribadi = get_saldo_by_kategori(db, kategori)
            saldo_akhir = saldo_bisnis + saldo_pribadi

            pdf_path = generate_rekapan_pdf(transactions, mode, bulan, tahun, saldo_akhir)

            with open(pdf_path, "rb") as f:
                await app.bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    filename=f"rekapan_{mode}_{tahun}_{bulan:02d}.pdf",
                    caption=f"Rekapan bulan {bulan}/{tahun}"
                )
        except Exception:
            pass


def reminder_job():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_send_reminder())
    finally:
        loop.close()


def monthly_recap_job():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_send_monthly_recap())
    finally:
        loop.close()


def _build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("batal", batal))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return app


_application = None


def get_application() -> Application:
    global _application
    if _application is None:
        _application = _build_app()
    return _application


async def set_webhook(webhook_url: str):
    app = get_application()
    await app.bot.set_webhook(url=webhook_url)
    print(f"Webhook set to {webhook_url}")


def setup_webhook_app(flask_app, webhook_url: str):
    import asyncio
    from flask import request

    if not webhook_url.rstrip("/").endswith("/webhook"):
        webhook_url = webhook_url.rstrip("/") + "/webhook"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(set_webhook(webhook_url))

    @flask_app.route("/webhook", methods=["POST"])
    def webhook():
        import json
        app = get_application()
        update = Update.de_json(json.loads(request.data), app.bot)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(app.process_update(update))
        return "OK", 200

    print("Bot running via webhook...")


def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        app = _build_app()
        print("Telegram bot started (polling)...")
        app.run_polling(close_loop=False)
    except KeyboardInterrupt:
        pass
