import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_bootstrap import Bootstrap
from logic.identificarPlaca import idPlaca

app = Flask(__name__)

app.config['uploadFolder'] = "./static/image"
app.config['MYSQL_HOST'] = 'localhost' 
app.config['MYSQL_USER'] = 'root' #user de la base
app.config['MYSQL_PASSWORD'] = 'J08042005' #contraseña de la base
app.config['MYSQL_DB'] = 'registro_acceso_vehicular' #nombre de la base 
mysql = MySQL(app)

# settings
app.secret_key = "mysecretkey"

# pagina de inicio
@app.route("/")
def Informacion():
    return render_template('Informacion.html')


@app.route("/index_visitante")
def index_visitante():
    return render_template("index_visitante.html")

# ------------ VISITANTES REGISTRO  ---------------------------

# pasamos a asolicitar los datos del visitante 
@app.route("/info_visitante")
def info_visitante():
    return render_template('info_visitante.html')


# añadimos los visitantes a la base de datos 
@app.route("/add_visitante", methods=['POST'])
def add_visitante():
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
            return render_template('index_visitante.html',mensaje_error=1)
            
    tipo = request.form['tipo']
    placa = request.form['placa']
    descripcion = request.form['descripcion']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO visitantes (nombre, apellido, email, tipo_visitante, placa_vehiculo, descripcion_vehiculo ) VALUES (%s,%s,%s,%s,%s,%s)", (nombre, apellido, e_mail, tipo, placa, descripcion))
    mysql.connection.commit()
    flash('Visitante registrado satisfactoriamente')
    return render_template('index_visitante.html',mensaje_error=0)


#-------------------------- VIGILANTE: VALIDACION Y REGISTRO DE LAS VISITAS -------------------------------------

vigilante_sesion=()

@app.route("/index_vigilante")
def index_vigilante(): 
    global vigilante_sesion
    vigilante_sesion=()
    return render_template('index_vigilante.html')

@app.route("/loguin_vigilante",methods=['POST'])
def loguin_vigilante():
    email = request.form['email']
    password = request.form['password']

    # validamos los datos ingresados con la base de datos 
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM vigilantes')
    vigilantes = cur.fetchall()
    cur.execute('SELECT * FROM  visitantes')
    visitantes =  cur.fetchall()
    for vig in vigilantes:
        if vig[3]==email and vig[4]==password:
            cur.execute('SELECT * FROM visitas')
            visitas_rej = cur.fetchall()
            global vigilante_sesion
            vigilante_sesion=vig
            return render_template('home_vigilante.html', vigilante=vig, visitas=visitas_rej, visitantes= visitantes)
    
    flash(" usuario ingresado es incorrecto ")
    return render_template('index_vigilante.html')


@app.route("/home_vigilante")
def home_vigilante():
    global vigilante_sesion
    # conectamos la tabla de visitas
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM visitas')
    visitas_rej = cur.fetchall()
    cur.execute('SELECT * FROM  visitantes')
    visitantes =  cur.fetchall()
    mysql.connection.commit()
    return render_template('home_vigilante.html', vigilante=vigilante_sesion, visitas=visitas_rej,visitantes= visitantes)


@app.route("/uploader",methods=['POST'])
def uploader():
    global vigilante_sesion
    if request.method == 'POST':
        file = request.files['archivo']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['uploadFolder'],"img.jpg"))
        placa = idPlaca(app.config['uploadFolder'],"img.jpg")
        print(placa)
        return render_template('confirmar_placa_vigilante.html', value = placa,vigilante=vigilante_sesion)


@app.route("/validar_visita",methods=['POST'])
def validar_visita():
    global vigilante_sesion
    
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
    print(visitantes)

    for vist in visitantes:
        print (vist )
        if _Placa==vist[5]:
            if vist[7] == 0:
                cur.execute("UPDATE visitantes SET activo = 1")
                cur.execute("INSERT INTO visitas (nombre_visitante, apellido_visitante, placa_vehiculo, fecha, hora_entrada, estado ) VALUES (%s,%s,%s,%s,%s,%s)",( vist[1],vist[2],vist[5], dia, h_entrada,1))
                mysql.connection.commit()
                cur.execute('SELECT * FROM visitas')
                visitas_rej = cur.fetchall()
                mysql.connection.commit()
                flash("visita registrada exitosamente")
                return render_template('home_vigilante.html',visitas=visitas_rej, visitantes= visitantes,  mensaje_error=0, vigilante=vigilante_sesion)

            else: 
                cur.execute("UPDATE visitantes SET activo = 0")
                sentencia = "DELETE FROM visitas WHERE placa_vehiculo LIKE ('{0}')".format (_Placa)
                cur.execute (sentencia)
                mysql.connection.commit()
                cur.execute('SELECT * FROM visitas')
                visitas_rej = cur.fetchall()
                mysql.connection.commit()
                flash("El vehiculo ha salido, que tenga buen viaje.")
                return render_template('home_vigilante.html',visitas=visitas_rej, visitantes= visitantes, mensaje_error=0, vigilante=vigilante_sesion)

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM visitas')
    visitas_rej = cur.fetchall()
    mysql.connection.commit()
    flash(" La placa ingresada no se encuentra en la base de datos de visitantes porfavor verificar ")
    return render_template('home_vigilante.html',visitas=visitas_rej,visitantes= visitantes, mensaje_error=1, vigilante=vigilante_sesion)
    

if __name__ == '__main__':
    app.run(debug=True)
