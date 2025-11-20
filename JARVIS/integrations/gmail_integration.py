import imaplib
import email
from email.header import decode_header
from typing import List, Dict
import smtplib
from email.mime.text import MIMEText
from config.loader import settings
class GmailIMAP:
    def __init__(self, email_addr: str, app_password: str):
        self.email = email_addr
        self.password = app_password
        self.imap = None
        self.smtp = None

    def connect(self):
        self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
        self.imap.login(self.email, self.password)
        self.imap.select("INBOX")
        self.smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        self.smtp.login(self.email, self.password)

    def get_unread_count(self) -> int:
        if not self.imap: self.connect()
        status, data = self.imap.search(None, "UNSEEN")
        return len(data[0].split())

    def get_recent_emails(self, count: int = 10) -> List[Dict]:
        if not self.imap: self.connect()
        status, data = self.imap.search(None, "ALL")
        ids = data[0].split()[-count:][::-1]
        emails = []
        for mid in ids:
            status, msg_data = self.imap.fetch(mid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes): subject = subject.decode()
            emails.append({
                "from": msg["From"],
                "subject": subject,
                "date": msg["Date"]
            })
        return emails

    def send_email(self, to: str, subject: str, body: str):
        if not self.smtp: self.connect()
        msg = MIMEText(body)
        msg["From"] = self.email
        msg["To"] = to
        msg["Subject"] = subject
        self.smtp.send_message(msg)

if __name__ == "__main__":
    EMAIL = settings.your_email_address         # ← change
    APP_PASS = settings.google_app_password  # ← change

    gmail = GmailIMAP(EMAIL, APP_PASS)
    print("Unread:", gmail.get_unread_count())
    print("Recent emails:")
    for e in gmail.get_recent_emails(5):
        print(f"{e['date']} | {e['from']} | {e['subject']}")

    # Test send (uncomment to try):
    gmail.send_email("example@gmail.com", "Test", "Hello from IMAP script")