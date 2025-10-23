"""
Servicio para generación de Reportes Académicos
"""

from datetime import datetime
from controllers.models import (
    db, ReporteCalificaciones, PeriodoAcademico, CicloAcademico,
    Matricula, Calificacion, Asistencia, Usuario, Curso, Asignatura
)
from sqlalchemy import and_, func
import json


def generar_reporte_periodo(periodo_id, tipo='general'):
    """
    Genera un reporte de un periodo académico
    
    Args:
        periodo_id (int): ID del periodo
        tipo (str): Tipo de reporte ('general', 'curso', 'estudiante')
    
    Returns:
        ReporteCalificaciones: Reporte generado o None
    """
    try:
        periodo = PeriodoAcademico.query.get(periodo_id)
        if not periodo:
            return None
        
        # Obtener todas las calificaciones del periodo
        calificaciones = Calificacion.query.filter_by(
            periodo_academico_id=periodo_id
        ).all()
        
        if not calificaciones:
            return None
        
        # Agrupar por estudiante
        datos_estudiantes = {}
        for cal in calificaciones:
            est_id = cal.estudianteId
            if est_id not in datos_estudiantes:
                estudiante = Usuario.query.get(est_id)
                datos_estudiantes[est_id] = {
                    'nombre': estudiante.nombre_completo if estudiante else 'Desconocido',
                    'calificaciones': [],
                    'promedio': 0
                }
            
            if cal.valor is not None:
                datos_estudiantes[est_id]['calificaciones'].append(float(cal.valor))
        
        # Calcular promedios
        for est_id in datos_estudiantes:
            if datos_estudiantes[est_id]['calificaciones']:
                promedio = sum(datos_estudiantes[est_id]['calificaciones']) / len(datos_estudiantes[est_id]['calificaciones'])
                datos_estudiantes[est_id]['promedio'] = round(promedio, 2)
        
        # Estadísticas generales
        todos_promedios = [d['promedio'] for d in datos_estudiantes.values() if d['promedio'] > 0]
        promedio_general = sum(todos_promedios) / len(todos_promedios) if todos_promedios else 0
        nota_mas_alta = max(todos_promedios) if todos_promedios else 0
        nota_mas_baja = min(todos_promedios) if todos_promedios else 0
        
        # Crear reporte
        reporte = ReporteCalificaciones(
            periodo_academico_id=periodo_id,
            ciclo_academico_id=periodo.ciclo_academico_id,
            tipo_reporte='periodo',
            nombre_curso=f'Reporte General - {periodo.nombre}',
            datos_estudiantes=datos_estudiantes,
            promedio_general=promedio_general,
            nota_mas_alta=nota_mas_alta,
            nota_mas_baja=nota_mas_baja,
            fecha_generacion=datetime.utcnow(),
            estado='generado'
        )
        
        db.session.add(reporte)
        db.session.commit()
        
        return reporte
        
    except Exception as e:
        db.session.rollback()
        print(f"Error generando reporte de periodo: {e}")
        return None


def generar_certificado_individual(estudiante_id, ciclo_id):
    """
    Genera un certificado individual de un estudiante para todo el ciclo
    
    Args:
        estudiante_id (int): ID del estudiante
        ciclo_id (int): ID del ciclo académico
    
    Returns:
        ReporteCalificaciones: Certificado generado o None
    """
    try:
        estudiante = Usuario.query.get(estudiante_id)
        if not estudiante:
            return None
        
        ciclo = CicloAcademico.query.get(ciclo_id)
        if not ciclo:
            return None
        
        # Obtener matrícula del estudiante en el ciclo
        matricula = Matricula.query.filter_by(
            estudianteId=estudiante_id,
            ciclo_academico_id=ciclo_id
        ).first()
        
        if not matricula:
            return None
        
        # Obtener periodos del ciclo
        periodos = PeriodoAcademico.query.filter_by(
            ciclo_academico_id=ciclo_id
        ).order_by(PeriodoAcademico.numero_periodo).all()
        
        # Datos por periodo y por asignatura
        datos_completos = {
            'estudiante': {
                'id': estudiante.id_usuario,
                'nombre': estudiante.nombre_completo,
                'documento': estudiante.no_identidad
            },
            'ciclo': ciclo.nombre,
            'curso': matricula.curso.nombreCurso if matricula.curso else 'N/A',
            'periodos': {},
            'resumen_final': {}
        }
        
        # Por cada periodo
        for periodo in periodos:
            calificaciones_periodo = Calificacion.query.filter_by(
                estudianteId=estudiante_id,
                periodo_academico_id=periodo.id_periodo
            ).all()
            
            asignaturas_promedios = {}
            for cal in calificaciones_periodo:
                asig_id = cal.asignaturaId
                if asig_id not in asignaturas_promedios:
                    asignatura = Asignatura.query.get(asig_id)
                    asignaturas_promedios[asig_id] = {
                        'nombre': asignatura.nombre if asignatura else 'N/A',
                        'notas': []
                    }
                
                if cal.valor is not None:
                    asignaturas_promedios[asig_id]['notas'].append(float(cal.valor))
            
            # Calcular promedios por asignatura en este periodo
            for asig_id in asignaturas_promedios:
                notas = asignaturas_promedios[asig_id]['notas']
                if notas:
                    asignaturas_promedios[asig_id]['promedio'] = round(sum(notas) / len(notas), 2)
                else:
                    asignaturas_promedios[asig_id]['promedio'] = 0
            
            datos_completos['periodos'][periodo.nombre] = asignaturas_promedios
        
        # Resumen final
        if matricula.promedio_final:
            datos_completos['resumen_final'] = {
                'promedio_general': float(matricula.promedio_final),
                'estado': matricula.estado_promocion,
                'observaciones': matricula.observaciones_cierre
            }
        
        # Crear reporte
        reporte = ReporteCalificaciones(
            ciclo_academico_id=ciclo_id,
            tipo_reporte='estudiante',
            nombre_curso=matricula.curso.nombreCurso if matricula.curso else 'N/A',
            datos_estudiantes=datos_completos,
            promedio_general=float(matricula.promedio_final) if matricula.promedio_final else 0,
            fecha_generacion=datetime.utcnow(),
            estado='generado',
            formato_archivo='pdf',
            nombre_archivo=f'Certificado_{estudiante.nombre}_{estudiante.apellido}_{ciclo.nombre}.pdf'
        )
        
        db.session.add(reporte)
        db.session.commit()
        
        return reporte
        
    except Exception as e:
        db.session.rollback()
        print(f"Error generando certificado individual: {e}")
        return None


def generar_reporte_asistencias(periodo_id, curso_id=None):
    """
    Genera un reporte de asistencias de un periodo
    
    Args:
        periodo_id (int): ID del periodo
        curso_id (int): ID del curso (opcional, None para todos)
    
    Returns:
        ReporteCalificaciones: Reporte de asistencias o None
    """
    try:
        periodo = PeriodoAcademico.query.get(periodo_id)
        if not periodo:
            return None
        
        # Obtener asistencias del periodo
        query = Asistencia.query.filter_by(periodo_academico_id=periodo_id)
        
        if curso_id:
            # Filtrar por curso (necesita join con matricula)
            matriculas_curso = [m.estudianteId for m in Matricula.query.filter_by(cursoId=curso_id).all()]
            query = query.filter(Asistencia.estudianteId.in_(matriculas_curso))
        
        asistencias = query.all()
        
        # Agrupar por estudiante
        datos_estudiantes = {}
        for asist in asistencias:
            est_id = asist.estudianteId
            if est_id not in datos_estudiantes:
                estudiante = Usuario.query.get(est_id)
                datos_estudiantes[est_id] = {
                    'nombre': estudiante.nombre_completo if estudiante else 'Desconocido',
                    'presentes': 0,
                    'faltas': 0,
                    'retardos': 0,
                    'excusas': 0,
                    'total': 0
                }
            
            datos_estudiantes[est_id]['total'] += 1
            
            if asist.estado == 'presente':
                datos_estudiantes[est_id]['presentes'] += 1
            elif asist.estado == 'falta':
                datos_estudiantes[est_id]['faltas'] += 1
            elif asist.estado == 'retardo':
                datos_estudiantes[est_id]['retardos'] += 1
            
            if asist.excusa:
                datos_estudiantes[est_id]['excusas'] += 1
        
        # Calcular porcentajes
        for est_id in datos_estudiantes:
            total = datos_estudiantes[est_id]['total']
            if total > 0:
                porcentaje = (datos_estudiantes[est_id]['presentes'] / total) * 100
                datos_estudiantes[est_id]['porcentaje_asistencia'] = round(porcentaje, 2)
            else:
                datos_estudiantes[est_id]['porcentaje_asistencia'] = 0
        
        # Crear reporte
        curso_nombre = 'Todos los cursos'
        if curso_id:
            curso = Curso.query.get(curso_id)
            curso_nombre = curso.nombreCurso if curso else 'N/A'
        
        reporte = ReporteCalificaciones(
            periodo_academico_id=periodo_id,
            ciclo_academico_id=periodo.ciclo_academico_id,
            curso_id=curso_id,
            tipo_reporte='asistencias',
            nombre_curso=curso_nombre,
            datos_estudiantes=datos_estudiantes,
            fecha_generacion=datetime.utcnow(),
            estado='generado',
            formato_archivo='excel',
            nombre_archivo=f'Asistencias_{periodo.nombre}_{curso_nombre}.xlsx'
        )
        
        db.session.add(reporte)
        db.session.commit()
        
        return reporte
        
    except Exception as e:
        db.session.rollback()
        print(f"Error generando reporte de asistencias: {e}")
        return None


def generar_reporte_promocion(ciclo_id):
    """
    Genera un reporte de promoción de todo el ciclo
    
    Args:
        ciclo_id (int): ID del ciclo académico
    
    Returns:
        ReporteCalificaciones: Reporte de promoción o None
    """
    try:
        ciclo = CicloAcademico.query.get(ciclo_id)
        if not ciclo:
            return None
        
        # Obtener todas las matrículas finalizadas del ciclo
        matriculas = Matricula.query.filter_by(
            ciclo_academico_id=ciclo_id,
            estado_matricula='finalizada'
        ).all()
        
        # Estadísticas
        total = len(matriculas)
        aprobados = len([m for m in matriculas if m.estado_promocion == 'aprobado'])
        reprobados = len([m for m in matriculas if m.estado_promocion == 'reprobado'])
        graduados = len([m for m in matriculas if m.estado_promocion == 'graduado'])
        
        # Datos detallados
        datos_promocion = {
            'estadisticas': {
                'total': total,
                'aprobados': aprobados,
                'reprobados': reprobados,
                'graduados': graduados,
                'tasa_aprobacion': round((aprobados + graduados) / total * 100, 2) if total > 0 else 0,
                'tasa_reprobacion': round(reprobados / total * 100, 2) if total > 0 else 0
            },
            'por_curso': {},
            'lista_estudiantes': []
        }
        
        # Agrupar por curso
        for matricula in matriculas:
            curso_nombre = matricula.curso.nombreCurso if matricula.curso else 'N/A'
            
            if curso_nombre not in datos_promocion['por_curso']:
                datos_promocion['por_curso'][curso_nombre] = {
                    'total': 0,
                    'aprobados': 0,
                    'reprobados': 0,
                    'graduados': 0
                }
            
            datos_promocion['por_curso'][curso_nombre]['total'] += 1
            
            if matricula.estado_promocion == 'aprobado':
                datos_promocion['por_curso'][curso_nombre]['aprobados'] += 1
            elif matricula.estado_promocion == 'reprobado':
                datos_promocion['por_curso'][curso_nombre]['reprobados'] += 1
            elif matricula.estado_promocion == 'graduado':
                datos_promocion['por_curso'][curso_nombre]['graduados'] += 1
            
            # Lista de estudiantes
            estudiante = Usuario.query.get(matricula.estudianteId)
            datos_promocion['lista_estudiantes'].append({
                'nombre': estudiante.nombre_completo if estudiante else 'Desconocido',
                'documento': estudiante.no_identidad if estudiante else 'N/A',
                'curso': curso_nombre,
                'promedio': float(matricula.promedio_final) if matricula.promedio_final else 0,
                'estado': matricula.estado_promocion,
                'observaciones': matricula.observaciones_cierre
            })
        
        # Crear reporte
        reporte = ReporteCalificaciones(
            ciclo_academico_id=ciclo_id,
            tipo_reporte='promocion',
            nombre_curso='Reporte de Promoción General',
            datos_estudiantes=datos_promocion,
            promedio_general=datos_promocion['estadisticas']['tasa_aprobacion'],
            fecha_generacion=datetime.utcnow(),
            estado='generado',
            formato_archivo='excel',
            nombre_archivo=f'Reporte_Promocion_{ciclo.nombre}.xlsx'
        )
        
        db.session.add(reporte)
        db.session.commit()
        
        return reporte
        
    except Exception as e:
        db.session.rollback()
        print(f"Error generando reporte de promoción: {e}")
        return None


def generar_estadisticas_ciclo(ciclo_id):
    """
    Genera estadísticas generales de un ciclo académico
    
    Args:
        ciclo_id (int): ID del ciclo académico
    
    Returns:
        ReporteCalificaciones: Reporte de estadísticas o None
    """
    try:
        ciclo = CicloAcademico.query.get(ciclo_id)
        if not ciclo:
            return None
        
        # Obtener todos los periodos
        periodos = PeriodoAcademico.query.filter_by(ciclo_academico_id=ciclo_id).all()
        
        # Obtener todas las calificaciones del ciclo
        calificaciones_ciclo = []
        for periodo in periodos:
            cals = Calificacion.query.filter_by(periodo_academico_id=periodo.id_periodo).all()
            calificaciones_ciclo.extend(cals)
        
        # Obtener todas las asistencias del ciclo
        asistencias_ciclo = []
        for periodo in periodos:
            asists = Asistencia.query.filter_by(periodo_academico_id=periodo.id_periodo).all()
            asistencias_ciclo.extend(asists)
        
        # Calcular estadísticas
        valores_notas = [float(c.valor) for c in calificaciones_ciclo if c.valor is not None]
        
        estadisticas = {
            'ciclo': ciclo.nombre,
            'total_periodos': len(periodos),
            'calificaciones': {
                'total': len(calificaciones_ciclo),
                'promedio_general': round(sum(valores_notas) / len(valores_notas), 2) if valores_notas else 0,
                'nota_maxima': max(valores_notas) if valores_notas else 0,
                'nota_minima': min(valores_notas) if valores_notas else 0
            },
            'asistencias': {
                'total_registros': len(asistencias_ciclo),
                'presentes': len([a for a in asistencias_ciclo if a.estado == 'presente']),
                'faltas': len([a for a in asistencias_ciclo if a.estado == 'falta']),
                'retardos': len([a for a in asistencias_ciclo if a.estado == 'retardo']),
                'porcentaje_asistencia': 0
            },
            'por_periodo': {}
        }
        
        # Calcular porcentaje de asistencia
        if len(asistencias_ciclo) > 0:
            porcentaje = (estadisticas['asistencias']['presentes'] / len(asistencias_ciclo)) * 100
            estadisticas['asistencias']['porcentaje_asistencia'] = round(porcentaje, 2)
        
        # Estadísticas por periodo
        for periodo in periodos:
            cals_periodo = [c for c in calificaciones_ciclo if c.periodo_academico_id == periodo.id_periodo]
            valores_periodo = [float(c.valor) for c in cals_periodo if c.valor is not None]
            
            estadisticas['por_periodo'][periodo.nombre] = {
                'calificaciones': len(cals_periodo),
                'promedio': round(sum(valores_periodo) / len(valores_periodo), 2) if valores_periodo else 0
            }
        
        # Crear reporte
        reporte = ReporteCalificaciones(
            ciclo_academico_id=ciclo_id,
            tipo_reporte='general',
            nombre_curso='Estadísticas Generales del Ciclo',
            datos_estudiantes=estadisticas,
            promedio_general=estadisticas['calificaciones']['promedio_general'],
            nota_mas_alta=estadisticas['calificaciones']['nota_maxima'],
            nota_mas_baja=estadisticas['calificaciones']['nota_minima'],
            fecha_generacion=datetime.utcnow(),
            estado='generado',
            formato_archivo='excel',
            nombre_archivo=f'Estadisticas_{ciclo.nombre}.xlsx'
        )
        
        db.session.add(reporte)
        db.session.commit()
        
        return reporte
        
    except Exception as e:
        db.session.rollback()
        print(f"Error generando estadísticas: {e}")
        return None


def obtener_reportes_ciclo(ciclo_id):
    """
    Obtiene todos los reportes generados para un ciclo
    
    Args:
        ciclo_id (int): ID del ciclo académico
    
    Returns:
        list: Lista de reportes
    """
    return ReporteCalificaciones.query.filter_by(
        ciclo_academico_id=ciclo_id
    ).order_by(ReporteCalificaciones.fecha_generacion.desc()).all()


def obtener_reportes_periodo(periodo_id):
    """
    Obtiene todos los reportes generados para un periodo
    
    Args:
        periodo_id (int): ID del periodo académico
    
    Returns:
        list: Lista de reportes
    """
    return ReporteCalificaciones.query.filter_by(
        periodo_academico_id=periodo_id
    ).order_by(ReporteCalificaciones.fecha_generacion.desc()).all()

