import logging
from pathlib import Path
from typing import Dict, Any, List
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
import secrets

from app.config import settings

# Configuration du logger
logger = logging.getLogger(__name__)

# Configuration du moteur de templates Jinja2
templates_dir = settings.BASE_DIR / "app" / "templates" / "email"
env = Environment(loader=FileSystemLoader(str(templates_dir)))

def generate_verification_token() -> str:
    """
    Génère un jeton de vérification aléatoire.
    """
    return secrets.token_urlsafe(32)

async def send_email(
    email_to: str,
    subject: str,
    template_name: str,
    template_data: Dict[str, Any]
) -> bool:
    """
    Envoie un email en utilisant un template.
    """
    # Si la configuration email n'est pas définie, enregistrer et sortir
    if not all([settings.MAIL_SERVER, settings.MAIL_PORT, settings.MAIL_USERNAME, 
                settings.MAIL_PASSWORD, settings.MAIL_FROM]):
        logger.warning("Configuration email incomplète, l'email n'a pas été envoyé")
        return False

    # Charger le template
    try:
        template = env.get_template(f"{template_name}.html")
        html_content = template.render(**template_data)
    except Exception as e:
        logger.error(f"Erreur lors du rendu du template: {str(e)}")
        return False

    # Créer le message
    message = MIMEMultipart()
    message["From"] = settings.MAIL_FROM
    message["To"] = email_to
    message["Subject"] = subject
    message.attach(MIMEText(html_content, "html"))

    # Envoyer l'email
    try:
        smtp = aiosmtplib.SMTP(
            hostname=settings.MAIL_SERVER,
            port=settings.MAIL_PORT,
            use_tls=settings.MAIL_TLS
        )
        await smtp.connect()
        await smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        await smtp.send_message(message)
        await smtp.quit()
        logger.info(f"Email envoyé à {email_to}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email: {str(e)}")
        return False

async def send_verification_email(email: str, token: str) -> bool:
    """
    Envoie un email de vérification à un utilisateur.
    """
    verification_url = f"http://{settings.HOST}:{settings.PORT}/api/auth/verify?token={token}"
    
    subject = f"{settings.APP_NAME} - Vérification de votre compte"
    template_data = {
        "app_name": settings.APP_NAME,
        "verification_url": verification_url,
        "token": token
    }
    
    return await send_email(
        email_to=email,
        subject=subject,
        template_name="confirmation",
        template_data=template_data
    )
