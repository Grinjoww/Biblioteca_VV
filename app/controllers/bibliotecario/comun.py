"""
Utilidades compartidas por los controladores de prestamos y devoluciones.

Aqui vive la logica que ambos modulos necesitan (cupos del estudiante, edad,
agrupacion de prestamos por operacion y estado derivado de la operacion) para
no duplicarla ni dejar que se desincronice entre pantallas.

Sobre las OPERACIONES: un prestamo por libro/ejemplar se conserva tal cual
(trazabilidad, fechas, multas y devolucion individuales). Los prestamos
creados en un mismo registro comparten `Prestamo.grupo_prestamo`. Los
prestamos anteriores a esa columna tienen NULL y se tratan como una operacion
de un solo libro, sin necesidad de migrar datos.
"""
from datetime import date

from app.extensions import db
from app.models import ConfiguracionSistema, Prestamo

# Un prestamo "ocupa cupo" mientras no se haya devuelto: tanto 'activo' como
# 'vencido' significan que el estudiante todavia tiene el libro.
ESTADOS_PENDIENTES = ('activo', 'vencido')


def max_prestamos_activos():
    """Limite configurable de prestamos simultaneos; None = sin limite."""
    config = ConfiguracionSistema.query.filter_by(clave='max_prestamos_activos').first()
    if config is None:
        return None
    try:
        return int(config.valor)
    except (TypeError, ValueError):
        return None


def calcular_edad(fecha_nacimiento, hoy=None):
    """Edad en anios a partir de la fecha de nacimiento (no se guarda en BD)."""
    if not fecha_nacimiento:
        return None
    hoy = hoy or date.today()
    return hoy.year - fecha_nacimiento.year - (
        (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )


def iniciales(nombres, apellidos):
    """Iniciales para el avatar de la tarjeta (el modelo no tiene fotografia)."""
    letras = ''
    for texto in (nombres, apellidos):
        texto = (texto or '').strip()
        if texto:
            letras += texto[0].upper()
    return letras or '?'


def contar_prestamos_pendientes(estudiante_id):
    return Prestamo.query.filter(
        Prestamo.estudiante_id == estudiante_id,
        Prestamo.estado.in_(ESTADOS_PENDIENTES),
    ).count()


def contar_prestamos_vencidos(estudiante_id):
    return Prestamo.query.filter_by(estudiante_id=estudiante_id, estado='vencido').count()


def calcular_cupos(estudiante_id):
    """Devuelve (activos, maximo, cupos_disponibles). maximo/cupos = None si no hay limite."""
    activos = contar_prestamos_pendientes(estudiante_id)
    maximo = max_prestamos_activos()
    if maximo is None:
        return activos, None, None
    return activos, maximo, max(maximo - activos, 0)


def clave_operacion(prestamo):
    """Identificador de la operacion: el grupo, o el propio prestamo si es NULL."""
    return prestamo.grupo_prestamo or f'P#{prestamo.id}'


def prestamos_de_operacion(prestamo):
    """Todos los prestamos de la operacion a la que pertenece `prestamo`."""
    if not prestamo.grupo_prestamo:
        return [prestamo]
    return (
        Prestamo.query.filter_by(grupo_prestamo=prestamo.grupo_prestamo)
        .order_by(Prestamo.id)
        .all()
    )


def resumen_operacion(prestamos, hoy=None):
    """
    Estado DERIVADO de una operacion a partir de sus prestamos individuales.

    No se guarda en BD ninguna columna de "devolucion parcial": se calcula
    contando cuantos prestamos del grupo ya tienen estado 'devuelto'.
    """
    hoy = hoy or date.today()
    prestamos = sorted(prestamos, key=lambda p: p.id)
    primero = prestamos[0]

    total = len(prestamos)
    devueltos = sum(1 for p in prestamos if p.estado == 'devuelto')
    pendientes = total - devueltos
    vencida = any(p.estado != 'devuelto' and p.fecha_limite < hoy for p in prestamos)

    if pendientes == 0:
        estado, badge = 'Devolución completa', 'success'
    elif devueltos > 0:
        estado, badge = 'Devolución parcial', 'warning'
    elif vencida:
        estado, badge = 'Vencido', 'danger'
    else:
        estado, badge = 'Activo', 'primary'

    fechas_limite = [p.fecha_limite for p in prestamos if p.estado != 'devuelto']

    return {
        'clave': clave_operacion(primero),
        'codigo': primero.grupo_prestamo or primero.codigo_prestamo,
        'es_grupo': bool(primero.grupo_prestamo),
        'representante_id': primero.id,
        'estudiante': primero.estudiante,
        'prestamos': prestamos,
        'total': total,
        'devueltos': devueltos,
        'pendientes': pendientes,
        'vencida': vencida,
        'estado': estado,
        'estado_badge': badge,
        'fecha_prestamo': primero.fecha_prestamo,
        'fecha_limite': min(fechas_limite) if fechas_limite else max(p.fecha_limite for p in prestamos),
    }


def agrupar_prestamos(prestamos_base, hoy=None):
    """
    Agrupa una lista de prestamos en operaciones, conservando el orden recibido.

    Para los prestamos con grupo se cargan TAMBIEN los hermanos que no estaban
    en la lista base (p. ej. los ya devueltos), para que el conteo de
    devueltos/pendientes de la operacion sea correcto.
    """
    grupos = {p.grupo_prestamo for p in prestamos_base if p.grupo_prestamo}
    hermanos = {}
    if grupos:
        for prestamo in Prestamo.query.filter(Prestamo.grupo_prestamo.in_(grupos)).all():
            hermanos.setdefault(prestamo.grupo_prestamo, []).append(prestamo)

    operaciones = []
    vistos = set()
    for prestamo in prestamos_base:
        clave = clave_operacion(prestamo)
        if clave in vistos:
            continue
        vistos.add(clave)
        del_grupo = hermanos.get(prestamo.grupo_prestamo) if prestamo.grupo_prestamo else None
        operaciones.append(resumen_operacion(del_grupo or [prestamo], hoy=hoy))
    return operaciones


def generar_codigo_grupo():
    """Siguiente codigo de operacion del anio en curso: 'GRP-<anio>-0001'."""
    anio = date.today().year
    prefijo = f'GRP-{anio}-'
    ultimo = (
        db.session.query(db.func.max(Prestamo.grupo_prestamo))
        .filter(Prestamo.grupo_prestamo.like(f'{prefijo}%'))
        .scalar()
    )
    siguiente = 1
    if ultimo:
        try:
            siguiente = int(ultimo[len(prefijo):]) + 1
        except (TypeError, ValueError):
            siguiente = 1
    return f'{prefijo}{siguiente:04d}'
