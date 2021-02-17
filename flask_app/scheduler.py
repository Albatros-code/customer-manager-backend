import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from . import mongoDB as db


def remove_invalid_reset_password_token():
    yesterday = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat()
    db.ResetPassword.objects(date__lt=yesterday).delete()
    print("Removing reset password tokens from database.")


def remove_outdated_access_token():
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db.RevokedToken.objects(expiration_date__lt=now).delete()
    print("Removing outdated access tokens from database.")


scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(remove_invalid_reset_password_token, 'interval', minutes=60)
scheduler.add_job(remove_outdated_access_token, 'interval', hours=12)
# scheduler.start()
