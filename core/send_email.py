import os
import smtplib
from datetime import datetime

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

from schemas.leads import LeadCreate


SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
PASSWORD = os.getenv("PASSWORD")


def send_email_notification(lead_data: LeadCreate):
    subject = f"Новая заявка: {lead_data.subject} от {lead_data.name}"

    body = f"""\
Получена новая заявка!

Имя:     {lead_data.name}
Email:   {lead_data.email}
Телефон: {lead_data.phone or "—"}
Тема:    {lead_data.subject}
Дата:    {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Сообщение:
{lead_data.message or "[сообщение отсутствует]"}

---
Система уведомлений
"""

    msg = MIMEMultipart()
    msg["From"] = formataddr(("Система заявок", EMAIL_FROM))
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_FROM, PASSWORD)
            server.send_message(msg)
        print(f"[EMAIL] Уведомление о заявке '{lead_data.subject}' отправлено")
    except Exception as e:
        print(f"[EMAIL ERROR] Не удалось отправить уведомление: {e}")
