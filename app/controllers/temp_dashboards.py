from flask import Blueprint
from flask_login import login_required, current_user
from app.controllers.decoradores import requiere_rol

gerente_bp = Blueprint('gerente', __name__, url_prefix='/gerente')


@gerente_bp.route('/dashboard')
@login_required
@requiere_rol('gerente')
def dashboard():
    return f'Bienvenido gerente: {current_user.username}'