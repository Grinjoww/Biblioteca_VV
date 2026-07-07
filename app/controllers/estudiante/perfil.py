from flask import render_template, flash
from flask_login import login_required, current_user

from app.controllers.decoradores import requiere_rol
from app.controllers.estudiante import estudiante_bp
from app.models import Prestamo


@estudiante_bp.route('/perfil')
@login_required
@requiere_rol('estudiante')
def mi_perfil():
    estudiante = current_user.estudiante
    if estudiante is None:
        flash('Tu cuenta no tiene un perfil de estudiante vinculado. Contacta al bibliotecario.', 'warning')
        return render_template('estudiante/perfil.html', estudiante=None, prestamos_activos=0)

    prestamos_activos = Prestamo.query.filter_by(estudiante_id=estudiante.id, estado='activo').count()

    return render_template(
        'estudiante/perfil.html', estudiante=estudiante, prestamos_activos=prestamos_activos
    )
