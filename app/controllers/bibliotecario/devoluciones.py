from datetime import date
from decimal import Decimal

from flask import redirect, render_template, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import text

from app.controllers.bibliotecario import bibliotecario_bp
from app.controllers.decoradores import requiere_rol
from app.extensions import db
from app.forms import DevolucionForm
from app.models import DanioPerdida, Devolucion, HistorialInventario, Prestamo


@bibliotecario_bp.route('/devoluciones')
@login_required
@requiere_rol('bibliotecario')
def listado_devoluciones():
    prestamos = (
        Prestamo.query.filter_by(estado='activo')
        .order_by(Prestamo.fecha_limite)
        .all()
    )
    return render_template('bibliotecario/devoluciones_lista.html', prestamos=prestamos, hoy=date.today())


@bibliotecario_bp.route('/devoluciones/registrar/<int:prestamo_id>', methods=['GET', 'POST'])
@login_required
@requiere_rol('bibliotecario')
def registrar_devolucion(prestamo_id):
    prestamo = Prestamo.query.filter_by(id=prestamo_id, estado='activo').first()
    if prestamo is None:
        flash('El préstamo indicado no existe o ya fue devuelto.', 'danger')
        return redirect(url_for('bibliotecario.listado_devoluciones'))

    form = DevolucionForm()

    if form.validate_on_submit():
        multa = db.session.execute(
            text('SELECT calcular_multa(:prestamo_id)'), {'prestamo_id': prestamo.id}
        ).scalar() or Decimal('0')

        dias_retraso = max((date.today() - prestamo.fecha_limite).days, 0)
        estado_ejemplar = form.estado_ejemplar.data
        observaciones = (form.observaciones.data or '').strip() or None

        devolucion = Devolucion(
            prestamo_id=prestamo.id,
            bibliotecario_id=current_user.id,
            estado_ejemplar=estado_ejemplar,
            dias_retraso=dias_retraso,
            multa_generada=multa,
            observaciones=observaciones,
        )
        db.session.add(devolucion)
        db.session.flush()  # dispara los triggers de BD (stock, ejemplar, préstamo, auditoría)

        # El trigger de devoluciones siempre deja el ejemplar como "disponible";
        # si se reporta dañado o perdido, corregimos su estado y el stock aquí
        # y dejamos constancia en danios_perdidas.
        if estado_ejemplar in ('dañado', 'perdido'):
            ejemplar = prestamo.ejemplar
            libro = ejemplar.libro
            estado_final = 'baja' if estado_ejemplar == 'perdido' else 'dañado'

            db.session.add(DanioPerdida(
                devolucion_id=devolucion.id,
                tipo='perdida' if estado_ejemplar == 'perdido' else 'danio',
                descripcion=observaciones or f'Ejemplar reportado como {estado_ejemplar} al devolver.',
                reportado_por=current_user.id,
            ))

            ejemplar.estado = estado_final
            libro.stock_disponible -= 1
            if estado_ejemplar == 'perdido':
                libro.stock_total -= 1

            db.session.add(HistorialInventario(
                ejemplar_id=ejemplar.id,
                tipo_movimiento='baja' if estado_ejemplar == 'perdido' else 'danio',
                estado_anterior='disponible',
                estado_nuevo=estado_final,
                usuario_id=current_user.id,
                prestamo_id=prestamo.id,
                observaciones=observaciones,
            ))

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('No se pudo registrar la devolución. Intenta nuevamente.', 'danger')
            return render_template('bibliotecario/devolucion_form.html', form=form, prestamo=prestamo)

        if multa and multa > 0:
            flash(
                f'Devolución registrada. Días de retraso: {dias_retraso}. Multa generada: ${multa}.',
                'warning'
            )
        else:
            flash('Devolución registrada correctamente, sin multa.', 'success')

        return redirect(url_for('bibliotecario.listado_devoluciones'))

    return render_template('bibliotecario/devolucion_form.html', form=form, prestamo=prestamo)
