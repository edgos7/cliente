from flask import Flask
from flask import render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from functools import wraps
from wtforms import Form, StringField, PasswordField, validators, IntegerField
from passlib.hash import sha256_crypt
from selenium import webdriver
import funcionesSelenium
import threading
from wtforms_components import TimeField

#print funcionesSelenium.respuestaAutomatica()

#browser = webdriver.Firefox()
#browser.get('https://web.whatsapp.com')
browser = None
iniciado = False
primera = True
app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'cliente'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


@app.errorhandler(404)
def noEncontrada(error):
    error = 'Pagina No Encontrada'
    return render_template('index.html', error=error)

@app.route('/')
def index():
	return render_template('index.html')


class RegisterForm(Form):
	name = StringField('', [
		validators.DataRequired(message='Campo Requerido'),
		validators.Length(min=6, max=50,message='Debe ingresar entre 6 y 50 caracteres')		
	])
	email = StringField('', [
		validators.DataRequired(message='Campo Requerido'),
		validators.Email(message='Debe ser un email valido')		
	])
	password = PasswordField('',[
		validators.DataRequired(message='Campo Requerido'),
		validators.EqualTo('confirm',message='Passwords no coinciden')
	])
	confirm = PasswordField('')


class ContactosForm(Form):
    name = StringField('', [
        validators.DataRequired(message='Campo Requerido'),
        validators.Length(min=6, max=50,message='Debe ingresar entre 6 y 50 caracteres')        
    ])
    telefono = IntegerField('', [
        validators.DataRequired(message='Ingrese Numeros')
    ])

class PalabrasForm(Form):
    palabra = StringField('', [
        validators.DataRequired(message='Campo Requerido'),
        validators.Length(min=0, max=50,message='Debe ingresar maximo 50 caracteres')        
    ])
    respuesta = StringField('', [
        validators.DataRequired(message='Campo Requerido'),
        validators.Length(min=0, max=100,message='Debe ingresar maximo y 100 caracteres')        
    ])


class MensajesForm(Form):
    hora = TimeField('Hora', [validators.DataRequired(message='Campo Requerido')])
    mensaje = StringField('Mensaje', [
        validators.DataRequired(message='Campo Requerido'),
        validators.Length(min=0, max=100,message='Debe ingresar maximo y 100 caracteres')        
    ])

@app.route('/registro', methods=['GET','POST'])
def registro():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE email = %s", [email])
        print("resultado",result)
        if result == 0:
        	cur.execute("INSERT INTO users(name, email, password) VALUES(%s, %s, %s)", (name, email, password))
        	mysql.connection.commit()
        	cur.close()
        	flash('Registro Exitoso', 'success')
        	return redirect(url_for('login'))
        else:
        	cur.close()
        	error ='Usuario ya registrado'
        	return render_template('registro.html', form=form,error=error)
    return render_template('registro.html',form=form)


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_candidate = request.form['password']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE email = %s", [email])
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            username = data['name']
            email = data['email']
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['name'] = username
                session['email'] = email
                global primera
                primera = True
                #flash('Logueo Exitoso', 'success')
                return redirect(url_for('principal'))
            else:
                error = 'Password incorrecto'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Email no Valido'
            return render_template('login.html', error=error)
    return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Acceso no autorizado', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    browser.quit()
    session.clear()
    return redirect(url_for('login'))


@app.route('/principal')
@is_logged_in
def principal():
    global browser, primera
    if primera:
        browser = webdriver.Firefox()
        browser.get('https://web.whatsapp.com')
        primera = False
    return render_template('dashboard.html')

@app.route('/respuesta')
@is_logged_in
def respuesta():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM respuesta WHERE usuario = %s", [session['email']])
    palabras = cur.fetchall()
    if result > 0:
        return render_template('respuesta.html', palabras=palabras, iniciado=iniciado)
    else:
        msg = 'No Se Encontraron Palabras a Buscar'
        return render_template('respuesta.html', msg=msg, iniciado=iniciado)
    # Close connection
    cur.close()


@app.route('/mensajes')
@is_logged_in
def mensajes():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM contactos WHERE usuario = %s", [session['email']])
    contactos = cur.fetchall()
    if result > 0:
        return render_template('mensajes.html', contactos=contactos)
    else:
        msg = 'No Se Encontraron Contactos'
        return render_template('mensajes.html', msg=msg)
    # Close connection
    cur.close()


@app.route('/adicionarContacto', methods=['GET','POST'])
@is_logged_in
def adicionarContacto():
    form = ContactosForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        telefono = form.telefono.data
        cur = mysql.connection.cursor()        
        cur.execute("INSERT INTO contactos(telefono, nombre, usuario) VALUES(%s, %s, %s)", (telefono, name, session['email']))
        mysql.connection.commit()
        cur.close()
        flash('Contacto Agregado', 'success')
        return redirect(url_for('mensajes'))
    return render_template('adicionarContacto.html',form=form)


@app.route('/editarContacto/<string:id>', methods=['GET','POST'])
@is_logged_in
def editarContacto(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM contactos WHERE id = %s", [id])
    contacto = cur.fetchone()
    cur.close()
    form = ContactosForm(request.form)
    form.name.data = contacto['nombre']
    form.telefono.data = contacto['telefono']
    if request.method == 'POST' and form.validate():
        name = request.form['name']
        telefono = request.form['telefono']
        cur = mysql.connection.cursor()        
        cur.execute ("UPDATE contactos SET nombre=%s, telefono=%s WHERE id=%s",(name, telefono, id))
        mysql.connection.commit()
        cur.close()
        flash('Cambio Exitoso', 'success')
        return redirect(url_for('mensajes'))
    return render_template('editarContacto.html', form=form)


@app.route('/borrarContacto/<string:id>', methods=['POST'])
@is_logged_in
def borrarContacto(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM contactos WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash('Contacto Eliminado', 'success')
    return redirect(url_for('mensajes'))


@app.route('/adicionarPalabra', methods=['GET','POST'])
@is_logged_in
def adicionarPalabra():
    form = PalabrasForm(request.form)
    if request.method == 'POST' and form.validate():
        palabra = form.palabra.data
        respuesta = form.respuesta.data
        cur = mysql.connection.cursor()        
        cur.execute("INSERT INTO respuesta(palabra, respuesta, usuario) VALUES(%s, %s, %s)", (palabra, respuesta, session['email']))
        mysql.connection.commit()
        cur.close()
        flash('Palabra Agregada', 'success')
        return redirect(url_for('respuesta'))
    return render_template('adicionarPalabra.html',form=form)


@app.route('/editarPalabra/<string:id>', methods=['GET','POST'])
@is_logged_in
def editarPalabra(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM respuesta WHERE id = %s", [id])
    palabra = cur.fetchone()
    cur.close()
    form = PalabrasForm(request.form)
    form.palabra.data = palabra['palabra']
    form.respuesta.data = palabra['respuesta']
    if request.method == 'POST' and form.validate():
        palabra = request.form['palabra']
        respuesta = request.form['respuesta']
        cur = mysql.connection.cursor()        
        cur.execute ("UPDATE respuesta SET palabra=%s, respuesta=%s WHERE id=%s",(palabra, respuesta, id))
        mysql.connection.commit()
        cur.close()
        flash('Cambio Exitoso', 'success')
        return redirect(url_for('respuesta'))
    return render_template('editarPalabra.html', form=form)


@app.route('/borrarPalabra/<string:id>', methods=['POST'])
@is_logged_in
def borrarPalabra(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM respuesta WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash('Palabra Eliminada', 'success')
    return redirect(url_for('respuesta'))


@app.route('/iniciarRespuesta', methods=['GET','POST'])
@is_logged_in
def iniciarRespuesta():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM respuesta WHERE usuario = %s", [session['email']])
    palabras = cur.fetchall()
    cur.close()
    listaPalabras = []
    listaRespuestas = []
    for palabra in palabras:
        listaPalabras.append(palabra['palabra'])
        listaRespuestas.append(palabra['respuesta'])
    flash('Respuesta Iniciada', 'success')
    print ("iniciado respuesta automatica")
    funcionesSelenium.cambiarTerminar(False)
    t = threading.Thread(target=funcionesSelenium.respuestaAutomatica,args=(browser,listaPalabras,listaRespuestas))
    t.start()
    global iniciado
    iniciado = True
    return redirect(url_for('respuesta'))

@app.route('/terminarRespuesta', methods=['GET','POST'])
@is_logged_in
def terminarRespuesta():
    global iniciado
    iniciado = False
    funcionesSelenium.cambiarTerminar(True)
    flash('Respuesta Terminada', 'success')
    return redirect(url_for('respuesta'))


@app.route('/iniciarEnvioMensajes', methods=['GET','POST'])
@is_logged_in
def iniciarEnvioMensajes():
    form = MensajesForm(request.form)
    if request.method == 'POST' and form.validate():
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM contactos WHERE usuario = %s", [session['email']])
        contactos = cur.fetchall()
        cur.close()
        numeros = []
        nombres = []
        for contacto in contactos:
            numeros.append(contacto['telefono'])
            nombres.append(contacto['nombre'])
        hora = form.hora.data
        mensaje = form.mensaje.data
        t = threading.Thread(target=funcionesSelenium.enviarMensajesHora,args=(browser,mensaje,numeros,nombres,hora))
        t.start()
        flash('Envio de mensajes iniciado', 'success')
        return redirect(url_for('mensajes'))
    return render_template('envioMensajes.html',form=form)


if __name__ == '__main__':
	app.secret_key='secret123'
	app.run(debug = True)