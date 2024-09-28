import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config

def generate_otp():
    return random.randint(100000, 999999)

def send_otp_email(email, otp):
    senderEmail = config.senderEmail
    senderPwd = config.senderPwd
    
    # Setup SMTP server (e.g., Gmail)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(senderEmail, senderPwd)
    
    # Create the email content
    msg = MIMEMultipart()
    msg['From'] = senderEmail
    msg['To'] = email
    msg['Subject'] = "Password Reset OTP"
    
    body = f"Your OTP for password reset is: {otp}"
    msg.attach(MIMEText(body, 'plain'))
    
    # Send the email
    server.sendmail(senderEmail, email, msg.as_string())
    server.quit()