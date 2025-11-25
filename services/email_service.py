import os
import secrets
import string
import requests
from threading import Thread
from flask import current_app, render_template, url_for
from itsdangerous import URLSafeTimedSerializer


# =========================================================
#  SENDGRID API
# =========================================================

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

def sendgrid_send_email(to_email, subject, html_content):
    """
    Envía correos usando la API de SendGrid.
    Compatible con Railway (NO usa SMTP).
    """
    url = "https://api.sendgrid.com/v3/mail/send"

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "personalizations": [{
            "to": [{"email": to_email}],
            "subject": subject
        }],
        "from": {"email": "gestion.acentrax@gmail.com.com"},  # Puede ser tu mismo correo
        "content": [{
            "type": "text/html",
            "value": html_content
        }]
    }

    response = requests.post(url, json=data, headers=headers)

    print("DEBUG SENDGRID:", response.status_code, response.text)


# =========================================================
#  FUNCIONES ASÍNCRONAS
# =========================================================

def send_async_email(to, subject, html):
    """
    Envío asíncrono REAL usando SendGrid API.
    """
    try:
        sendgrid_send_email(to, subject, html)
    except Exception as e:
        print("ERROR ENVIANDO CORREO SENDGRID:", str(e))


# =========================================================
#  GENERACIÓN DE TOKENS Y CÓDIGOS
# =========================================================

def generate_verification_code():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

def generate_verification_token(user_id, code, email):
    s = get_serializer()
    return s.dumps({
        'user_id': user_id,
        'code': code,
        'email': email
    }, salt='email-verification')


# =========================================================
#  ENVÍO DE EMAILS
# =========================================================

def send_welcome_email(usuario, verification_code):
    """
    Enviar correo con SENDGRID (asíncrono).
    """
    try:
        token = generate_verification_token(usuario.id_usuario, verification_code, usuario.correo)
        verification_url = url_for('auth.verify_email_with_token', token=token, _external=True)

        print(f"DEBUG: Token: {token}")
        print(f"DEBUG: URL: {verification_url}")

        subject = "¡Bienvenido al Sistema Académico - Verifica tu Email!"

        html_body = render_template(
            'emails/welcome_verification.html',
            usuario=usuario,
            verification_code=verification_code,
            verification_url=verification_url
        )

        Thread(target=send_async_email, args=(usuario.correo, subject, html_body)).start()
        return True

    except Exception as e:
        print("ERROR PREPARANDO CORREO:", str(e))
        return True



def send_verification_success_email(usuario, password=None):
    try:
        subject = "✅ Verificación Exitosa - Tus Credenciales"
        html_body = render_template(
            'emails/verification_success.html',
            usuario=usuario,
            password=password,
            login_url=url_for('auth.login', _external=True)
        )

        Thread(target=send_async_email, args=(usuario.correo, subject, html_body)).start()
        return True

    except Exception as e:
        print("ERROR correo éxito:", str(e))
        return False



def send_password_reset_email(usuario, token):
    try:
        reset_url = url_for('auth.restablecer_password', token=token, _external=True)

        subject = "Restablecimiento de Contraseña"
        html_body = render_template(
            'emails/password_reset.html',
            usuario=usuario,
            reset_url=reset_url
        )

        Thread(target=send_async_email, args=(usuario.correo, subject, html_body)).start()
        return True

    except Exception as e:
        print("ERROR reset:", str(e))
        return False



def send_welcome_email_with_retry(usuario, verification_code, max_retries=2):
    return send_welcome_email(usuario, verification_code)



def get_verification_info(usuario):
    token = generate_verification_token(usuario.id_usuario, usuario.verification_code, usuario.correo)
    verification_url = url_for('auth.verify_email_with_token', token=token, _external=True)

    return {
        'code': usuario.verification_code,
        'url': verification_url,
        'expires': usuario.verification_code_expires
    }
