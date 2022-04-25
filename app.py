import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_bootstrap import Bootstrap
from logic.identificarPlaca import idPlaca

app = Flask(__name__)

app.config['uploadFolder'] = "./static/images"
app.config['MYSQL_HOST'] = 'localhost' 
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'J08042005'
app.config['MYSQL_DB'] = 'registro_acceso_vehicular' #
mysql = MySQL(app)

# settings
app.secret_key = "mysecretkey"

# variable auxiliara para notificacion de mensajes entre vistas 
mensaje_error=0

# pagina de inicio
@app.route("/")
def info():
    return render_template('Info.html')

@app.route("/index_visitante")
def index_visitante ():
    global mensaje_error
    return render_template('index_visitante.html',mensaje_error=mensaje_error)
# ------------ VISITANTES REGISTRO  ---------------------------

# añadimos los visitantes a la base de datos 
@app.route("/add_visitante", methods=['POST'])
def add_visitante():
    global mensaje_error

    nombre = request.form['nombre']
    apellido = request.form['apellido']
    e_mail = request.form['e-mail']

    # validamos de que no se ingrese un correo ya existente en la base de datos
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM visitantes')
    visitantes = cur.fetchall()
    for visitante in visitantes:
        if e_mail==visitante[3]:
            cur = mysql.connection.cursor()
            flash('El correo ingresado ya esta ascociado a otro visitante, porfavor usar otro ')
            mensaje_error=1
            return redirect(url_for('index_visitante'))
            
    tipo = request.form['tipo']
    placa = request.form['placa']
    descripcion = request.form['descripcion']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO visitantes (nombre, apellido, email, tipo_visitante, placa_vehiculo, descripcion_vehiculo ) VALUES (%s,%s,%s,%s,%s,%s)", (nombre, apellido, e_mail, tipo, placa, descripcion))
    mysql.connection.commit()
    flash('Visitante registrado satisfactoriamente')
    mensaje_error=0
    return redirect(url_for('index_visitante'))


#-------------------------- VIGILANTE: VALIDACION Y REGISTRO DE LAS VISITAS -------------------------------------

vigilante_sesion=()
visitas=()

@app.route("/index_vigilante")
def index_vigilante(): 
    global vigilante_sesion
    vigilante_sesion=()
    return render_template('index_vigilante.html')

@app.route("/loguin_vigilante",methods=['POST'])
def loguin_vigilante():
    global vigilante_sesion
    email = request.form['email']
    password = request.form['password']

    # validamos los datos ingresados con la base de datos 
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM vigilantes')
    vigilantes = cur.fetchall()
    for vig in vigilantes:
        if vig[3]==email and vig[4]==password:
            vigilante_sesion=vig
            return redirect(url_for('home_vigilante'))
    
    flash(" usuario ingresado es incorrecto ")
    return render_template('index_vigilante.html')


@app.route("/home_vigilante")
def home_vigilante():
    global vigilante_sesion
    global mensaje_error
    # conectamos la tabla de visitas
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM visitantes')
    visitantes = cur.fetchall()
    cur.execute('SELECT * FROM visitas')
    visitas_rej = cur.fetchall()
    mysql.connection.commit()
    return render_template('home_vigilante.html', vigilante=vigilante_sesion, visitantes= visitantes, visitas=visitas_rej, mensaje_error=mensaje_error)


@app.route("/uploader",methods=['POST'])
def uploader():
    global vigilante_sesion
    if request.method == 'POST':
        file = request.files['archivo']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['uploadFolder'],"img.jpg"))
        placa = idPlaca(app.config['uploadFolder'],"img.jpg")
        return render_template('confirmar_placa_vigilante.html', value = placa,vigilante=vigilante_sesion)


@app.route("/validar_visita",methods=['POST']) # se registra y valida la entrada del visitante
def validar_visita():
    global vigilante_sesion
    global mensaje_error
    placa= request.form['placa']
    _Placa = placa.rstrip()

    # obtenemos fecha yn hora del registro de la visita 
    now = datetime.now()
    dia=now.date()
    h_entrada=now.strftime("%H:%M:%S")
    # validamos de que la placa ingresada este en la base de datos
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM visitantes')
    visitantes = cur.fetchall()
    for vist in visitantes:
        if _Placa==vist[5]:
            cur.execute("INSERT INTO visitas (nombre_visitante, apellido_visitante, placa_vehiculo, fecha, hora_entrada, estado ) VALUES (%s,%s,%s,%s,%s,%s)",( vist[1],vist[2],vist[5], dia, h_entrada,1))
            mysql.connection.commit()
            cur.execute('SELECT * FROM visitas')
            visitas_rej = cur.fetchall()
            mysql.connection.commit()
            flash("visita registrada exitosamente")
            mensaje_error=0
            return redirect(url_for('home_vigilante'))
    
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM visitas')
    visitas_rej = cur.fetchall()
    mysql.connection.commit()
    flash(" La placa ingresada no se encuentra en la base de datos de visitantes porfavor verificar ")
    mensaje_error=1
    return redirect(url_for('home_vigilante'))
    
@app.route("/registrar_salida")
def registro_salida():
    global mensaje_error
    # obtenemos fecha yn hora del registro de la visita 
    now = datetime.now()
    hora_salida=now.strftime("%H:%M:%S")
    
    # hacemos la actualizacion del estado de la visita de 1=activa a 0=inactiva
    cur = mysql.connection.cursor()
    sentencia = " UPDATE visitas SET hora_salida = '{0}' , estado = 0".format( hora_salida)
    cur.execute (sentencia)
    
    flash('Salida registrada exitosamente')
    cur.execute('SELECT * FROM visitas')
    visitas_rej = cur.fetchall()
    mysql.connection.commit()
    mensaje_error=0
    return redirect(url_for('home_vigilante'))

if __name__ == '__main__':
    app.run(debug=True)
