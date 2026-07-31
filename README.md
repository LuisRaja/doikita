---
title: Doikita
emoji: 💰
colorFrom: green
colorTo: blue
sdk: gradio
app_file: app.py
pinned: false
---

# Doikita

Personal finance tracker with Telegram bot. Runs Flask + webhook for the Telegram bot, stores data in Supabase.

To configure, set these environment variables in **Settings → Variables and secrets**:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `BOT_TOKEN`
- `SECRET_KEY`
- `APPS_SCRIPT_URL`
- `WEBHOOK_URL=https://<hf-username>-doikita.hf.space/webhook`
