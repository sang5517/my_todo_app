import smtplib
from email.mime.text import MIMEText
import random
import os
def generate_code():
    return str(random.randint(100000, 999999))

def send_email(to_email, code, purpose):
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.starttls()
    smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))

    if purpose == "register":
        subject = "회원가입 인증코드"
        content = f"[회원가입] 인증코드: {code}"

    elif purpose == "reset":
        subject = "비밀번호 재설정 인증코드"
        content = f"[비밀번호 찾기] 인증코드: {code}"

    else:
        subject = "인증코드"
        content = f"코드: {code}"

    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = os.getenv("EMAIL_USER")
    msg['To'] = to_email

    smtp.send_message(msg)
    smtp.quit()