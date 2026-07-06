from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(message='El usuario es obligatorio')])
    password = PasswordField('Contraseña', validators=[DataRequired(message='La contraseña es obligatoria')])
    submit = SubmitField('Ingresar')