document.addEventListener('DOMContentLoaded', function () {
    const inputCedula = document.getElementById('cedula');
    const inputIsbn = document.getElementById('isbn');
    const contenedor = document.getElementById('validacion-prestamo');
    if (!inputCedula || !inputIsbn || !contenedor) return;

    let temporizador = null;

    function escaparHtml(texto) {
        const div = document.createElement('div');
        div.textContent = texto == null ? '' : texto;
        return div.innerHTML;
    }

    function validar() {
        const cedula = inputCedula.value.trim();
        const isbn = inputIsbn.value.trim();

        if (cedula.length !== 10 || isbn.length !== 13) {
            contenedor.classList.add('d-none');
            return;
        }

        fetch('/bibliotecario/api/prestamos/validar?cedula=' + encodeURIComponent(cedula) + '&isbn=' + encodeURIComponent(isbn))
            .then(function (resp) { return resp.json(); })
            .then(function (datos) {
                contenedor.classList.remove('d-none', 'alert-success', 'alert-danger');
                if (datos.codigo_resultado === 0) {
                    contenedor.classList.add('alert-success');
                    contenedor.innerHTML = escaparHtml(datos.mensaje) + ' · Estudiante: ' + escaparHtml(datos.estudiante) + ' · Libro: ' + escaparHtml(datos.libro);
                } else {
                    contenedor.classList.add('alert-danger');
                    contenedor.textContent = datos.mensaje;
                }
            });
    }

    [inputCedula, inputIsbn].forEach(function (campo) {
        campo.addEventListener('input', function () {
            clearTimeout(temporizador);
            temporizador = setTimeout(validar, 350);
        });
    });
});
