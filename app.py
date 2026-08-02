from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
from datetime import datetime
import threading
import os

from config import SECRET_KEY, FLASK_PORT, FLASK_HOST, FLASK_DEBUG, USERS, WEBHOOK_URL
from service.database import get_db, init_saldo_if_not_exists, get_saldo_dashboard, get_transactions, get_transactions_by_month, add_rekapan, update_saldo, get_saldo_by_kategori
from service.rekapan import generate_rekapan_pdf

app = Flask(__name__)
app.secret_key = SECRET_KEY

if WEBHOOK_URL:
    from service.telegram import setup_webhook_app
    setup_webhook_app(app, WEBHOOK_URL)
    print("Bot mode: webhook")


from service.scheduler import start_scheduler

_scheduler = start_scheduler()


def _keepalive_url() -> str:
    if not WEBHOOK_URL:
        return None
    base = WEBHOOK_URL.rstrip("/")
    if base.endswith("/webhook"):
        base = base[: -len("/webhook")]
    return base + "/health"


def _keepalive_loop():
    import time
    import urllib.request

    url = _keepalive_url()
    while True:
        time.sleep(300)
        try:
            urllib.request.urlopen(url, timeout=10).read()
        except Exception:
            pass


def start_keepalive():
    if not _keepalive_url():
        return
    threading.Thread(target=_keepalive_loop, daemon=True).start()


start_keepalive()


@app.before_request
def before_request():
    if request.endpoint and request.endpoint not in ("login", "webhook", "health") and not session.get("user"):
        return redirect(url_for("login"))


@app.route("/health")
def health():
    return "OK"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("user")
        if user in USERS:
            session["user"] = user
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Pilih user valid.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def dashboard():
    user = session.get("user")
    db = get_db()
    init_saldo_if_not_exists(db)
    saldo = get_saldo_dashboard(db, user)
    transactions = get_transactions(db, limit=20, user=user)
    return render_template("dashboard.html", user=user, saldo=saldo, transactions=transactions)


@app.route("/api/transactions", methods=["GET"])
def api_transactions():
    db = get_db()
    user = request.args.get("user")
    limit = request.args.get("limit", 50, type=int)
    transactions = get_transactions(db, limit=limit, user=user)
    return jsonify(transactions)


@app.route("/rekapan/pdf")
def rekapan_pdf():
    user = session.get("user")
    bulan = request.args.get("bulan", datetime.now().month, type=int)
    tahun = request.args.get("tahun", datetime.now().year, type=int)

    db = get_db()
    transactions = get_transactions_by_month(db, bulan, tahun, user=user)

    kategori = "pribadi_LUIS" if user == "LUIS" else "pribadi_HESTI"
    saldo_bisnis = get_saldo_by_kategori(db, "bisnis")
    saldo_pribadi = get_saldo_by_kategori(db, kategori)
    saldo_akhir = saldo_bisnis + saldo_pribadi

    pdf_path = generate_rekapan_pdf(transactions, user, bulan, tahun, saldo_akhir)

    add_rekapan(db, bulan, tahun, user, sum(t["amount"] for t in transactions if t["type"] == "pemasukan"), sum(t["amount"] for t in transactions if t["type"] == "pengeluaran"), saldo_akhir, pdf_link=pdf_path)

    return send_file(pdf_path, as_attachment=True, download_name=f"rekapan_{user}_{tahun}_{bulan:02d}.pdf")


@app.route("/api/saldo", methods=["GET"])
def api_saldo():
    db = get_db()
    init_saldo_if_not_exists(db)
    user = session.get("user")
    saldo = get_saldo_dashboard(db, user)
    return jsonify(saldo)


@app.route("/api/add", methods=["POST"])
def api_add_transaction():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user = data.get("user", session.get("user"))
    ttype = data.get("type")
    category = data.get("category")
    amount = data.get("amount", type=int)
    description = data.get("description", "")

    if not all([user, ttype, category, amount]):
        return jsonify({"error": "Missing fields"}), 400

    owner_pribadi = data.get("owner_pribadi")
    if category == "bisnis":
        owner_pribadi = None

    db = get_db()
    from service.database import add_transaction as db_add_tx
    db_add_tx(db, user, ttype, category, amount, description, owner_pribadi)

    if category == "bisnis":
        kategori_saldo = "bisnis"
    elif owner_pribadi == "LUIS":
        kategori_saldo = "pribadi_LUIS"
    else:
        kategori_saldo = "pribadi_HESTI"

    nominal = amount if ttype == "pemasukan" else -amount
    update_saldo(db, kategori_saldo, nominal)

    return jsonify({"status": "ok"}), 201


def start_bot():
    from service.telegram import run_bot
    run_bot()


if __name__ == "__main__":
    if not WEBHOOK_URL:
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()

    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, use_reloader=False, threaded=True)
