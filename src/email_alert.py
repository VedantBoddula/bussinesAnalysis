import smtplib
from email.message import EmailMessage


def send_email_alert(sender_email, app_password, receiver_email, subject, body):

    message = EmailMessage()

    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, app_password)
        smtp.send_message(message)

    print("Email alert sent successfully!")