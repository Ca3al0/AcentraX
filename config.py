import os

class Config:
    # --- CONFIGURACIÓN DE BASE DE DATOS ---
    # 1. Intentamos obtener la URL de la base de datos de las variables de entorno (Railway)
    db_url = os.environ.get('DATABASE_URL')
    
    # 2. Corrección para Railway: SQLAlchemy necesita 'mysql+pymysql://' pero a veces recibe 'mysql://'
    if db_url and db_url.startswith("mysql://"):
        db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)

    # 3. Asignación final: Si hay URL de Railway la usa, si no, usa tu configuración local (tu casa)
    SQLALCHEMY_DATABASE_URI = db_url or 'mysql+pymysql://root:@127.0.0.1:3306/institucion_db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- SEGURIDAD ---
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-llave-secreta-para-proteger-las-sesiones'

    # --- CONFIGURACIÓN DE CORREO ---
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'Gestion.Acentrax@gmail.com'
    # Se recomienda usar variables de entorno para la contraseña también, pero dejé la tuya como respaldo para que te funcione ya.
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'bgycesijhhnoqhac'  
    MAIL_DEFAULT_SENDER = 'Gestion.Acentrax@gmail.com'
    
    # --- CONFIGURACIÓN DEL SERVIDOR ---
    # IMPORTANTE: He comentado (desactivado) SERVER_NAME. 
    # Mantenerlo activo como 'localhost:5000' rompe la aplicación en Railway.
    # SERVER_NAME = 'localhost:5000'  
    
    APPLICATION_ROOT = '/'
    
    # En Railway usamos HTTPS (candadito seguro), en local suele ser HTTP.
    # Esto intenta detectar si estamos en producción.
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        PREFERRED_URL_SCHEME = 'https'
    else:
        PREFERRED_URL_SCHEME = 'http'
        
    # --- ARCHIVOS Y CARPETAS ---
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'tareas')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'rar'}
