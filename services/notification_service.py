from flask import current_app
from controllers.models import db, Notificacion, Usuario
from datetime import datetime

def crear_notificacion(usuario_id, titulo, mensaje, tipo='general', link=None, auto_commit=True):
    """Crea una nueva notificación para un usuario.
    
    Args:
        usuario_id: ID del usuario que recibirá la notificación
        titulo: Título de la notificación
        mensaje: Contenido del mensaje
        tipo: Tipo de notificación (general, tarea, solicitud, etc.)
        link: URL opcional para redirección
        auto_commit: Si es True, hace commit automático. Si es False, solo agrega a la sesión.
    """
    try:
        notificacion = Notificacion(
            usuario_id=usuario_id,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            link=link,
            leida=False
        )
        
        db.session.add(notificacion)
        
        if auto_commit:
            db.session.commit()
        
        return notificacion
    except Exception as e:
        if auto_commit:
            db.session.rollback()
        print(f"Error creando notificación: {str(e)}")
        return None

def notificar_respuesta_solicitud(solicitud):
    """Envía notificación al padre cuando el profesor responde a una solicitud."""
    try:
        if solicitud.estado == 'aceptada':
            titulo = " Solicitud de Calificaciones Aceptada"
            mensaje = f"El profesor {solicitud.profesor.nombre_completo} ha aceptado tu solicitud para revisar las calificaciones de {solicitud.nombre_completo_hijo} en {solicitud.asignatura.nombre}."
            link = f"/padre/ver_calificaciones_estudiante/{solicitud.estudiante_id}/{solicitud.asignatura_id}"
        else:
            titulo = " Solicitud de Calificaciones Denegada"
            mensaje = f"El profesor {solicitud.profesor.nombre_completo} ha denegado tu solicitud para revisar las calificaciones de {solicitud.nombre_completo_hijo} en {solicitud.asignatura.nombre}."
            if solicitud.respuesta_profesor:
                mensaje += f"\n\nComentario del profesor: {solicitud.respuesta_profesor}"
            link = "/padre/consultar_estudiante"
        
        return crear_notificacion(
            usuario_id=solicitud.padre_id,
            titulo=titulo,
            mensaje=mensaje,
            tipo='solicitud',
            link=link
        )
    except Exception as e:
        print(f"Error notificando respuesta de solicitud: {str(e)}")
        return None

def notificar_nueva_solicitud(solicitud):
    """Envía notificación al profesor cuando llega una nueva solicitud."""
    try:
        titulo = " Nueva Solicitud de Consulta de Calificaciones"
        mensaje = f"El padre {solicitud.padre.nombre_completo} ha solicitado revisar las calificaciones de {solicitud.nombre_completo_hijo} en {solicitud.asignatura.nombre}."
        link = "/profesor/solicitudes"
        
        return crear_notificacion(
            usuario_id=solicitud.profesor_id,
            titulo=titulo,
            mensaje=mensaje,
            tipo='solicitud',
            link=link
        )
    except Exception as e:
        print(f"Error notificando nueva solicitud: {str(e)}")
        return None

def obtener_notificaciones_no_leidas(usuario_id):
    """Obtiene las notificaciones no leídas de un usuario."""
    try:
        return Notificacion.query.filter_by(
            usuario_id=usuario_id,
            leida=False
        ).order_by(Notificacion.creada_en.desc()).all()
    except Exception as e:
        print(f"Error obteniendo notificaciones: {str(e)}")
        return []

def contar_notificaciones_no_leidas(usuario_id):
    """Cuenta las notificaciones no leídas de un usuario."""
    try:
        return Notificacion.query.filter_by(
            usuario_id=usuario_id,
            leida=False
        ).count()
    except Exception as e:
        print(f"Error contando notificaciones: {str(e)}")
        return 0

def marcar_notificacion_como_leida(notificacion_id, usuario_id):
    """Marca una notificación como leída."""
    try:
        notificacion = Notificacion.query.filter_by(
            id_notificacion=notificacion_id,
            usuario_id=usuario_id
        ).first()
        
        if notificacion:
            notificacion.leida = True
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error marcando notificación como leída: {str(e)}")
        return False

def obtener_todas_notificaciones(usuario_id, limite=50):
    """Obtiene todas las notificaciones de un usuario."""
    try:
        return Notificacion.query.filter_by(
            usuario_id=usuario_id
        ).order_by(Notificacion.creada_en.desc()).limit(limite).all()
    except Exception as e:
        print(f"Error obteniendo todas las notificaciones: {str(e)}")
        return []


# ============================================================================
# NOTIFICACIONES DEL SISTEMA DE PERIODOS ACADÉMICOS
# ============================================================================

def notificar_inicio_ciclo(ciclo_id):
    """Notifica a todos los usuarios sobre el inicio de un nuevo ciclo académico."""
    try:
        from controllers.models import CicloAcademico, Rol
        
        ciclo = CicloAcademico.query.get(ciclo_id)
        if not ciclo:
            return 0
        
        # Obtener todos los usuarios (estudiantes, profesores, padres)
        roles_notificar = ['estudiante', 'profesor', 'padre', 'admin']
        usuarios = Usuario.query.join(Rol).filter(
            Rol.nombre.in_(roles_notificar)
        ).all()
        
        titulo = f"🎓 Inicio del {ciclo.nombre}"
        mensaje = f"Bienvenidos al nuevo año escolar: {ciclo.nombre}. " \
                  f"Fecha de inicio: {ciclo.fecha_inicio.strftime('%d/%m/%Y')}. ¡Mucho éxito!"
        
        contador = 0
        for usuario in usuarios:
            notif = Notificacion(
                usuario_id=usuario.id_usuario,
                titulo=titulo,
                mensaje=mensaje,
                tipo='sistema',
                tipo_evento='inicio_ciclo',
                ciclo_academico_id=ciclo_id,
                enviada=True,
                link='/dashboard'
            )
            db.session.add(notif)
            contador += 1
        
        db.session.commit()
        return contador
        
    except Exception as e:
        db.session.rollback()
        print(f"Error notificando inicio de ciclo: {str(e)}")
        return 0


def notificar_inicio_periodo(periodo_id):
    """Notifica a todos los usuarios sobre el inicio de un nuevo periodo."""
    try:
        from controllers.models import PeriodoAcademico, Rol
        
        periodo = PeriodoAcademico.query.get(periodo_id)
        if not periodo:
            return 0
        
        # Obtener todos los usuarios activos
        roles_notificar = ['estudiante', 'profesor', 'padre']
        usuarios = Usuario.query.join(Rol).filter(
            Rol.nombre.in_(roles_notificar)
        ).all()
        
        titulo = f"📚 Inicio del {periodo.nombre}"
        mensaje = f"Ha iniciado el {periodo.nombre} del año escolar. " \
                  f"Fecha de cierre de notas: {periodo.fecha_cierre_notas.strftime('%d/%m/%Y')}. " \
                  "¡Mucho éxito en este periodo!"
        
        contador = 0
        for usuario in usuarios:
            notif = Notificacion(
                usuario_id=usuario.id_usuario,
                titulo=titulo,
                mensaje=mensaje,
                tipo='sistema',
                tipo_evento='inicio_periodo',
                periodo_academico_id=periodo_id,
                ciclo_academico_id=periodo.ciclo_academico_id,
                enviada=True,
                link='/dashboard'
            )
            db.session.add(notif)
            contador += 1
        
        db.session.commit()
        return contador
        
    except Exception as e:
        db.session.rollback()
        print(f"Error notificando inicio de periodo: {str(e)}")
        return 0


def notificar_proximidad_cierre(periodo_id):
    """Notifica a los profesores sobre la proximidad del cierre del periodo."""
    try:
        from controllers.models import PeriodoAcademico, Rol
        
        periodo = PeriodoAcademico.query.get(periodo_id)
        if not periodo:
            return 0
        
        dias_restantes = periodo.dias_para_cierre()
        if dias_restantes is None:
            return 0
        
        # Obtener solo profesores
        rol_profesor = Rol.query.filter_by(nombre='profesor').first()
        if not rol_profesor:
            return 0
        
        profesores = Usuario.query.filter_by(id_rol_fk=rol_profesor.id_rol).all()
        
        titulo = f"⚠️ Cierre de Notas Próximo - {periodo.nombre}"
        mensaje = f"Recordatorio: El cierre de notas del {periodo.nombre} será en {dias_restantes} días " \
                  f"({periodo.fecha_cierre_notas.strftime('%d/%m/%Y')}). " \
                  "Por favor, asegúrese de ingresar todas las calificaciones a tiempo."
        
        contador = 0
        for profesor in profesores:
            notif = Notificacion(
                usuario_id=profesor.id_usuario,
                titulo=titulo,
                mensaje=mensaje,
                tipo='alerta',
                tipo_evento='proximidad_cierre',
                periodo_academico_id=periodo_id,
                ciclo_academico_id=periodo.ciclo_academico_id,
                enviada=True,
                link='/profesor/dashboard'
            )
            db.session.add(notif)
            contador += 1
        
        db.session.commit()
        return contador
        
    except Exception as e:
        db.session.rollback()
        print(f"Error notificando proximidad de cierre: {str(e)}")
        return 0


def notificar_cierre_periodo(periodo_id):
    """Notifica a todos sobre el cierre de un periodo."""
    try:
        from controllers.models import PeriodoAcademico, Rol
        
        periodo = PeriodoAcademico.query.get(periodo_id)
        if not periodo:
            return 0
        
        # Obtener todos los usuarios
        roles_notificar = ['estudiante', 'profesor', 'padre']
        usuarios = Usuario.query.join(Rol).filter(
            Rol.nombre.in_(roles_notificar)
        ).all()
        
        titulo = f"🔒 {periodo.nombre} Cerrado"
        mensaje = f"El {periodo.nombre} ha sido cerrado. " \
                  "Las calificaciones ya no pueden ser modificadas. " \
                  "Los reportes del periodo ya están disponibles."
        
        contador = 0
        for usuario in usuarios:
            # Link diferente según el rol
            link = '/dashboard'
            if usuario.es_profesor():
                link = '/profesor/dashboard'
            elif usuario.es_padre():
                link = '/padre/informacion_academica'
            elif usuario.es_estudiante():
                link = '/estudiante/dashboard'
            
            notif = Notificacion(
                usuario_id=usuario.id_usuario,
                titulo=titulo,
                mensaje=mensaje,
                tipo='sistema',
                tipo_evento='cierre_periodo',
                periodo_academico_id=periodo_id,
                ciclo_academico_id=periodo.ciclo_academico_id,
                enviada=True,
                link=link
            )
            db.session.add(notif)
            contador += 1
        
        db.session.commit()
        return contador
        
    except Exception as e:
        db.session.rollback()
        print(f"Error notificando cierre de periodo: {str(e)}")
        return 0


def notificar_fin_ciclo(ciclo_id):
    """Notifica a todos sobre el fin de un ciclo académico."""
    try:
        from controllers.models import CicloAcademico, Rol
        
        ciclo = CicloAcademico.query.get(ciclo_id)
        if not ciclo:
            return 0
        
        # Obtener todos los usuarios
        roles_notificar = ['estudiante', 'profesor', 'padre', 'admin']
        usuarios = Usuario.query.join(Rol).filter(
            Rol.nombre.in_(roles_notificar)
        ).all()
        
        titulo = f"🎉 Fin del {ciclo.nombre}"
        mensaje = f"Ha finalizado el año escolar {ciclo.nombre}. " \
                  "Los resultados de promoción y reportes finales ya están disponibles. " \
                  "¡Felicitaciones por completar este ciclo!"
        
        contador = 0
        for usuario in usuarios:
            notif = Notificacion(
                usuario_id=usuario.id_usuario,
                titulo=titulo,
                mensaje=mensaje,
                tipo='sistema',
                tipo_evento='fin_ciclo',
                ciclo_academico_id=ciclo_id,
                enviada=True,
                link='/dashboard'
            )
            db.session.add(notif)
            contador += 1
        
        db.session.commit()
        return contador
        
    except Exception as e:
        db.session.rollback()
        print(f"Error notificando fin de ciclo: {str(e)}")
        return 0


def notificar_promocion(estudiante_id, resultado, promedio, curso_destino_id=None):
    """Notifica a un estudiante y sus padres sobre el resultado de su promoción."""
    try:
        from controllers.models import Curso, estudiante_padre
        
        estudiante = Usuario.query.get(estudiante_id)
        if not estudiante:
            return 0
        
        # Determinar mensaje según resultado
        if resultado == 'aprobado':
            curso_destino = Curso.query.get(curso_destino_id) if curso_destino_id else None
            titulo = "🎉 ¡Felicitaciones! Has sido promovido"
            mensaje = f"Has aprobado el año escolar con un promedio de {promedio}. " \
                      f"Serás promovido a: {curso_destino.nombreCurso if curso_destino else 'próximo nivel'}. " \
                      "¡Excelente trabajo!"
            tipo = 'exito'
        elif resultado == 'reprobado':
            titulo = "📚 Resultado del Año Escolar"
            mensaje = f"Tu promedio final fue de {promedio}. " \
                      "Deberás repetir el grado actual. " \
                      "¡No te desanimes! Puedes lograrlo el próximo año."
            tipo = 'alerta'
        elif resultado == 'graduado':
            titulo = "🎓 ¡Felicitaciones Graduado!"
            mensaje = f"Has completado tu educación con un promedio de {promedio}. " \
                      "¡Felicidades por este gran logro!"
            tipo = 'exito'
        else:
            return 0
        
        contador = 0
        
        # Notificar al estudiante
        notif_estudiante = Notificacion(
            usuario_id=estudiante_id,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            tipo_evento='promocion',
            enviada=True,
            link='/estudiante/dashboard'
        )
        db.session.add(notif_estudiante)
        contador += 1
        
        # Notificar a los padres
        # Obtener padres del estudiante
        padres = db.session.execute(
            db.select(Usuario).join(
                estudiante_padre, 
                Usuario.id_usuario == estudiante_padre.c.padre_id
            ).where(estudiante_padre.c.estudiante_id == estudiante_id)
        ).scalars().all()
        
        for padre in padres:
            mensaje_padre = f"Resultado de {estudiante.nombre_completo}: {mensaje}"
            notif_padre = Notificacion(
                usuario_id=padre.id_usuario,
                titulo=f"Resultado de {estudiante.nombre_completo}",
                mensaje=mensaje_padre,
                tipo=tipo,
                tipo_evento='promocion',
                enviada=True,
                link='/padre/informacion_academica'
            )
            db.session.add(notif_padre)
            contador += 1
        
        db.session.commit()
        return contador
        
    except Exception as e:
        db.session.rollback()
        print(f"Error notificando promoción: {str(e)}")
        return 0


def procesar_notificaciones_programadas():
    """
    Procesa y envía notificaciones que están programadas para hoy.
    Esta función debe ejecutarse diariamente (cron/celery).
    """
    try:
        from datetime import date
        
        # Obtener notificaciones programadas para hoy que no han sido enviadas
        hoy = datetime.now().date()
        notificaciones_pendientes = Notificacion.query.filter(
            Notificacion.programada_para <= datetime.now(),
            Notificacion.enviada == False
        ).all()
        
        contador = 0
        for notif in notificaciones_pendientes:
            notif.enviada = True
            notif.creada_en = datetime.utcnow()
            contador += 1
        
        db.session.commit()
        
        return {
            'procesadas': contador,
            'mensaje': f'{contador} notificaciones enviadas'
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            'error': str(e),
            'procesadas': 0
        }
