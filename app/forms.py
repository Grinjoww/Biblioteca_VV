from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileSize
from wtforms import (
    StringField, PasswordField, SubmitField, SelectField, IntegerField,
    DateField, TextAreaField, HiddenField
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Regexp, EqualTo

from app.portadas import EXTENSIONES_PERMITIDAS, MENSAJE_FORMATO_INVALIDO, MENSAJE_TAMANO_INVALIDO, TAMANO_MAXIMO_BYTES
from app.validators import (
    AnioValido, CedulaEcuatorianaValida, ContieneLetra, CorreoValido,
    EdadEntre, FechaNoFutura, Isbn13Valido, SoloLetras, TelefonoValido,
)


class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(message='El usuario es obligatorio')])
    password = PasswordField('Contraseña', validators=[DataRequired(message='La contraseña es obligatoria')])
    submit = SubmitField('Ingresar')


class CambiarPasswordForm(FlaskForm):
    password_actual = PasswordField('Contraseña actual', validators=[DataRequired()])
    password_nueva = PasswordField(
        'Nueva contraseña',
        validators=[DataRequired(), Length(min=6, message='Debe tener al menos 6 caracteres')]
    )
    password_confirmar = PasswordField(
        'Confirmar nueva contraseña',
        validators=[DataRequired(), EqualTo('password_nueva', message='Las contraseñas no coinciden')]
    )
    submit = SubmitField('Cambiar contraseña')


class LibroForm(FlaskForm):
    # ISBN: campo de CREACION de un libro nuevo -> validacion completa
    # (formato + digito verificador real de ISBN-13).
    isbn = StringField('ISBN', validators=[
        DataRequired(message='El ISBN es obligatorio.'),
        Isbn13Valido(),
    ])
    titulo = StringField('Título', validators=[
        DataRequired(message='El título es obligatorio.'),
        Length(min=2, max=255, message='El título debe tener entre 2 y 255 caracteres.'),
        ContieneLetra(message='El título no puede contener solo números o símbolos.'),
    ])
    subtitulo = StringField('Subtítulo', validators=[Optional(), Length(max=255)])
    editorial_nombre = StringField('Editorial', validators=[
        DataRequired(message='La editorial es obligatoria.'),
        Length(min=2, max=150, message='La editorial debe tener entre 2 y 150 caracteres.'),
        ContieneLetra(message='La editorial no puede contener solo números o símbolos.'),
    ])
    categoria_id = SelectField(
        'Categoría', coerce=int,
        validators=[NumberRange(min=1, message='Selecciona una categoría.')]
    )
    anio_publicacion = IntegerField('Año de publicación', validators=[
        Optional(),
        AnioValido(minimo=1000, message='Ingresa un año de publicación válido (entre 1000 y el año actual).'),
    ])
    edicion = StringField('Edición', validators=[Optional(), Length(max=20)])
    num_paginas = IntegerField('Número de páginas', validators=[
        Optional(),
        NumberRange(min=1, message='El número de páginas debe ser mayor a 0.'),
    ])
    idioma = StringField('Idioma', default='Español', validators=[
        DataRequired(message='El idioma es obligatorio.'),
        Length(max=30),
        SoloLetras(message='El idioma solo puede contener letras y espacios.'),
    ])
    stock_inicial = IntegerField(
        'Stock inicial (ejemplares)',
        validators=[
            DataRequired(message='El stock inicial es obligatorio.'),
            NumberRange(min=1, max=200, message='Ingresa una cantidad entre 1 y 200.'),
        ]
    )
    resumen = TextAreaField('Resumen / Sinopsis', validators=[
        Optional(),
        Length(max=5000, message='El resumen no puede superar los 5000 caracteres.'),
    ])
    autores_ids = HiddenField('Autores')
    portada = FileField('Portada del libro (opcional)', validators=[
        Optional(),
        FileAllowed(sorted(EXTENSIONES_PERMITIDAS), message=MENSAJE_FORMATO_INVALIDO),
        FileSize(max_size=TAMANO_MAXIMO_BYTES, message=MENSAJE_TAMANO_INVALIDO),
    ])
    submit = SubmitField('Registrar libro')


class EstudianteForm(FlaskForm):
    # Cedula: campo de CREACION de un estudiante nuevo -> validacion
    # completa (formato + digito verificador real).
    cedula = StringField('Cédula', validators=[
        DataRequired(message='La cédula es obligatoria.'),
        CedulaEcuatorianaValida(),
    ])
    nombres = StringField('Nombres', validators=[
        DataRequired(message='Los nombres son obligatorios.'),
        Length(min=2, max=100, message='Los nombres deben tener entre 2 y 100 caracteres.'),
        SoloLetras(message='Los nombres solo pueden contener letras y espacios.'),
    ])
    apellidos = StringField('Apellidos', validators=[
        DataRequired(message='Los apellidos son obligatorios.'),
        Length(min=2, max=100, message='Los apellidos deben tener entre 2 y 100 caracteres.'),
        SoloLetras(message='Los apellidos solo pueden contener letras y espacios.'),
    ])
    correo = StringField('Correo electrónico', validators=[
        DataRequired(message='El correo es obligatorio.'),
        CorreoValido(),
        Length(max=150),
    ])
    telefono = StringField('Teléfono', validators=[
        Optional(),
        TelefonoValido(),
    ])
    carrera_id = SelectField(
        'Carrera', coerce=int,
        validators=[NumberRange(min=1, message='Selecciona una carrera.')]
    )
    fecha_nacimiento = DateField('Fecha de nacimiento', validators=[
        DataRequired(message='La fecha de nacimiento es obligatoria.'),
        FechaNoFutura(message='La fecha de nacimiento no puede ser futura.'),
        EdadEntre(15, 100, message='El estudiante debe tener entre 15 y 100 años.'),
    ])
    genero = SelectField(
        'Género',
        choices=[('', 'Prefiero no decir'), ('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')],
        validators=[Optional()],
    )
    submit = SubmitField('Registrar estudiante')


class PrestamoForm(FlaskForm):
    # Cedula aqui es un campo de BUSQUEDA de un estudiante que ya debe existir
    # (no se crea aqui), por eso se valida solo el formato y no el digito
    # verificador: exigirlo bloquearia prestamos para estudiantes de
    # prueba/demo registrados antes de esa regla.
    cedula = StringField('Cédula del estudiante', validators=[
        DataRequired(message='La cédula es obligatoria.'),
        Regexp(r'^[0-9]{10}$', message='La cédula debe contener exactamente 10 dígitos.')
    ])
    # Lista de ISBN seleccionados para este prestamo, separados por coma. La
    # arma la pantalla al ir agregando libros; el contenido se revalida
    # completo en el servidor (existencia, stock, duplicados y cupos).
    isbns = HiddenField('Libros a prestar')
    observaciones = TextAreaField('Observaciones', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Registrar préstamo')


class DevolucionForm(FlaskForm):
    estado_ejemplar = SelectField(
        'Estado del ejemplar',
        choices=[('bueno', 'Bueno'), ('dañado', 'Dañado'), ('perdido', 'Perdido')],
        validators=[DataRequired(message='Selecciona el estado del ejemplar.')],
    )
    observaciones = TextAreaField('Observaciones', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Registrar devolución')


class AccionUsuarioForm(FlaskForm):
    """
    Acciones administrativas del gerente sobre una cuenta (activar/desactivar,
    restablecer contraseña, cambiar rol). Solo aporta el token CSRF: el destino
    va en la URL y el rol nuevo se lee de request.form contra una lista blanca.
    Todas se ejecutan por POST, nunca por GET.
    """
    submit = SubmitField('Confirmar')


class DevolucionLoteForm(FlaskForm):
    """
    Devolucion de varios libros de una misma operacion.

    Los campos por libro (casilla, estado y observacion) son dinamicos: se
    generan en la plantilla a partir de los prestamos pendientes y se leen
    desde request.form en el controlador. Este form aporta el token CSRF y el
    boton, que es lo unico fijo.
    """
    submit = SubmitField('Registrar devolución seleccionada')
