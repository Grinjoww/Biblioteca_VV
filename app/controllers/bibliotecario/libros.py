from datetime import date

from flask import jsonify, redirect, render_template, request, url_for, flash
from flask_login import login_required

from app.controllers.bibliotecario import bibliotecario_bp
from app.controllers.decoradores import requiere_rol
from app.extensions import db
from app.forms import LibroForm
from app.models import Autor, CategoriaLibro, Editorial, Ejemplar, Libro, LibroAutor


def _siguiente_numero_ejemplar():
    resultado = db.session.execute(
        db.text(
            "SELECT COALESCE(MAX(CAST(SUBSTRING(codigo_ejemplar FROM 4) AS INTEGER)), 0) "
            "FROM ejemplares WHERE codigo_ejemplar LIKE 'EJ-%'"
        )
    ).scalar()
    return resultado or 0


def _obtener_o_crear_editorial(nombre):
    nombre = nombre.strip()
    editorial = Editorial.query.filter(db.func.lower(Editorial.nombre) == nombre.lower()).first()
    if editorial:
        return editorial

    editorial = Editorial(nombre=nombre)
    db.session.add(editorial)
    db.session.flush()
    return editorial


@bibliotecario_bp.route('/libros')
@login_required
@requiere_rol('bibliotecario')
def listado_libros():
    libros = Libro.query.order_by(Libro.titulo).all()
    return render_template('bibliotecario/libros_lista.html', libros=libros)


@bibliotecario_bp.route('/libros/nuevo', methods=['GET', 'POST'])
@login_required
@requiere_rol('bibliotecario')
def nuevo_libro():
    form = LibroForm()
    form.categoria_id.choices = [(0, '-- Selecciona una categoría --')] + [
        (categoria.id, categoria.nombre)
        for categoria in CategoriaLibro.query.order_by(CategoriaLibro.nombre)
    ]
    editoriales = Editorial.query.order_by(Editorial.nombre).all()

    if form.validate_on_submit():
        autores_ids = sorted({
            int(valor) for valor in (form.autores_ids.data or '').split(',')
            if valor.strip().isdigit()
        })

        if not autores_ids:
            flash('Debes agregar al menos un autor.', 'danger')
            return render_template('bibliotecario/libros_nuevo.html', form=form, editoriales=editoriales)

        autores_validos = Autor.query.filter(Autor.id.in_(autores_ids)).count()
        if autores_validos != len(autores_ids):
            flash('Uno o más autores seleccionados no son válidos.', 'danger')
            return render_template('bibliotecario/libros_nuevo.html', form=form, editoriales=editoriales)

        if Libro.query.filter_by(isbn=form.isbn.data).first():
            flash('Ya existe un libro registrado con ese ISBN.', 'danger')
            return render_template('bibliotecario/libros_nuevo.html', form=form, editoriales=editoriales)

        editorial = _obtener_o_crear_editorial(form.editorial_nombre.data)

        libro = Libro(
            isbn=form.isbn.data.strip(),
            titulo=form.titulo.data.strip(),
            subtitulo=(form.subtitulo.data or '').strip() or None,
            editorial_id=editorial.id,
            categoria_id=form.categoria_id.data,
            anio_publicacion=form.anio_publicacion.data,
            edicion=(form.edicion.data or '').strip() or None,
            num_paginas=form.num_paginas.data,
            idioma=form.idioma.data.strip(),
            stock_total=form.stock_inicial.data,
            stock_disponible=form.stock_inicial.data,
        )
        db.session.add(libro)
        db.session.flush()

        for autor_id in autores_ids:
            db.session.add(LibroAutor(libro_id=libro.id, autor_id=autor_id))

        siguiente = _siguiente_numero_ejemplar()
        hoy = date.today()
        for i in range(1, form.stock_inicial.data + 1):
            codigo = f'EJ-{siguiente + i:06d}'
            db.session.add(Ejemplar(
                libro_id=libro.id,
                codigo_ejemplar=codigo,
                fecha_adquisicion=hoy,
            ))

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('No se pudo registrar el libro. Verifica los datos ingresados.', 'danger')
            return render_template('bibliotecario/libros_nuevo.html', form=form, editoriales=editoriales)

        flash(
            f'Libro "{libro.titulo}" registrado con {form.stock_inicial.data} ejemplar(es).',
            'success'
        )
        return redirect(url_for('bibliotecario.listado_libros'))

    return render_template('bibliotecario/libros_nuevo.html', form=form, editoriales=editoriales)


@bibliotecario_bp.route('/api/libros/buscar')
@login_required
@requiere_rol('bibliotecario')
def api_buscar_libros():
    termino = (request.args.get('q') or '').strip()
    consulta = Libro.query
    if termino:
        patron = f'%{termino}%'
        consulta = consulta.filter(
            db.or_(Libro.titulo.ilike(patron), Libro.isbn.ilike(patron))
        )
    libros = consulta.order_by(Libro.titulo).limit(30).all()

    return jsonify([
        {
            'id': libro.id,
            'titulo': libro.titulo,
            'isbn': libro.isbn,
            'editorial': libro.editorial.nombre if libro.editorial else '',
            'categoria': libro.categoria.nombre if libro.categoria else '',
            'stock_disponible': libro.stock_disponible,
            'stock_total': libro.stock_total,
        }
        for libro in libros
    ])


@bibliotecario_bp.route('/api/autores/buscar')
@login_required
@requiere_rol('bibliotecario')
def api_buscar_autores():
    termino = (request.args.get('q') or '').strip()
    if len(termino) < 2:
        return jsonify([])

    patron = f'%{termino}%'
    autores = (
        Autor.query.filter(
            db.or_(Autor.nombres.ilike(patron), Autor.apellidos.ilike(patron))
        )
        .order_by(Autor.apellidos)
        .limit(10)
        .all()
    )
    return jsonify([
        {'id': autor.id, 'nombre': f'{autor.nombres} {autor.apellidos}'}
        for autor in autores
    ])


@bibliotecario_bp.route('/api/autores', methods=['POST'])
@login_required
@requiere_rol('bibliotecario')
def api_crear_autor():
    datos = request.get_json(silent=True) or {}
    nombres = (datos.get('nombres') or '').strip()
    apellidos = (datos.get('apellidos') or '').strip()

    if not nombres or not apellidos:
        return jsonify({'error': 'Nombres y apellidos son obligatorios.'}), 400

    autor_existente = Autor.query.filter(
        db.func.lower(Autor.nombres) == nombres.lower(),
        db.func.lower(Autor.apellidos) == apellidos.lower(),
    ).first()
    if autor_existente:
        return jsonify({
            'id': autor_existente.id,
            'nombre': f'{autor_existente.nombres} {autor_existente.apellidos}',
        })

    autor = Autor(nombres=nombres, apellidos=apellidos)
    db.session.add(autor)
    db.session.commit()

    return jsonify({'id': autor.id, 'nombre': f'{autor.nombres} {autor.apellidos}'}), 201
