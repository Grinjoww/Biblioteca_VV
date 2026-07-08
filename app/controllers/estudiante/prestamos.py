from datetime import date

from flask import render_template, flash
from flask_login import login_required, current_user

from app.controllers.decoradores import requiere_rol
from app.controllers.estudiante import estudiante_bp
from app.models import Prestamo


@estudiante_bp.route('/prestamos')
@login_required
@requiere_rol('estudiante')
def mis_prestamos():
    estudiante = current_user.estudiante
    if estudiante is None:
        flash('Tu cuenta no tiene un perfil de estudiante vinculado. Contacta al bibliotecario.', 'warning')
        return render_template(
            'estudiante/prestamos.html', prestamos_activos=[], historial=[], hoy=date.today()
        )

    todos = (
        Prestamo.query.filter_by(estudiante_id=estudiante.id)
        .order_by(Prestamo.fecha_prestamo.desc())
        .all()
    )
    prestamos_activos = [p for p in todos if p.estado != 'devuelto']
    historial = [p for p in todos if p.estado == 'devuelto']

    return render_template(
        'estudiante/prestamos.html',
        prestamos_activos=prestamos_activos,
        historial=historial,
        hoy=date.today(),
    )
