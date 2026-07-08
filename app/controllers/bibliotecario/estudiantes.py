import secrets

from flask import jsonify, redirect, render_template, request, url_for, flash
from flask_login import login_required
from werkzeug.security import generate_password_hash

from app.controllers.bibliotecario import bibliotecario_bp
from app.controllers.decoradores import requiere_rol
from app.extensions import db
from app.forms import EstudianteForm
from app.models import Carrera, Estudiante, Usuario
from app.validators import es_cedula_ecuatoriana_valida


def _generar_password_temporal():
    return secrets.token_urlsafe(6)


@bibliotecario_bp.route('/estudiantes')
@login_required
@requiere_rol('bibliotecario')
def listado_estudiantes():
    estudiantes = Estudiante.query.order_by(Estudiante.apellidos, Estudiante.nombres).all()
    return render_template('bibliotecario/estudiantes_lista.html', estudiantes=estudiantes)


@bibliotecario_bp.route('/estudiantes/nuevo', methods=['GET', 'POST'])
@login_required
@requiere_rol('bibliotecario')
def nuevo_estudiante():
    form = EstudianteForm()
    form.carrera_id.choices = [(0, '-- Selecciona una carrera --')] + [
        (carrera.id, f'{carrera.nombre} ({carrera.facultad.nombre})')
        for carrera in Carrera.query.join(Carrera.facultad).order_by(Carrera.nombre)
    ]

    if form.validate_on_submit():
        if Estudiante.query.filter_by(cedula=form.cedula.data).first():
            flash('Ya existe un estudiante registrado con esa cédula.', 'danger')
            return render_template('bibliotecario/estudiantes_nuevo.html', form=form)

        if Estudiante.query.filter_by(correo=form.correo.data).first():
            flash('Ya existe un estudiante registrado con ese correo.', 'danger')
            return render_template('bibliotecario/estudiantes_nuevo.html', form=form)

        if Usuario.query.filter_by(username=form.cedula.data).first():
            flash('Ya existe una cuenta de usuario con esa cédula.', 'danger')
            return render_template('bibliotecario/estudiantes_nuevo.html', form=form)

        password_temporal = _generar_password_temporal()

        usuario = Usuario(
            username=form.cedula.data,
            password_hash=generate_password_hash(password_temporal),
            rol='estudiante',
            debe_cambiar_password=True,
        )
        db.session.add(usuario)
        db.session.flush()

        estudiante = Estudiante(
            cedula=form.cedula.data,
            nombres=form.nombres.data.strip(),
            apellidos=form.apellidos.data.strip(),
            correo=form.correo.data.strip(),
            telefono=(form.telefono.data or '').strip() or None,
            carrera_id=form.carrera_id.data,
            fecha_nacimiento=form.fecha_nacimiento.data,
            genero=form.genero.data or None,
            usuario_id=usuario.id,
        )
        db.session.add(estudiante)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('No se pudo registrar el estudiante. Verifica los datos ingresados.', 'danger')
            return render_template('bibliotecario/estudiantes_nuevo.html', form=form)

        flash(
            f'Estudiante registrado correctamente. Usuario: {usuario.username} · '
            f'Contraseña temporal: {password_temporal} (el estudiante deberá cambiarla al ingresar).',
            'success'
        )
        return redirect(url_for('bibliotecario.listado_estudiantes'))

    return render_template('bibliotecario/estudiantes_nuevo.html', form=form)


@bibliotecario_bp.route('/api/estudiantes/verificar-cedula')
@login_required
@requiere_rol('bibliotecario')
def api_verificar_cedula():
    cedula = (request.args.get('cedula') or '').strip()
    if not es_cedula_ecuatoriana_valida(cedula):
        return jsonify({'valida': False, 'existe': False, 'mensaje': 'La cédula ingresada no es válida.'})

    estudiante = Estudiante.query.filter_by(cedula=cedula).first()
    if estudiante:
        return jsonify({
            'valida': True,
            'existe': True,
            'mensaje': f'Ya existe un estudiante registrado: {estudiante.nombres} {estudiante.apellidos}.',
        })

    return jsonify({'valida': True, 'existe': False, 'mensaje': 'Cédula disponible.'})
