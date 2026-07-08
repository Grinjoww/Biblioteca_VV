"""
Pruebas de validacion de formularios.

Confirman que datos con formato invalido son rechazados por los
validadores del servidor (WTForms) antes de intentar escribir en la
base de datos o de llamar a validar_prestamo()/generar_codigo_prestamo().
No dependen de database/setup.sql.
"""


def test_registrar_libro_isbn_invalido(client, login, usuario_bibliotecario):
    login('test_bibliotecario', 'ClaveSegura123')

    respuesta = client.post('/bibliotecario/libros/nuevo', data={
        'isbn': '123',  # debe tener 13 digitos
        'titulo': 'Libro de prueba',
        'editorial_nombre': 'Editorial de prueba',
        'categoria_id': '0',
        'idioma': 'Español',
        'stock_inicial': '1',
        'autores_ids': '',
    })

    # No redirige: el formulario se vuelve a mostrar con el error.
    assert respuesta.status_code == 200
    assert '13 dígitos' in respuesta.get_data(as_text=True)


def test_registrar_prestamo_cedula_invalida(client, login, usuario_bibliotecario):
    login('test_bibliotecario', 'ClaveSegura123')

    respuesta = client.post('/bibliotecario/prestamos/nuevo', data={
        'cedula': '123',  # debe tener 10 digitos
        'isbn': '9789978000000',
        'observaciones': '',
    })

    assert respuesta.status_code == 200
    assert '10 dígitos' in respuesta.get_data(as_text=True)
