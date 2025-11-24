import os
# Es necesario importar os para leer las variables de entorno

class Config:
    # --- CONFIGURACIÓN DE BASE DE DATOS (Soluciona Egress Fees) ---
    # 1. Lee la URL de la base de datos de las variables de entorno (MySQL_URL)
    db_url = os.environ.get('MYSQL_URL')
    
    # 2. Corrección para SQLAlchemy: Reemplaza "mysql://" por "mysql+pymysql://" si está presente.
    if db_url and db_url.startswith("mysql://"):
        db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)

    # 3. Asignación final: Usa la URL de Railway (privada) o la URL local como respaldo.
    SQLALCHEMY_DATABASE_URI = db_url or 'mysql+pymysql://root:@127.0.0.1:3306/institucion_db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- SEGURIDAD ---
    # Lee SECRET_KEY de Railway o usa la local.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-llave-secreta-para-proteger-las-sesiones'

    # --- CONFIGURACIÓN DE CORREO (SOLUCIONA EL ERROR 500) ---
    # Todas las credenciales sensibles deben leerse de las Variables de Entorno de Railway.
    # ¡Esto soluciona el WORKER TIMEOUT!

    # Lee el servidor desde Railway o usa Gmail como respaldo.
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    # Lee el puerto desde Railway o usa 587 como respaldo.
    MAIL_PORT = os.environ.get('MAIL_PORT', 587)
    # Lee la opción de TLS (True/False) desde Railway.
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True' 
    # Lee el usuario (tu correo) desde Railway o usa el valor predeterminado.
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'Gestion.Acentrax@gmail.com'
    # Lee la CLAVE DE APLICACIÓN desde Railway (¡CRÍTICO!).
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'bgycesijhhnoqhac'   
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'Gestion.Acentrax@gmail.com'
    
    # --- CONFIGURACIÓN DEL SERVIDOR ---
    # Hemos quitado el SERVER_NAME estático.
    # Si quieres una URL personalizada, puedes leerla de una variable de Railway.
    # SERVER_NAME = os.environ.get('SERVER_NAME') or 'localhost:5000' 
    APPLICATION_ROOT = '/'
    
    # Esto asegura que los enlaces generados (como la URL de verificación de correo) usen HTTPS en producción.
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        PREFERRED_URL_SCHEME = 'https'
    else:
        PREFERRED_URL_SCHEME = 'http'
        
    # --- ARCHIVOS Y CARPETAS ---
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'tareas')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'rar'}
