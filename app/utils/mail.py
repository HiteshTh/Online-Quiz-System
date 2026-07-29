import logging
from flask import current_app
from flask_mail import Message
from app.extensions import mail

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(subject, recipients, html_body, attachment_filename=None, attachment_data=None, attachment_mime=None):
    """
    Sends an email using Flask-Mail.
    If mail credentials/server are not configured, it fails gracefully and logs the message to the console.
    """
    # Quick sanity check: are mail configurations set?
    mail_server = current_app.config.get('MAIL_SERVER')
    mail_username = current_app.config.get('MAIL_USERNAME')
    
    msg = Message(
        subject=subject,
        recipients=recipients,
        html=html_body,
        sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@quizsystem.com')
    )
    
    if attachment_filename and attachment_data:
        msg.attach(
            filename=attachment_filename,
            content_type=attachment_mime or 'application/octet-stream',
            data=attachment_data
        )

    if not mail_server or not mail_username:
        logger.warning(
            f"[MAIL MOCK] Mail server not configured. Email NOT sent to {recipients}.\n"
            f"Subject: {subject}\n"
            f"Body (HTML): {html_body[:300]}...\n"
            f"Attachment: {attachment_filename or 'None'}"
        )
        return False
        
    try:
        mail.send(msg)
        logger.info(f"Email successfully sent to {recipients}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipients}. Error: {str(e)}")
        return False
