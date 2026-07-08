from flask import render_template
from flask_login import login_required
from sqlalchemy import text

from app.controllers.decoradores import requiere_rol
from app.controllers.gerente import gerente_bp
from app.extensions import db


@gerente_bp.route('/dashboard')
@login_required
@requiere_rol('gerente')
def dashboard():
    fila = db.session.execute(text('SELECT * FROM obtener_indicadores_dashboard()')).fetchone()

    indicadores = {
        'total_libros': fila.total_libros if fila else 0,
        'prestamos_activos': fila.prestamos_activos if fila else 0,
        'devoluciones_con_multa': fila.devoluciones_con_multa if fila else 0,
        'estudiantes_con_vencidos': fila.estudiantes_con_vencidos if fila else 0,
    }

    return render_template('gerente/dashboard.html', indicadores=indicadores)
