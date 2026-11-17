from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "agrospace_andes_2026"

DATABASE = "agrospace.db"


def conectar():
    conexion = sqlite3.connect(DATABASE)
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_tablas():
    conexion = conectar()
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'usuario'
        )
    """)

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS cultivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            terreno TEXT NOT NULL,
            cultivo TEXT NOT NULL,
            area REAL NOT NULL,
            observaciones TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    conexion.commit()
    conexion.close()


def login_requerido(funcion):
    @wraps(funcion)
    def comprobar(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return funcion(*args, **kwargs)
    return comprobar


@app.route("/")
def inicio():
    return render_template("inicio.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        password = generate_password_hash(request.form["password"])

        conexion = conectar()
        try:
            conexion.execute(
                "INSERT INTO usuarios (nombre, correo, password) VALUES (?, ?, ?)",
                (nombre, correo, password)
            )
            conexion.commit()
            flash("Registro exitoso. Ahora inicia sesión.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Ese correo ya está registrado.")
        finally:
            conexion.close()

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        password = request.form["password"]

        conexion = conectar()
        usuario = conexion.execute(
            "SELECT * FROM usuarios WHERE correo = ?", (correo,)
        ).fetchone()
        conexion.close()

        if usuario and check_password_hash(usuario["password"], password):
            session["usuario_id"] = usuario["id"]
            session["nombre"] = usuario["nombre"]
            session["rol"] = usuario["rol"]
            return redirect(url_for("panel"))

        flash("Correo o contraseña incorrectos.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("inicio"))


@app.route("/panel")
@login_requerido
def panel():
    conexion = conectar()
    cultivos = conexion.execute(
        "SELECT * FROM cultivos WHERE usuario_id = ?",
        (session["usuario_id"],)
    ).fetchall()
    conexion.close()

    return render_template("panel.html", cultivos=cultivos)


@app.route("/cultivos/nuevo", methods=["GET", "POST"])
@login_requerido
def nuevo_cultivo():
    if request.method == "POST":
        terreno = request.form["terreno"]
        cultivo = request.form["cultivo"]
        area = request.form["area"]
        observaciones = request.form["observaciones"]

        conexion = conectar()
        conexion.execute("""
            INSERT INTO cultivos
            (usuario_id, terreno, cultivo, area, observaciones)
            VALUES (?, ?, ?, ?, ?)
        """, (session["usuario_id"], terreno, cultivo, area, observaciones))
        conexion.commit()
        conexion.close()

        return redirect(url_for("panel"))

    return render_template("cultivo_form.html")


@app.route("/cultivos/editar/<int:id>", methods=["GET", "POST"])
@login_requerido
def editar_cultivo(id):
    conexion = conectar()
    cultivo = conexion.execute(
        "SELECT * FROM cultivos WHERE id = ? AND usuario_id = ?",
        (id, session["usuario_id"])
    ).fetchone()

    if cultivo is None:
        conexion.close()
        return redirect(url_for("panel"))

    if request.method == "POST":
        conexion.execute("""
            UPDATE cultivos
            SET terreno = ?, cultivo = ?, area = ?, observaciones = ?
            WHERE id = ? AND usuario_id = ?
        """, (
            request.form["terreno"],
            request.form["cultivo"],
            request.form["area"],
            request.form["observaciones"],
            id,
            session["usuario_id"]
        ))
        conexion.commit()
        conexion.close()
        return redirect(url_for("panel"))

    conexion.close()
    return render_template("cultivo_form.html", cultivo=cultivo)


@app.route("/cultivos/eliminar/<int:id>")
@login_requerido
def eliminar_cultivo(id):
    conexion = conectar()
    conexion.execute(
        "DELETE FROM cultivos WHERE id = ? AND usuario_id = ?",
        (id, session["usuario_id"])
    )
    conexion.commit()
    conexion.close()
    return redirect(url_for("panel"))


if __name__ == "__main__":
    crear_tablas()
    app.run(debug=True)