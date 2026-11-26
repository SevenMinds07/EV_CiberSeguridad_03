from flask import Flask, request, render_template_string, redirect, session
from werkzeug.security import check_password_hash
import sqlite3
import secrets
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Configuración segura de cookies de sesión
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

def get_db():
    conn = sqlite3.connect('vulnerable.db')
    conn.row_factory = sqlite3.Row
    return conn

# Cabeceras de seguridad HTTP (Mitiga alertas de OWASP ZAP)
@app.after_request
def aplicar_cabeceras_seguridad(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'none'; form-action 'self'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

def generar_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username', '').strip()
        pw = request.form.get('password', '')
        
        # Consulta parametrizada (Mitiga SQL Injection)
        conn = get_db()
        usuario = conn.execute("SELECT * FROM usuarios WHERE username = ?", (user,)).fetchone()
        conn.close()
        
        if usuario and check_password_hash(usuario['password'], pw):
            session.clear()
            session['username'] = usuario['username']
            generar_csrf_token()
            return redirect('/dashboard')
        return "<h3>Acceso denegado</h3><a href='/login'>Volver</a>", 401

    return '''
        <h2>Login del Sistema Académico (Seguro)</h2>
        <form method="post">
            Usuario: <input type="text" name="username" required><br>
            Password: <input type="password" name="password" required><br>
            <input type="submit" value="Ingresar">
        </form>
    '''

@app.route('/dashboard')
def dashboard():
    username = session.get('username')
    if not username:
        return redirect('/login')

    conn = get_db()
    datos = conn.execute("SELECT * FROM usuarios WHERE username = ?", (username,)).fetchone()
    conn.close()

    if not datos:
        session.clear()
        return redirect('/login')

    # Plantilla con variables escapadas por Jinja2 (Mitiga XSS) y Token CSRF
    html = """
    <h1>Panel de {{ user }}</h1>
    <p><b>Rol:</b> {{ rol }}</p>
    <p><b>Biografía:</b> {{ bio }}</p>
    <hr>
    <h3>Actualizar Biografía (Protegido contra CSRF)</h3>
    <form action="/update_bio" method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <input type="text" name="nueva_bio" placeholder="Escribe algo..." maxlength="200">
        <input type="submit" value="Guardar Cambios">
    </form>
    <br><a href="/logout">Cerrar Sesión</a>
    """
    return render_template_string(
        html,
        user=datos['username'],
        rol=datos['rol'],
        bio=datos['bio'],
        csrf_token=generar_csrf_token()
    )

@app.route('/update_bio', methods=['POST'])
def update_bio():
    username = session.get('username')
    token_recibido = request.form.get('csrf_token')
    
    # Validación estricta de Token CSRF
    if not username or not token_recibido or token_recibido != session.get('csrf_token'):
        return "<h3>Error de seguridad: Token CSRF inválido o ausente</h3>", 403

    nueva_bio = request.form.get('nueva_bio', '').strip()
    conn = get_db()
    conn.execute("UPDATE usuarios SET bio = ? WHERE username = ?", (nueva_bio, username))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def home():
    return redirect('/login')

if __name__ == '__main__':
    # Modo debug desactivado en producción
    app.run(host='0.0.0.0', debug=False, port=5000)
