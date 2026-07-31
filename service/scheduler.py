from apscheduler.schedulers.background import BackgroundScheduler


def start_scheduler() -> BackgroundScheduler:
    from service.telegram import reminder_job, monthly_recap_job

    scheduler = BackgroundScheduler()
    scheduler.add_job(reminder_job, "interval", hours=2, id="reminder")
    scheduler.add_job(monthly_recap_job, "cron", day=1, hour=9, minute=0, id="monthly_recap")
    scheduler.start()
    return scheduler
