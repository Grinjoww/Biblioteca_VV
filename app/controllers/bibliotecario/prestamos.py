from datetime import date

from flask import jsonify, redirect, render_template, request, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import text

from app.controllers.bibliotecario import bibliotecario_bp
from app.controllers.decoradores import requiere_rol
from app.extensions import db
from app.forms import PrestamoForm
from app.models import ConfiguracionSistema, Ejemplar, Estudiante, Libro, Prestamo


def _validar_prestamo_bd(cedula, isbn):
    return db.session.execute(
        text('SELECT codigo_resultado, mensaje FROM validar_prestamo(:cedula, :isbn)'),
        {'cedula': cedula, 'isbn': isbn},
    ).fetchone()


def _max_prestamos_activos():
    """Lee el limite configurable; si no existe o es invalido, no limita."""
    config = ConfiguracionSistema.query.filter_by(clave='max_prestamos_activos').first()
    if config is None:
        return None
    try:
        return int(config.valor)
    except (TypeError, ValueError):
        return None


@bibliotecario_bp.route('/prestamos')
@login_required
@requiere_rol('bibliotecario')
def listado_prestamos():
    prestamos = (
        Prestamo.query.filter_by(estado='activo')
        .order_by(Prestamo.fecha_limite)
        .all()
    )
    return render_template('bibliotecario/prestamos_lista.html', prestamos=prestamos, hoy=date.today())


@bibliotecario_bp.route('/prestamos/nuevo', methods=['GET', 'POST'])
@login_required
@requiere_rol('bibliotecario')
def nuevo_prestamo():
    form = PrestamoForm()

    if form.validate_on_submit():
        cedula = form.cedula.data.strip()
        isbn = form.isbn.data.strip()

        resultado = _validar_prestamo_bd(cedula, isbn)

        if resultado is None or resultado.codigo_resultado != 0:
            mensaje = resultado.mensaje if resultado else 'No se pudo validar el préstamo.'
            flash(mensaje, 'danger')
            return render_template('bibliotecario/prestamos_nuevo.html', form=form)

        estudiante = Estudiante.query.filter_by(cedula=cedula).first()
        libro = Libro.query.filter_by(isbn=isbn).first()

        limite = _max_prestamos_activos()
        if limite is not None:
            prestamos_activos = Prestamo.query.filter_by(
                estudiante_id=estudiante.id, estado='activo'
            ).count()
            if prestamos_activos >= limite:
                flash(
                    f'El estudiante ya alcanzó el máximo de {limite} préstamos activos permitidos.',
                    'danger'
                )
                return render_template('bibliotecario/prestamos_nuevo.html', form=form)

        ejemplar = Ejemplar.query.filter_by(libro_id=libro.id, estado='disponible').first()

        if ejemplar is None:
            flash('No hay ejemplares disponibles para este libro en este momento.', 'danger')
            return render_template('bibliotecario/prestamos_nuevo.html', form=form)

        codigo_prestamo = db.session.execute(text('SELECT generar_codigo_prestamo()')).scalar()

        prestamo = Prestamo(
            codigo_prestamo=codigo_prestamo,
            estudiante_id=estudiante.id,
            ejemplar_id=ejemplar.id,
            bibliotecario_id=current_user.id,
            observaciones=(form.observaciones.data or '').strip() or None,
        )
        db.session.add(prestamo)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('No se pudo registrar el préstamo. Intenta nuevamente.', 'danger')
            return render_template('bibliotecario/prestamos_nuevo.html', form=form)

        flash(
            f'Préstamo {prestamo.codigo_prestamo} registrado para '
            f'{estudiante.nombres} {estudiante.apellidos} · Libro: {libro.titulo}.',
            'success'
        )
        return redirect(url_for('bibliotecario.listado_prestamos'))

    return render_template('bibliotecario/prestamos_nuevo.html', form=form)


@bibliotecario_bp.route('/api/prestamos/validar')
@login_required
@requiere_rol('bibliotecario')
def api_validar_prestamo():
    cedula = (request.args.get('cedula') or '').strip()
    isbn = (request.args.get('isbn') or '').strip()

    if len(cedula) != 10 or not cedula.isdigit() or len(isbn) != 13 or not isbn.isdigit():
        return jsonify({
            'codigo_resultado': -1,
            'mensaje': 'Ingresa una cédula (10 dígitos) y un ISBN (13 dígitos) válidos.',
        })

    resultado = _validar_prestamo_bd(cedula, isbn)
    if resultado is None:
        return jsonify({'codigo_resultado': -1, 'mensaje': 'No se pudo validar el préstamo.'})

    respuesta = {'codigo_resultado': resultado.codigo_resultado, 'mensaje': resultado.mensaje}

    if resultado.codigo_resultado == 0:
        estudiante = Estudiante.query.filter_by(cedula=cedula).first()
        libro = Libro.query.filter_by(isbn=isbn).first()
        respuesta['estudiante'] = f'{estudiante.nombres} {estudiante.apellidos}' if estudiante else None
        respuesta['libro'] = libro.titulo if libro else None

    return jsonify(respuesta)
