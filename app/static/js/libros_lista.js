document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('buscador-libros');
    const cuerpo = document.getElementById('cuerpo-tabla-libros');
    if (!input || !cuerpo) return;

    let temporizador = null;

    function escaparHtml(texto) {
        const div = document.createElement('div');
        div.textContent = texto == null ? '' : texto;
        return div.innerHTML;
    }

    function renderFilas(libros) {
        if (!libros.length) {
            cuerpo.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">No se encontraron libros.</td></tr>';
            return;
        }
        cuerpo.innerHTML = libros.map(function (libro) {
            return (
                '<tr>' +
                '<td>' + escaparHtml(libro.titulo) + '</td>' +
                '<td>' + escaparHtml(libro.isbn) + '</td>' +
                '<td>' + escaparHtml(libro.editorial || '-') + '</td>' +
                '<td>' + escaparHtml(libro.categoria || '-') + '</td>' +
                '<td>' + libro.stock_disponible + ' / ' + libro.stock_total + '</td>' +
                '</tr>'
            );
        }).join('');
    }

    function buscar() {
        const termino = input.value.trim();
        fetch('/bibliotecario/api/libros/buscar?q=' + encodeURIComponent(termino))
            .then(function (resp) { return resp.json(); })
            .then(renderFilas)
            .catch(function () {
                cuerpo.innerHTML = '<tr><td colspan="5" class="text-center text-danger py-3">Error al buscar libros.</td></tr>';
            });
    }

    input.addEventListener('input', function () {
        clearTimeout(temporizador);
        temporizador = setTimeout(buscar, 300);
    });
});
