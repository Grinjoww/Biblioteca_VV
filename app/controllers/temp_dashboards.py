from flask import Blueprint
from flask_login import login_required, current_user
from app.controllers.decoradores import requiere_rol

estudiante_bp = Blueprint('estudiante', __name__, url_prefix='/estudiante')
gerente_bp = Blueprint('gerente', __name__, url_prefix='/gerente')


@estudiante_bp.route('/catalogo')
@login_required
@requiere_rol('estudiante')
def catalogo():
    return f'Bienvenido estudiante: {current_user.username}'


@gerente_bp.route('/dashboard')
@login_required
@requiere_rol('gerente')
def dashboard():
    return f'Bienvenido gerente: {current_user.username}'