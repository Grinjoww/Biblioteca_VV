from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, SelectField, IntegerField,
    DateField, TextAreaField, HiddenField
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Regexp, EqualTo


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
    isbn = StringField('ISBN', validators=[
        DataRequired(),
        Regexp(r'^[0-9]{13}$', message='El ISBN debe tener 13 dígitos numéricos')
    ])
    titulo = StringField('Título', validators=[DataRequired(), Length(max=255)])
    subtitulo = StringField('Subtítulo', validators=[Optional(), Length(max=255)])
    editorial_nombre = StringField('Editorial', validators=[DataRequired(), Length(max=150)])
    categoria_id = SelectField(
        'Categoría', coerce=int,
        validators=[NumberRange(min=1, message='Selecciona una categoría')]
    )
    anio_publicacion = IntegerField('Año de publicación', validators=[Optional(), NumberRange(min=1800)])
    edicion = StringField('Edición', validators=[Optional(), Length(max=20)])
    num_paginas = IntegerField('Número de páginas', validators=[Optional(), NumberRange(min=1)])
    idioma = StringField('Idioma', default='Español', validators=[DataRequired(), Length(max=30)])
    stock_inicial = IntegerField(
        'Stock inicial (ejemplares)',
        validators=[DataRequired(), NumberRange(min=1, max=200, message='Ingresa una cantidad entre 1 y 200')]
    )
    autores_ids = HiddenField('Autores')
    submit = SubmitField('Registrar libro')


class EstudianteForm(FlaskForm):
    cedula = StringField('Cédula', validators=[
        DataRequired(),
        Regexp(r'^[0-9]{10}$', message='La cédula debe tener 10 dígitos')
    ])
    nombres = StringField('Nombres', validators=[DataRequired(), Length(max=100)])
    apellidos = StringField('Apellidos', validators=[DataRequired(), Length(max=100)])
    correo = StringField('Correo electrónico', validators=[
        DataRequired(),
        Regexp(r'^[^@]+@[^@]+\.[^@]+$', message='Ingresa un correo válido'),
        Length(max=150),
    ])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=15)])
    carrera_id = SelectField(
        'Carrera', coerce=int,
        validators=[NumberRange(min=1, message='Selecciona una carrera')]
    )
    fecha_nacimiento = DateField('Fecha de nacimiento', validators=[Optional()])
    genero = SelectField(
        'Género',
        choices=[('', 'Prefiero no decir'), ('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')],
        validators=[Optional()],
    )
    submit = SubmitField('Registrar estudiante')


class PrestamoForm(FlaskForm):
    cedula = StringField('Cédula del estudiante', validators=[
        DataRequired(),
        Regexp(r'^[0-9]{10}$', message='La cédula debe tener 10 dígitos')
    ])
    isbn = StringField('ISBN del libro', validators=[
        DataRequired(),
        Regexp(r'^[0-9]{13}$', message='El ISBN debe tener 13 dígitos numéricos')
    ])
    observaciones = TextAreaField('Observaciones', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Registrar préstamo')


class DevolucionForm(FlaskForm):
    estado_ejemplar = SelectField(
        'Estado del ejemplar',
        choices=[('bueno', 'Bueno'), ('dañado', 'Dañado'), ('perdido', 'Perdido')],
        validators=[DataRequired()],
    )
    observaciones = TextAreaField('Observaciones', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Registrar devolución')
