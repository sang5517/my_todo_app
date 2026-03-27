import smtplib
from email.mime.text import MIMEText
import random
import os
def generate_code():
    return str(random.randint(100000, 999999))

def send_email(to_email, code):
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.starttls()
    smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))

    msg = MIMEText(f"인증코드: {code}")
    msg['Subject'] = '회원가입 인증코드'
    msg['From'] = 'sang5517@gmail.com'
    msg['To'] = to_email

    smtp.send_message(msg)
    smtp.quit()