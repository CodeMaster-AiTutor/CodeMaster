from email.message import EmailMessage
import smtplib

from flask import Blueprint, jsonify, request, current_app

from app.config import Config
from app.utils.validators import validate_email

support_bp = Blueprint('support', __name__)

def _get_sender_email():
    return Config.SMTP_FROM_EMAIL or Config.SMTP_USERNAME

@support_bp.route('/contact', methods=['POST'])
def contact_support():
    data = request.get_json(silent=True) or {}
    name = str(data.get('name', '')).strip()
    email = str(data.get('email', '')).strip().lower()
    subject = str(data.get('subject', '')).strip()
    message_body = str(data.get('message', '')).strip()

    if not name or not email or not subject or not message_body:
        return jsonify({'error': 'All fields are required'}), 400
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    if len(subject) > 200:
        return jsonify({'error': 'Subject is too long'}), 400
    if len(message_body) > 5000:
        return jsonify({'error': 'Message is too long'}), 400

    if not Config.SMTP_HOST:
        return jsonify({'error': 'Email service is not configured'}), 503
    sender = _get_sender_email()
    if not sender:
        return jsonify({'error': 'Email service is not configured'}), 503
    if not Config.SUPPORT_EMAIL:
        return jsonify({'error': 'Support email is not configured'}), 500

    message = EmailMessage()
    message['Subject'] = f"Support: {subject}"
    message['From'] = sender
    message['To'] = Config.SUPPORT_EMAIL
    message['Reply-To'] = email
    message.set_content(f"Name: {name}\nEmail: {email}\nSubject: {subject}\n\n{message_body}")

    try:
        server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=10)
        if Config.SMTP_USE_TLS:
            server.starttls()
        if Config.SMTP_USERNAME and Config.SMTP_PASSWORD:
            server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        server.send_message(message)
        server.quit()
    except Exception as exc:
        current_app.logger.warning(f'Support email failed: {exc}')
        return jsonify({'error': 'Failed to send message'}), 500

    return jsonify({'message': 'Message sent'}), 200
