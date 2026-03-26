from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events

scheduler = BackgroundScheduler()
jobstore_added = False  # variable de suivi

def job_send_reminder():
    from appointments.tasks import send_rappel_emails
    send_rappel_emails()

def start():
    global jobstore_added

    if scheduler.state == 1:  # si déjà démarré, ne rien faire
        return

    if not jobstore_added:
        scheduler.add_jobstore(DjangoJobStore(), "default")
        jobstore_added = True

    scheduler.add_job(
        job_send_reminder,
        trigger='cron',
        hour=18,
        minute=0,
        id='job_send_reminder',
        replace_existing=True,
    )

    register_events(scheduler)
    scheduler.start()
