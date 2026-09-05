"""
Helpers de paginacion y filtros para los listados.

Todos los listados paginan y filtran EN BACKEND (query.filter/order_by/paginate);
aqui solo se centraliza la lectura segura de los parametros GET para que un
`?page=abc` o un `?estado=<script>` no reviente la pagina ni cambie la consulta.
"""

# Registros por pagina en los listados principales del bibliotecario.
POR_PAGINA = 10


def pagina_actual(request):
    """Numero de pagina pedido por GET. Cualquier valor invalido -> pagina 1."""
    pagina = request.args.get('page', type=int)
    if pagina is None or pagina < 1:
        return 1
    return pagina


def texto_filtro(request, nombre, maximo=100):
    """Lee un filtro de texto libre, recortado a un largo razonable."""
    return (request.args.get(nombre) or '').strip()[:maximo]


def opcion_filtro(request, nombre, permitidas, por_defecto=''):
    """Lee un filtro de lista cerrada; si no esta en `permitidas`, usa el valor por defecto."""
    valor = (request.args.get(nombre) or '').strip()
    return valor if valor in permitidas else por_defecto


def entero_filtro(request, nombre):
    """Lee un filtro numerico (ids de carrera/categoria). Invalido o <= 0 -> None."""
    valor = request.args.get(nombre, type=int)
    return valor if valor and valor > 0 else None


def id_nuevo(request):
    """
    Id del registro recien creado, que llega por querystring tras el redirect.

    Sirve para pintar el badge "Nuevo" sin guardar nada en la base de datos:
    en cuanto el usuario navega (otra pagina, otro filtro) el parametro
    desaparece y el indicador tambien.
    """
    return request.args.get('nuevo', type=int)


def argumentos_activos(**filtros):
    """
    Filtros vigentes, listos para reinyectarlos en los enlaces de paginacion.

    Se descartan los vacios para no arrastrar `?q=&estado=` en cada URL. Nunca
    incluye `page` ni `nuevo`: la pagina la pone el propio enlace y el badge
    "Nuevo" debe desaparecer al navegar.
    """
    return {clave: valor for clave, valor in filtros.items() if valor not in (None, '', 0)}
