import re
import base64
import json
import smtplib
from django.conf import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import logging

_logger = logging.getLogger(__name__)

supportemail = settings.GROWTH_VALUE_SUPPORT

def encode_base64(params={}):
    json_str = json.dumps(params)
    byte_data = json_str.encode('utf-8')
    base64_bytes = base64.b64encode(byte_data)
    base64_string = base64_bytes.decode('utf-8')
    return base64_string


def decode_base64(base64_string=""):
    base64_bytes = base64_string.encode('utf-8')
    byte_data = base64.b64decode(base64_bytes)
    data = byte_data.decode('utf-8')
    return json.loads(data)


def validate_password(password):

    pattern = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'
    if not re.match(pattern, password):
        return "Password must be at least 8 characters long and contain both letters and numbers."
    return True


def send_welcome_email(user_name="", email_to="", email_subject=""):
    # Email configuration
    subject = email_subject or 'Welcome to Growth Value - Your Journey to Find the Best Deals Starts Here!🐾'
    # Email content
    html_content = f"""
    <html>
    <body style="margin: 20px">
        <p>Hi <strong>{user_name}</strong>,</p>
        <p>Welcome to <strong>Growth Value</strong>!</p>
        <p>We're thrilled to have you join our community of savvy shoppers who are eager to find, compare, and purchase items from the best suppliers.<br/> Your decision to register with us marks the beginning of a new, hassle-free shopping experience tailored just for you.</p>
        <h4>Here's what you can expect:</h4>
        <ul>
            <li><b>Wide Selection of Products:</b> Discover a vast range of items from trusted suppliers all in one place.</li>
            <li><b>Easy Comparisons:</b> Effortlessly compare products, prices, and reviews to make the best purchasing decisions.</li>
            <li><b>Exclusive Deals:</b> Get access to special offers and discounts available only to our members.</li>
            <li><b>Personalized Recommendations:</b> Receive suggestions based on your preferences and shopping history.</li>
        </ul>
        <p>Our support team is here to help! If you have any questions or need any assistance, don't hesitate to reach out to us at <a href="mailto:{supportemail}">{supportemail}</a>.</p>
        <p>We're excited to have you with us and look forward to helping you find the best deals!</p>
        
        <p style="margin-top: 12px">
        Happy shopping,<br /><strong>Team Growth Value</strong>
        </p>
    </body>
    </html>
    """
    growthvalue_send_mail(
        email_to=email_to,
        subject=subject,
        html_content=html_content,
    )

    return


def send_reset_password_email(user_name="", email_to="", token="",):
    subject = 'Growth Value - Reset Your Password⏰'
    redirect_url = f"{settings.GROWTH_VALUE_BASE_URL}/reset_password/{token}"
    # Email content
    html_content = f"""
    <html>
    <body>
        <div style="padding:20px">
        <p style="margin-top:18px">Hi <strong>{user_name}</strong>,</p>
        <div>
        <p style="margin-top:12px">We heard that you lost your <strong>Growth Value</strong> password. 
        Sorry about that! but don't worry! You can use the following link to reset your password.<br>
        <p><a href="{redirect_url}" >{redirect_url}</a></p><br>
        If you don't use this link within <b>12</b> hours, it will get expired.<br> 
        Thank you for using our services.</p>
        </div>
        <p style="margin-top:12px">Best regards,<br><strong>Team Growth Value</strong></p>
        </div>
    </body>
    </html>
    """
    growthvalue_send_mail(
        email_to=email_to,
        subject=subject,
        html_content=html_content,
    )


def subscription_notif_email(user_name="", email_to="", plan=""):
    subject = 'Thanks for Subscribing to Growth Value🎉'
    # Email Content
    html_content = f"""
    <html>
    <body style="margin: 20px">
        <p>Dear <strong>{user_name}</strong>,</p>
        <br>Thank you for choosing <strong>{plan}</strong> plan!<br /> We are thrilled to have you as a valued customer and are committed to providing you with the best service possible.!<br />
        Your subscription plan is now active, and we want to express our sincere gratitude for your trust.<br />
        Our support team is here to help! If you have any questions or need any assistance, don't hesitate to reach out to us at <a href="mailto:{supportemail}">{supportemail}</a>.<br />
        <p>Thank you once again to connecting with <strong>Growth Value</strong>. We look forward to serving you and ensuring you have the best experience possible.</p>
        <p style="margin-top: 12px">
        Happy shopping,<br /><strong>Team Growth Value</strong>
        </p>
    </body>
    </html>
    """
    growthvalue_send_mail(
        email_to=email_to,
        subject=subject,
        html_content=html_content,
    )


def growthvalue_send_mail(
    email_to="",
    subject="",
    html_content=""
):
    email_from = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD
    # Create message container
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = email_from
    msg['To'] = email_to

    # Record the MIME types of both parts - text/plain and text/html.
    part2 = MIMEText(html_content, 'html')

    # Attach parts into message container.
    msg.attach(part2)

    # Send the message via SMTP server
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_from, password)
            server.sendmail(email_from, email_to, msg.as_string())
            _logger.info("Email sent successfully")
    except Exception as e:
        _logger.error(f"Failed to send email: {e}")
