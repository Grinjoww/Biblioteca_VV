from flask import redirect, render_template, url_for, flash
from flask_login import login_required
from sqlalchemy import text

from app.controllers.decoradores import requiere_rol
from app.controllers.gerente import gerente_bp
from app.extensions import db

# Lista blanca fija: el parámetro <tipo> de la URL solo se usa para
# buscar en este diccionario. El nombre real de la vista SQL que se
# ejecuta nunca proviene directamente de la petición del usuario.
REPORTES = {
    'prestamos-activos': {
        'titulo': 'Préstamos activos',
        'vista': 'vista_prestamos_activos',
    },
    'multas-pendientes': {
        'titulo': 'Multas pendientes',
        'vista': 'vista_multas_pendientes',
    },
    'libros-mas-prestados': {
        'titulo': 'Libros más prestados',
        'vista': 'vista_libros_mas_prestados',
    },
    'estudiantes-con-deuda': {
        'titulo': 'Estudiantes con deuda',
        'vista': 'vista_estudiantes_con_deuda',
    },
    'inventario-actual': {
        'titulo': 'Inventario actual',
        'vista': 'vista_inventario_actual',
    },
    'historial-movimientos': {
        'titulo': 'Historial de movimientos',
        'vista': 'vista_historial_movimientos',
    },
}


@gerente_bp.route('/reportes')
@login_required
@requiere_rol('gerente')
def listado_reportes():
    return render_template('gerente/reportes.html', reportes=REPORTES)


@gerente_bp.route('/reportes/<tipo>')
@login_required
@requiere_rol('gerente')
def ver_reporte(tipo):
    reporte = REPORTES.get(tipo)
    if reporte is None:
        flash('El reporte solicitado no existe.', 'warning')
        return redirect(url_for('gerente.listado_reportes'))

    resultado = db.session.execute(text(f"SELECT * FROM {reporte['vista']}"))
    columnas = list(resultado.keys())
    filas = resultado.fetchall()

    return render_template(
        'gerente/reporte_detalle.html',
        titulo=reporte['titulo'],
        tipo=tipo,
        columnas=columnas,
        filas=filas,
        reportes=REPORTES,
    )
