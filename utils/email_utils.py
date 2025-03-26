import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from fastapi import UploadFile
from dotenv import load_dotenv

from utils.logger import logger

load_dotenv()

async def send_email_with_pdf(to_email: str, pdf_file: UploadFile, query: str):
    """
    Send an email with PDF attachment

    Args:
        to_email: str - Recipient's email address
        pdf_file: UploadFile - PDF file from form data
        query: str - Query text to include in email body
    """
    try:
        # Email configuration
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")

        if not smtp_username or not smtp_password:
            raise ValueError("SMTP credentials not configured. Please set SMTP_USERNAME and SMTP_PASSWORD environment variables.")

        from_email = os.getenv("FROM_EMAIL", smtp_username)

        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = "Your Requested PDF Document"

        # Email body
        body = f"""Hello,

Here is your requested PDF document related to the query:
"{query}"

Best regards,
Your Chatbot"""
        msg.attach(MIMEText(body, 'plain'))

        # Attach PDF file
        try:
            pdf_content = await pdf_file.read()
            pdf_attachment = MIMEApplication(pdf_content, _subtype="pdf")
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename=pdf_file.filename)
            msg.attach(pdf_attachment)
        except Exception as e:
            logger.error(f"Error processing PDF attachment: {str(e)}")
            raise ValueError("Invalid PDF file")

        # Send email with explicit SSL/TLS handling
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.ehlo()  # Identify ourselves to the server
            server.starttls()  # Secure the connection
            server.ehlo()  # Re-identify ourselves over TLS
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP Authentication failed. Please check your credentials.")
            raise ValueError("Email authentication failed. Please check your SMTP credentials.")
        except Exception as e:
            logger.error(f"SMTP Error: {str(e)}")
            raise
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise e 