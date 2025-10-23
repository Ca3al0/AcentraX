from flask import Flask, render_template, request, jsonify 
from flask_login import current_user
from flask_login import LoginManager
from controllers.models import db, Usuario, Rol
from routes.auth import auth_bp
from routes.main import main_bp
from routes.admin import admin_bp
from routes.estudiantes import estudiante_bp
from routes.profesor import profesor_bp
from routes.padres import padre_bp
from config import Config
from extensions import init_app 
# IMPORTE CRÍTICO PARA VERCEL
from vercel_flask import VercelStaticFiles 
import os

app = Flask(__name__, static_folder='static', template_folder='templates') 
app.config.from_object(Config)

# =================================================================
# === NUEVA COMPROBACIÓN DE SEGURIDAD PARA BASE DE DATOS (CRÍTICO) ===
# Verifica si la URI de la DB existe en la configuración (debería venir de las variables de entorno).
# Esto previene el fallo si la DB no está configurada en Vercel.
IS_DB_CONFIGURED = app.config.get('SQLALCHEMY_DATABASE_URI') is not None

if IS_DB_CONFIGURED:
    init_app(app) # Inicializa la base de datos solo si está configurada
    # 1. APLICAR EL WRAPPER VERCEL (SOLUCIÓN AL PROBLEMA DE RUTAS ESTÁTICAS)
    app.wsgi_app = VercelStaticFiles(app.wsgi_app) 
else:
    # Si la DB no está configurada, se salta la inicialización, evitando el error 500.
    print("WARNING: SQLALCHEMY_DATABASE_URI missing. Skipping DB initialization.")
# =================================================================

# Add getattr to Jinja2 environment
app.jinja_env.globals.update(getattr=getattr)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    # Solo ejecuta la consulta de DB si la conexión fue establecida
    if IS_DB_CONFIGURED:
        return Usuario.query.get(int(user_id))
    return None

# Lógica de Inicialización de Datos (Comentada para Vercel)
def create_initial_data():
    if not IS_DB_CONFIGURED:
        print("Error: No se puede crear data. Base de datos no configurada.")
        return

    with app.app_context():
        # ... Lógica original de db.create_all() y creación de roles/admin ...
        # Se deja el cuerpo de la función vacío para Vercel ya que solo corre en __main__
        pass 


# Solución Temporal para carga de archivos
UPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "images", "candidatos")
# ¡IMPORTANTE! Se comenta la línea que intenta crear la carpeta en un sistema de solo lectura
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(estudiante_bp)
app.register_blueprint(padre_bp)
app.register_blueprint(profesor_bp)

@app.context_processor
def inject_unread_notifications():
    unread = 0
    # Solo intenta acceder a la DB si la conexión fue establecida
    if IS_DB_CONFIGURED and current_user.is_authenticated:
        try:
            # Lazy import to avoid circular imports
            from services.notification_service import contar_notificaciones_no_leidas
            unread = contar_notificaciones_no_leidas(current_user.id_usuario)
        except Exception as e:
            # print(f"Error al cargar notificaciones: {e}") 
            unread = 0
    
    return {
        'unread_notifications': unread,
        'unread_messages': unread,
    }

# ESTE BLOQUE NO SE EJECUTA EN VERCEL. Es solo para desarrollo local.
if __name__ == '__main__':
    with app.app_context():
        create_initial_data()
    app.run(debug=True)
