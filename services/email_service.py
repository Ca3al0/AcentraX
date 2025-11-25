import os
import secrets
import string
import time
from threading import Thread  # <--- NUEVA IMPORTACIÓN CRÍTICA
from flask_mail import Message
from flask import current_app, render_template, url_for
from extensions import mail
from itsdangerous import URLSafeTimedSerializer  

# --- FUNCIONES ASÍNCRONAS ---

def send_async_email(app, msg):
    """
    Función que envía el correo en un hilo de fondo. 
    Usa app.app_context() para que Flask-Mail sepa qué app usar.
    """
    with app.app_context():
        try:
            mail.send(msg)
            print("DEBUG: Email enviado exitosamente en segundo plano.")
        except Exception as e:
            # Si el correo falla aquí, solo afecta al hilo, NO al usuario.
            error_msg = str(e)
            print(f"ERROR EN HILO DE CORREO (Gmail Block): {error_msg}")
            # Puedes manejar logs o notificaciones aquí si es necesario.


# --- FUNCIONES DE VERIFICACIÓN Y SERIALIZACIÓN ---

def generate_verification_code():
    """Genera un código de verificación de 8 caracteres alfanuméricos"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(8))

def get_serializer():
    """ Obtiene el serializador de forma consistente"""
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

def generate_verification_token(user_id, code, email):
    """Genera token de verificación consistente"""
    s = get_serializer() 
    return s.dumps({
        'user_id': user_id,
        'code': code,
        'email': email
    }, salt='email-verification')


# --- FUNCIONES DE ENVÍO DE CORREO ---

def send_welcome_email(usuario, verification_code):
    """
    MODIFICADA: Inicia el envío de correo en un hilo de fondo 
    para evitar el WORKER TIMEOUT de Gunicorn.
    """
    try:
        verification_token = generate_verification_token(
            usuario.id_usuario, 
            verification_code, 
            usuario.correo
        )
        
        verification_url = url_for('auth.verify_email_with_token', token=verification_token, _external=True)
        
        # DEBUG: Mostrar información del token (como respaldo)
        print(f"DEBUG: Token generado para {usuario.correo}: {verification_token}")
        print(f"DEBUG: URL de verificación: {verification_url}")
        
        subject = "¡Bienvenido al Sistema Académico - Verifica tu Email!"
        
        html_body = render_template(
            'emails/welcome_verification.html',
            usuario=usuario,
            verification_code=verification_code,
            verification_url=verification_url
        )
        
        msg = Message(
            subject=subject,
            recipients=[usuario.correo],
            html=html_body,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        # --- LANZAR EL HILO DE ENVÍO ---
        app = current_app._get_current_object()
        thr = Thread(target=send_async_email, args=(app, msg))
        thr.start()
        
        # Retornar éxito inmediatamente, el envío sigue en el hilo de fondo
        return True
        
    except Exception as e:
        # Esto solo atraparía errores antes de enviar (ej. error de renderizado)
        print(f"Error preparando el correo: {str(e)}")
        # Siempre retornamos éxito para evitar el error 500 al usuario
        return True


def send_verification_success_email(usuario, password=None):
    """Envía correo con credenciales después de verificación exitosa (DEBE HACERSE ASÍNCRONO TAMBIÉN)"""
    # Para consistencia y evitar que esta función también cause timeouts, la haremos asíncrona.
    try:
        subject = "✅ Verificación Exitosa - Tus Credenciales de Acceso"
        
        html_body = render_template(
            'emails/verification_success.html',
            usuario=usuario,
            password=password,
            login_url=url_for('auth.login', _external=True)
        )
        
        msg = Message(
            subject=subject,
            recipients=[usuario.correo],
            html=html_body,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        app = current_app._get_current_object()
        thr = Thread(target=send_async_email, args=(app, msg))
        thr.start()
        
        return True
    except Exception as e:
        print(f"Error preparando correo de verificación exitosa: {str(e)}")
        return False

def send_password_reset_email(usuario, token):
    """Envía correo para restablecer contraseña (DEBE HACERSE ASÍNCRONO TAMBIÉN)"""
    # Para consistencia y evitar que esta función también cause timeouts, la haremos asíncrona.
    try:
        reset_url = url_for('auth.restablecer_password', token=token, _external=True)
        
        subject = "Restablecimiento de Contraseña - Sistema Académico"
        
        html_body = render_template(
            'emails/password_reset.html',
            usuario=usuario,
            reset_url=reset_url
        )
        
        msg = Message(
            subject=subject,
            recipients=[usuario.correo],
            html=html_body,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        app = current_app._get_current_object()
        thr = Thread(target=send_async_email, args=(app, msg))
        thr.start()
        
        return True
    except Exception as e:
        print(f"Error preparando correo de restablecimiento: {str(e)}")
        return False

def send_welcome_email_with_retry(usuario, verification_code, max_retries=2):
    """
    MODIFICADA: Ya no necesita reintentos, porque send_welcome_email es asíncrona y no falla la vista principal.
    Solo llama a la función principal.
    """
    return send_welcome_email(usuario, verification_code)
    
def get_verification_info(usuario):
    """Obtiene información de verificación para mostrar al usuario cuando falla el correo"""
    verification_token = generate_verification_token(
        usuario.id_usuario, 
        usuario.verification_code, 
        usuario.correo
    )
    
    verification_url = url_for('auth.verify_email_with_token', token=verification_token, _external=True)
    
    return {
        'code': usuario.verification_code,
        'url': verification_url,
        'expires': usuario.verification_code_expires
    }
