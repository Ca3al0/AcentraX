from flask import Flask, render_template, request, jsonify # Añadir jsonify si lo usas en otro lado
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

app = Flask(__name__, static_folder='static', template_folder='templates') # Añadir carpetas explícitamente es buena práctica
app.config.from_object(Config)
init_app(app)

# 1. APLICAR EL WRAPPER VERCEL (SOLUCIÓN AL PROBLEMA DE RUTAS ESTÁTICAS)
# Esto DEBE estar antes de que la aplicación se corra.
app.wsgi_app = VercelStaticFiles(app.wsgi_app) 

# Add getattr to Jinja2 environment
app.jinja_env.globals.update(getattr=getattr)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# 2. SE COMENTA O ELIMINA EL CÓDIGO DE INICIALIZACIÓN DE DATOS PERMANENTE 
# ESTO FALLARÍA EN VERCEL SI LAS VARIABLES DE ENTORNO DB NO ESTÁN LISTAS.
# Si necesitas inicializar la DB, hazlo en un script de Python separado ejecutado manualmente.
def create_initial_data():
    with app.app_context():
        # **ESTO DEBE SER MANEJADO CUIDADOSAMENTE**
        db.create_all() 
        print("Base de datos y tablas verificadas/creadas.")

        roles_to_create = ['Super Admin', 'Profesor', 'Estudiante', 'Padre']
        # ... resto de la lógica de creación de roles y usuario
        # Se deja aquí solo para referencia, pero debe ser controlado.
        # ...
        pass


# 3. SOLUCIÓN TEMPORAL PARA CARGA DE ARCHIVOS (SUBIDAS)
# ESTO DEBE SER REEMPLAZADO POR S3 O GCS
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
    try:
        if current_user.is_authenticated:
            # Lazy import to avoid circular imports
            from services.notification_service import contar_notificaciones_no_leidas
            unread = contar_notificaciones_no_leidas(current_user.id_usuario)
        else:
            unread = 0
    except Exception:
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
