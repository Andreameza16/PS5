from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Blueprint
from flask_mail import Mail, Message
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
from extensions import db
import os
import requests

# Cargar las variables .env
load_dotenv()

app = Flask(__name__)
# Clave secreta
app.secret_key = os.getenv("SECRET_KEY")

# Configuracion de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  

db.init_app(app)

# importar modelos
from models import Usuario, Producto, Carrito, CarritoItem, Pedido, PedidoItem

# Configuracion de flask mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_USERNAME")

mail = Mail(app)


#RUTAS

@app.route('/')
def index():
    productos = Producto.query.all()
    usuario = None
    if "usuario_id" in session:
        usuario = Usuario.query.get(session["usuario_id"])

    return render_template('index.html', productos=productos, usuario=usuario)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.password_hash, password):
            session["usuario_id"] = usuario.id
            return redirect(url_for("index"))

        return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]

        existe = Usuario.query.filter_by(email=email).first()
        if existe:
            return render_template("register.html", error="Este correo ya está registrado.")

        nuevo = Usuario(
            nombre=nombre,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(nuevo)
        db.session.commit()

        session["usuario_id"] = nuevo.id
        return redirect(url_for("index"))

    return render_template("register.html")

@app.route("/perfil")
def perfil():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario = Usuario.query.get(session["usuario_id"])
    return render_template("perfil.html", usuario=usuario)

@app.route("/perfil/editar", methods=["GET", "POST"])
def editar_perfil():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario = Usuario.query.get(session["usuario_id"])

    if request.method == "POST":
        usuario.nombre = request.form["nombre"]
        usuario.email = request.form["email"]
        usuario.telefono = request.form["telefono"]
        usuario.direccion = request.form["direccion"]

        db.session.commit()

        return redirect(url_for("perfil"))

    return render_template("editar_perfil.html", usuario=usuario)

#PANEL DE ADMINISTRADOR
@app.route("/admin")
def admin_panel():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario = Usuario.query.get(session["usuario_id"])

    if usuario.rol != "admin":
        return redirect(url_for("index"))

    return render_template("admin.html", usuario=usuario)

#CRUD PRODUCTOS
@app.route("/admin/productos")
def admin_productos():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario = Usuario.query.get(session["usuario_id"])
    if usuario.rol != "admin":
        return redirect(url_for("index"))

    productos = Producto.query.all()
    return render_template("admin_productos.html", productos=productos, usuario=usuario)

#PRODUCTO NUEVO
@app.route("/admin/productos/nuevo", methods=["GET", "POST"])
def admin_producto_nuevo():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario = Usuario.query.get(session["usuario_id"])
    if usuario.rol != "admin":
        return redirect(url_for("index"))

    if request.method == "POST":
        nombre = request.form["nombre"]
        sku = request.form["sku"]
        descripcion = request.form["descripcion"]
        precio = request.form["precio"]
        stock = request.form["stock"]
        imagen_url = request.form["imagen_url"]

        nuevo = Producto(
            nombre=nombre,
            sku=sku,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            imagen_url=imagen_url
        )

        db.session.add(nuevo)
        db.session.commit()

        return redirect("/admin/productos")

    return render_template("admin_producto_form.html", modo="nuevo")

#EDITAR PRODUCTO
@app.route("/admin/productos/editar/<int:id>", methods=["GET","POST"])
def admin_producto_editar(id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario = Usuario.query.get(session["usuario_id"])
    if usuario.rol != "admin":
        return redirect(url_for("index"))

    producto = Producto.query.get(id)

    if request.method == "POST":
        producto.nombre = request.form["nombre"]
        producto.sku = request.form["sku"]
        producto.descripcion = request.form["descripcion"]
        producto.precio = request.form["precio"]
        producto.stock = request.form["stock"]
        producto.imagen_url = request.form["imagen_url"]

        db.session.commit()
        return redirect("/admin/productos")

    return render_template("admin_producto_form.html", producto=producto, modo="editar")

#ELIMINAR PRODUCTO
@app.route("/admin/productos/eliminar/<int:id>")
def admin_producto_eliminar(id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario = Usuario.query.get(session["usuario_id"])
    if usuario.rol != "admin":
        return redirect(url_for("index"))

    producto = Producto.query.get(id)
    db.session.delete(producto)
    db.session.commit()

    return redirect("/admin/productos")

#CRUD USUARIOS
@app.route("/admin/usuarios")
def admin_usuarios():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    admin = Usuario.query.get(session["usuario_id"])
    if admin.rol != "admin":
        return redirect(url_for("index"))

    usuarios = Usuario.query.all()
    return render_template("admin_usuarios.html", usuarios=usuarios, admin=admin)

#AGREGAR USUARIO
@app.route("/admin/usuarios/nuevo", methods=["GET", "POST"])
def admin_usuario_nuevo():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    admin = Usuario.query.get(session["usuario_id"])
    if admin.rol != "admin":
        return redirect(url_for("index"))

    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        telefono = request.form["telefono"]
        direccion = request.form["direccion"]
        password = request.form["password"]
        rol = request.form["rol"]

        nuevo = Usuario(
            nombre=nombre,
            email=email,
            telefono=telefono,
            direccion=direccion,
            password_hash=generate_password_hash(password),
            rol=rol
        )

        db.session.add(nuevo)
        db.session.commit()

        return redirect("/admin/usuarios")

    return render_template("admin_usuario_form.html", modo="nuevo")

#EDITAR USUARIO
@app.route("/admin/usuarios/editar/<int:id>", methods=["GET", "POST"])
def admin_usuario_editar(id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    admin = Usuario.query.get(session["usuario_id"])
    if admin.rol != "admin":
        return redirect(url_for("index"))

    usuario = Usuario.query.get(id)

    if request.method == "POST":
        usuario.nombre = request.form["nombre"]
        usuario.email = request.form["email"]
        usuario.telefono = request.form["telefono"]
        usuario.direccion = request.form["direccion"]
        usuario.rol = request.form["rol"]

        db.session.commit()
        return redirect("/admin/usuarios")

    return render_template("admin_usuario_form.html", modo="editar", usuario=usuario)

#ELIMINAR USUARIO
@app.route("/admin/usuarios/eliminar/<int:id>")
def admin_usuario_eliminar(id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    admin = Usuario.query.get(session["usuario_id"])
    if admin.rol != "admin":
        return redirect(url_for("index"))

    usuario = Usuario.query.get(id)
    db.session.delete(usuario)
    db.session.commit()

    return redirect("/admin/usuarios")

#CRUD PEDIDOS
@app.route("/admin/pedidos")
def admin_pedidos():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    admin = Usuario.query.get(session["usuario_id"])
    if admin.rol != "admin":
        return redirect(url_for("index"))

    pedidos = Pedido.query.order_by(Pedido.creado_en.desc()).all()
    return render_template("admin_pedidos.html", pedidos=pedidos)

#DETALLES DE UN PEDIDO
@app.route("/admin/pedidos/<int:id>")
def admin_pedido_detalle(id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    admin = Usuario.query.get(session["usuario_id"])
    if admin.rol != "admin":
        return redirect(url_for("index"))

    pedido = Pedido.query.get(id)
    items = PedidoItem.query.filter_by(pedido_id=id).all()

    return render_template("admin_pedido_detalle.html", pedido=pedido, items=items)

#ELIMINAR PEDIDO
@app.route("/admin/pedidos/eliminar/<int:id>")
def admin_pedido_eliminar(id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    admin = Usuario.query.get(session["usuario_id"])
    if admin.rol != "admin":
        return redirect(url_for("index"))

    pedido = Pedido.query.get(id)
    
    PedidoItem.query.filter_by(pedido_id=id).delete()

    db.session.delete(pedido)
    db.session.commit()

    return redirect("/admin/pedidos")

@app.route("/logout")
def logout():
    session.pop("usuario_id", None)
    return redirect(url_for("login"))

@app.route("/catalogo")
def catalogo():
    productos = Producto.query.all()
    usuario = None
    if "usuario_id" in session:
        usuario = Usuario.query.get(session["usuario_id"])

    return render_template("catalogo.html", productos=productos, usuario=usuario)

# CARRITO
carrito_bp = Blueprint("carrito", __name__)

@carrito_bp.route("/agregar_carrito/<int:producto_id>", methods=["POST"])
def agregar_carrito(producto_id):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]

    # Obtener cantidad desde el formulario
    cantidad = int(request.form.get("cantidad", 1))

    # Obtener o crear carrito
    carrito = Carrito.query.filter_by(usuario_id=usuario_id).first()

    if not carrito:
        carrito = Carrito(usuario_id=usuario_id)
        db.session.add(carrito)
        db.session.commit()

    # Verificar si el producto ya esta en el carrito
    item = CarritoItem.query.filter_by(carrito_id=carrito.id, producto_id=producto_id).first()

    if item:
        item.cantidad += cantidad
    else:
        producto = Producto.query.get(producto_id)
        item = CarritoItem(
            carrito_id=carrito.id,
            producto_id=producto_id,
            cantidad=cantidad,
            precio_unitario=producto.precio
        )
        db.session.add(item)

    db.session.commit()
    return redirect(url_for("catalogo"))

app.register_blueprint(carrito_bp)

@app.route("/carrito")
def ver_carrito():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario = Usuario.query.get(session["usuario_id"])

    carrito = Carrito.query.filter_by(usuario_id=usuario.id).first()

    items = carrito.items if carrito else []
    total = sum(item.cantidad * float(item.precio_unitario) for item in items)

    return render_template("carrito.html", items=items, total=total, usuario=usuario)

@app.route("/eliminar_item/<int:item_id>")
def eliminar_item(item_id):
    item = CarritoItem.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for("ver_carrito"))

#PAGOS
@app.route("/checkout")
def checkout():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario = Usuario.query.get(session["usuario_id"])

    carrito = Carrito.query.filter_by(usuario_id=usuario.id).first()
    items = carrito.items if carrito else []
    total = sum(item.cantidad * float(item.precio_unitario) for item in items)

    client_id = os.getenv("PAYPAL_CLIENT_ID")

    return render_template("checkout.html",
                           usuario=usuario,
                           total=total,
                           items=items,
                           client_id=client_id)


import base64
import json

@app.route("/crear_orden_paypal", methods=["POST"])
def crear_orden_paypal():
    usuario_id = session.get("usuario_id")
    carrito = Carrito.query.filter_by(usuario_id=usuario_id).first()

    total = sum(item.cantidad * float(item.precio_unitario) for item in carrito.items)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Basic " + base64.b64encode(
            (os.getenv("PAYPAL_CLIENT_ID") + ":" + os.getenv("PAYPAL_SECRET")).encode()
        ).decode()
    }

    cuerpo = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "USD",
                    "value": f"{total:.2f}"
                }
            }
        ]
    }

    r = requests.post(os.getenv("PAYPAL_API") + "/v2/checkout/orders",
                      json=cuerpo, headers=headers)

    return r.json()

@app.route("/capturar_pago_paypal/<order_id>", methods=["POST"])
def capturar_pago_paypal(order_id):

    #PAGO EN PAYPAL
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Basic " + base64.b64encode(
            (os.getenv("PAYPAL_CLIENT_ID") + ":" + os.getenv("PAYPAL_SECRET")).encode()
        ).decode()
    }

    r = requests.post(os.getenv("PAYPAL_API") + f"/v2/checkout/orders/{order_id}/capture",
                      headers=headers)

    data = r.json()

    #DATOS DEL CLIENTE
    usuario_id = session["usuario_id"]
    usuario = Usuario.query.get(usuario_id)

    #OBTENER CARRITO
    carrito = Carrito.query.filter_by(usuario_id=usuario.id).first()
    items = carrito.items
    total = sum(item.cantidad * float(item.precio_unitario) for item in items)

    #GUARDAR PEDIDO
    nuevo_pedido = Pedido(
        usuario_id=usuario_id,
        total=total,
        estado="Pagado",
        metodo_pago="PayPal",
        direccion_envio=usuario.direccion
    )
    db.session.add(nuevo_pedido)
    db.session.commit()

    # Guardar items del pedido
    for item in items:
        pedido_item = PedidoItem(
            pedido_id=nuevo_pedido.id,
            producto_id=item.producto_id,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario
        )
        db.session.add(pedido_item)

        # Descontar inventario
        producto = Producto.query.get(item.producto_id)
        producto.stock -= item.cantidad

    # Vaciar carrito
    for item in items:
        db.session.delete(item)

    db.session.commit()

    #ENVIAR CORREO DE CONFIRMACION
    cuerpo = f"""
Hola {usuario.nombre},

Tu pago se ha procesado con éxito. 🎉

DETALLES DEL PEDIDO:
---------------------------------------
Número de pedido: {nuevo_pedido.id}
Total pagado: ${total:.2f}
Método de pago: PayPal
---------------------------------------

Productos comprados:
"""

    for item in items:
        cuerpo += f"- {item.producto.nombre} x {item.cantidad} (${item.precio_unitario})\n"

    cuerpo += "\n¡Gracias por tu compra!\nFerretería Online 🔧🧡"

    msg = Message(
        subject=f"Confirmación de compra #{nuevo_pedido.id}",
        recipients=[usuario.email],
        body=cuerpo
    )
    mail.send(msg)

    return jsonify({"status": "COMPLETED"})


@app.route("/pedido_exitoso")
def pedido_exitoso():
    return render_template("pago_exitoso.html")

@app.route("/contacto")
def contacto():
    return render_template("contacto.html")

@app.route("/enviar_contacto", methods=["POST"])
def enviar_contacto():
    nombre = request.form["nombre"]
    email = request.form["email"]
    mensaje = request.form["mensaje"]

    # Mensaje que se envia al admin
    cuerpo = f"""
    Admin tienes un nuevo mensaje desde el formulario de contacto:

    Nombre: {nombre}
    Correo: {email}
    Mensaje:
    {mensaje}
    """

    msg = Message(
        subject="Nuevo mensaje de contacto",
        recipients=[os.getenv("MAIL_USERNAME")],
        body=cuerpo
    )
    mail.send(msg)

    # Mensaje de confirmacion al usuario
    confirmacion = Message(
        subject="Hemos recibido tu mensaje",
        recipients=[email],
        body=f"Hola {nombre},\n\nGracias por contactarnos. Te responderemos pronto.\n\nMensaje enviado:\n{mensaje}"
    )
    mail.send(confirmacion)

    return render_template("contacto_exitoso.html", nombre=nombre)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
