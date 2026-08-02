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

## Hosting (Render)

On Render the bot runs as a webhook service (see `render.yaml`). `WEBHOOK_URL` is derived
automatically from `RENDER_EXTERNAL_URL`, so no manual env var is needed.

### Why the bot sometimes goes offline (and the fix)

- **Render free tier spins down after 15 minutes of inactivity**, so `/webhook` is unreachable
  while sleeping and Telegram messages get dropped.
  → **Keep it awake**: the repo includes two keep-alive mechanisms:
    1. **Self-pinger** in `app.py` (GET `/health` every 5 minutes while deployed).
    2. **GitHub Actions workflow** `.github/workflows/keepalive.yml` (cron every 5 minutes).
       ⚠️ Edit that file and replace `<your-app-name>` with your real Render app name
       (e.g. `doikita`) so it becomes `https://doikita.onrender.com/health`.
       Optionally also create a free UptimeRobot monitor as a backup.
- **Authorized Telegram users used to be stored in a local file** (`data/authorized_users.json`)
  that resets on every restart on Render. It now lives in the Supabase `telegram_auth` table
  (columns `user_id`, `username`, `mode`, `chat_id`) so users stay authorized across restarts.
  Run `migrations/004_telegram_auth_extend.sql` in the Supabase SQL Editor if you already ran
  migration 002 before.
- **Run only ONE deployment at a time.** If the bot also runs on a local PC
  (`run_worker.ps1` / `worker.py`, polling mode), it conflicts with the Render webhook
  (Telegram returns `409 Conflict`). Use the PC only for development.

### Supabase setup

Create tables by running the SQL files in `migrations/` inside the Supabase SQL Editor
(`001_initial.sql`, `002_telegram_auth.sql`, `004_telegram_auth_extend.sql`).

To configure, set these environment variables in **Settings → Variables and secrets**:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `BOT_TOKEN`
- `SECRET_KEY`
- `APPS_SCRIPT_URL`
- `WEBHOOK_URL=https://<hf-username>-doikita.hf.space/webhook` (only if not on Render/Railway)

## Check webhook status

```bash
python check_webhook.py   # set BOT_TOKEN first; shows getWebhookInfo result
```
