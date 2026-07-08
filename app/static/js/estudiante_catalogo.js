document.addEventListener('DOMContentLoaded', function () {
    const inputBuscar = document.getElementById('buscador-catalogo');
    const selectCategoria = document.getElementById('filtro-categoria');
    const contenedor = document.getElementById('contenedor-libros');
    if (!inputBuscar || !selectCategoria || !contenedor) return;

    let temporizador = null;

    function crearTarjeta(libro) {
        const col = document.createElement('div');
        col.className = 'col-md-4';

        const card = document.createElement('div');
        card.className = 'card h-100 shadow-sm';

        const body = document.createElement('div');
        body.className = 'card-body';

        const titulo = document.createElement('h5');
        titulo.className = 'card-title';
        titulo.textContent = libro.titulo;

        const categoria = document.createElement('h6');
        categoria.className = 'card-subtitle mb-2 text-muted';
        categoria.textContent = libro.categoria || '-';

        const editorial = document.createElement('p');
        editorial.className = 'card-text small';
        editorial.textContent = 'Editorial: ' + (libro.editorial || '-');

        const stockParrafo = document.createElement('p');
        stockParrafo.className = 'card-text';
        const badge = document.createElement('span');
        badge.className = 'badge ' + (libro.stock_disponible > 0 ? 'text-bg-success' : 'text-bg-secondary');
        badge.textContent = libro.stock_disponible + ' disponible(s)';
        stockParrafo.appendChild(badge);

        const enlace = document.createElement('a');
        enlace.className = 'btn btn-outline-primary btn-sm';
        enlace.href = '/estudiante/catalogo/' + encodeURIComponent(libro.isbn);
        enlace.textContent = 'Ver detalle';

        body.appendChild(titulo);
        body.appendChild(categoria);
        body.appendChild(editorial);
        body.appendChild(stockParrafo);
        body.appendChild(enlace);
        card.appendChild(body);
        col.appendChild(card);
        return col;
    }

    function renderLibros(libros) {
        contenedor.innerHTML = '';
        if (!libros.length) {
            const vacio = document.createElement('div');
            vacio.className = 'col-12';
            const mensaje = document.createElement('p');
            mensaje.className = 'text-muted text-center py-4';
            mensaje.textContent = 'No se encontraron libros con esos criterios.';
            vacio.appendChild(mensaje);
            contenedor.appendChild(vacio);
            return;
        }
        libros.forEach(function (libro) {
            contenedor.appendChild(crearTarjeta(libro));
        });
    }

    function buscar() {
        const termino = inputBuscar.value.trim();
        const categoriaId = selectCategoria.value;
        const params = new URLSearchParams();
        if (termino) params.set('q', termino);
        if (categoriaId) params.set('categoria_id', categoriaId);

        fetch('/estudiante/api/catalogo/buscar?' + params.toString())
            .then(function (resp) { return resp.json(); })
            .then(renderLibros)
            .catch(function () {
                contenedor.innerHTML = '';
                const error = document.createElement('div');
                error.className = 'col-12';
                const mensaje = document.createElement('p');
                mensaje.className = 'text-danger text-center py-4';
                mensaje.textContent = 'Error al buscar libros.';
                error.appendChild(mensaje);
                contenedor.appendChild(error);
            });
    }

    inputBuscar.addEventListener('input', function () {
        clearTimeout(temporizador);
        temporizador = setTimeout(buscar, 300);
    });

    selectCategoria.addEventListener('change', buscar);
});
