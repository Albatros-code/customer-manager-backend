import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

port = 465  # For SSL
sender_email = os.environ.get('EMAIL_USER')
password = os.environ.get('EMAIL_PASSWORD')


def send_verification_email(receiver_email, email_verification_string):
    message = MIMEMultipart("alternative")
    message["Subject"] = "CustomerApp verification email"
    message["From"] = sender_email
    message["To"] = receiver_email

    text = """\
    Hi,
    please confirm your email.
    """
    html = f"""\
    <html>
    <body>
        <p>Hi,<br>
        please confirm your email.<br>
        <a href="{os.environ.get('FRONTEND_HOST')}/register/{email_verification_string}"><button>Confirm</button></a>
        </p>
    </body>
    </html>
    """

    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=ssl.create_default_context()) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())


def send_reset_password_email(receiver_email: str, reset_password_string: str):
    message = MIMEMultipart("alternative")
    message["Subject"] = "CustomerApp password reset"
    message["From"] = sender_email
    message["To"] = receiver_email

    text = f"""\
    You can reset your password by clicking the link below:
    {os.environ.get('FRONTEND_HOST')}/reset-password?token={reset_password_string}
    """
    html = f"""\
    <html>
    <body>
        <p>Somebody requested a new password for CustomerApp account for {receiver_email}. No changes have been made to your account yet. </p>
        <p>You can reset your password by clicking the button below:</p>
        <p><a href="{os.environ.get('FRONTEND_HOST')}/reset-password?token={reset_password_string}"><button>Reset password</button></a></p>
        <p>If there are any problems, please let us know by replaying to this email.</p>
        <p>CustomerApp team</p>
    </body>
    </html>
    """

    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=ssl.create_default_context()) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

