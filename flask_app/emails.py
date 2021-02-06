import smtplib, ssl, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv
load_dotenv()

port = 465  # For SSL
sender_email = os.environ.get('EMAIL_USER')
password = os.environ.get('EMAIL_PASSWORD')
receiver_email = sender_email



# Create a secure SSL context
# context = ssl.create_default_context()

# with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
#     server.login(sender_email, password)
#     server.sendmail(sender_email, receiver_email, message.as_string())


def send_verification_email(receiver_email, userID, verification_string):
    
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
        <a href="{os.environ.get('BACKEND_HOST')}/user/{userID}/{verification_string}"><button>Confirm</button></a>
        </p>
    </body>
    </html>
    """


    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=ssl.create_default_context()) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

send_verification_email(receiver_email, '5ffb420d4a0f7e9caf30e0d0', 'noElo')