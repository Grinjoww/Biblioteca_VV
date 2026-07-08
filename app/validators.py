"""
Validadores reutilizables para datos de entrada del sistema.

Cada regla existe primero como una funcion pura de Python (es_..., sin
dependencias de Flask/WTForms) para poder usarla desde cualquier lugar:
formularios, endpoints JSON (por ejemplo la creacion de autores por AJAX)
o scripts. Encima de esas funciones se definen validadores de WTForms
listos para usar en app/forms.py.

Distincion importante entre campos de "creacion" y de "busqueda":
- Los campos que CREAN un registro nuevo (cedula al registrar un
  estudiante, ISBN al registrar un libro) llevan la validacion completa
  (digito verificador, checksum, etc.).
- Los campos que solo BUSCAN un registro ya existente (cedula/ISBN al
  registrar un prestamo) se quedan con una validacion de formato mas
  liviana, para no bloquear el acceso a datos de prueba/demo que ya
  existian antes de esta validacion mas estricta.
"""
import re
from datetime import date

from wtforms.validators import ValidationError

_PATRON_SOLO_LETRAS = re.compile(r'^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s]+$')
_PATRON_CONTIENE_LETRA = re.compile(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]')
_PATRON_CORREO = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


# ---------------------------------------------------------------------
# Funciones puras (reutilizables fuera de WTForms)
# ---------------------------------------------------------------------

def es_solo_letras(texto):
    return bool(texto) and bool(_PATRON_SOLO_LETRAS.match(texto.strip()))


def contiene_letra(texto):
    return bool(texto) and bool(_PATRON_CONTIENE_LETRA.search(texto))


def es_correo_valido(correo):
    return bool(correo) and bool(_PATRON_CORREO.match(correo.strip()))


def es_telefono_valido(telefono, longitud_min=7, longitud_max=15):
    return bool(telefono) and telefono.isdigit() and longitud_min <= len(telefono) <= longitud_max


def es_cedula_ecuatoriana_valida(cedula):
    """Cedula ecuatoriana de persona natural: 10 digitos, codigo de
    provincia 01-24 y digito verificador modulo 10."""
    if not cedula or not cedula.isdigit() or len(cedula) != 10:
        return False

    digitos = [int(c) for c in cedula]

    provincia = digitos[0] * 10 + digitos[1]
    if provincia < 1 or provincia > 24:
        return False

    if digitos[2] >= 6:
        return False

    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0
    for digito, coeficiente in zip(digitos[:9], coeficientes):
        valor = digito * coeficiente
        if valor > 9:
            valor -= 9
        suma += valor

    digito_verificador = (10 - (suma % 10)) % 10
    return digito_verificador == digitos[9]


def es_isbn13_valido(isbn):
    """ISBN-13: 13 digitos y digito verificador (pesos 1/3 alternados)."""
    if not isbn or not isbn.isdigit() or len(isbn) != 13:
        return False

    digitos = [int(c) for c in isbn]
    suma = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digitos[:12]))
    digito_verificador = (10 - (suma % 10)) % 10
    return digito_verificador == digitos[12]


def es_anio_valido(anio, minimo=1000, maximo=None):
    if maximo is None:
        maximo = date.today().year
    return minimo <= anio <= maximo


# ---------------------------------------------------------------------
# Validadores de WTForms (envuelven las funciones de arriba)
# ---------------------------------------------------------------------

class SoloLetras:
    """Solo letras (con tildes y ñ) y espacios."""

    def __init__(self, message=None):
        self.message = message or 'Solo se permiten letras y espacios.'

    def __call__(self, form, field):
        if field.data and not es_solo_letras(field.data):
            raise ValidationError(self.message)


class ContieneLetra:
    """Rechaza textos formados solo por numeros o solo por simbolos."""

    def __init__(self, message=None):
        self.message = message or 'No puede contener solo números o símbolos.'

    def __call__(self, form, field):
        if field.data and not contiene_letra(field.data):
            raise ValidationError(self.message)


class CorreoValido:
    def __init__(self, message=None):
        self.message = message or 'Ingresa un correo válido.'

    def __call__(self, form, field):
        if field.data and not es_correo_valido(field.data):
            raise ValidationError(self.message)


class TelefonoValido:
    def __init__(self, longitud_min=7, longitud_max=15, message=None):
        self.longitud_min = longitud_min
        self.longitud_max = longitud_max
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return
        if not field.data.isdigit():
            raise ValidationError(self.message or 'El teléfono solo puede contener números.')
        if not (self.longitud_min <= len(field.data) <= self.longitud_max):
            raise ValidationError(
                self.message
                or f'El teléfono debe tener entre {self.longitud_min} y {self.longitud_max} dígitos.'
            )


class CedulaEcuatorianaValida:
    """Formato (10 digitos) y digito verificador de una cedula ecuatoriana."""

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        valor = field.data or ''
        if not valor.isdigit() or len(valor) != 10:
            raise ValidationError(self.message or 'La cédula debe contener exactamente 10 dígitos.')
        if not es_cedula_ecuatoriana_valida(valor):
            raise ValidationError(self.message or 'La cédula ingresada no es válida.')


class Isbn13Valido:
    """Formato (13 digitos) y digito verificador de un ISBN-13."""

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        valor = field.data or ''
        if not valor.isdigit() or len(valor) != 13:
            raise ValidationError(self.message or 'El ISBN debe contener exactamente 13 dígitos numéricos.')
        if not es_isbn13_valido(valor):
            raise ValidationError(self.message or 'El ISBN ingresado no es válido.')


class AnioValido:
    def __init__(self, minimo=1000, maximo=None, message=None):
        self.minimo = minimo
        self.maximo = maximo
        self.message = message

    def __call__(self, form, field):
        if field.data is None:
            return
        maximo = self.maximo if self.maximo is not None else date.today().year
        if not (self.minimo <= field.data <= maximo):
            raise ValidationError(self.message or f'Ingresa un año entre {self.minimo} y {maximo}.')


class FechaNoFutura:
    def __init__(self, message=None):
        self.message = message or 'La fecha no puede ser futura.'

    def __call__(self, form, field):
        if field.data and field.data > date.today():
            raise ValidationError(self.message)


class EdadEntre:
    def __init__(self, minimo, maximo, message=None):
        self.minimo = minimo
        self.maximo = maximo
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return
        hoy = date.today()
        edad = hoy.year - field.data.year - (
            (hoy.month, hoy.day) < (field.data.month, field.data.day)
        )
        if not (self.minimo <= edad <= self.maximo):
            raise ValidationError(
                self.message or f'La edad debe estar entre {self.minimo} y {self.maximo} años.'
            )
