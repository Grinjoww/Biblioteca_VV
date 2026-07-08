"""
Pruebas de autenticacion: login correcto por cada rol del sistema.
"""


def test_login_bibliotecario_exitoso(login, usuario_bibliotecario):
    respuesta = login('test_bibliotecario', 'ClaveSegura123')

    assert respuesta.status_code == 302
    assert respuesta.headers['Location'] == '/bibliotecario/inicio'


def test_login_estudiante_exitoso(login, usuario_estudiante):
    respuesta = login('1234567899', 'ClaveSegura123')

    assert respuesta.status_code == 302
    assert respuesta.headers['Location'] == '/estudiante/catalogo'


def test_login_gerente_exitoso(login, usuario_gerente):
    respuesta = login('test_gerente', 'ClaveSegura123')

    assert respuesta.status_code == 302
    assert respuesta.headers['Location'] == '/gerente/dashboard'


def test_login_credenciales_invalidas(login, usuario_bibliotecario):
    respuesta = login('test_bibliotecario', 'clave-incorrecta')

    # No debe redirigir: se re-renderiza el formulario con el mensaje de error.
    assert respuesta.status_code == 200
    assert 'incorrectos' in respuesta.get_data(as_text=True)
