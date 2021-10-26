import datetime
import hashlib
import random

from decouple import config
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from flask import Flask, jsonify, request
# from database import User, UserSchema, Verification
from sqlalchemy import Column, Integer, Float, String, DateTime
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail, Message

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+ os.path.join(basedir, 'planets.db')
app.config['SCHEDULER_API_ENABLED'] = True
# app.config['MAIL_SERVER']= str(config('MAIL_SERVER'))
# app.config['MAIL_PORT'] = config('MAIL_PORT')
# app.config['MAIL_USERNAME'] = str(config('MAIL_USERNAME'))
# app.config['MAIL_PASSWORD'] = str(config('MAIL_PASSWORD'))
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USE_SSL'] = False
app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'f702b77be1a9e9'
app.config['MAIL_PASSWORD'] = '666dd4298133e8'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
mail = Mail(app)

scheduler = BackgroundScheduler()

migrate = Migrate(app, db)


authentication_minutes = 50

@app.before_first_request
def initialises():
    scheduler.start()


@app.cli.command('db_create')
def db_create_all():
    db.create_all()
    print('Database created')

@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database dropped')

# Create login with password
@app.route('/')
def test():
    return  jsonify('welcome to Giddy')

 # Create login with password
@app.route('/login', methods= ['POST'])
def login():
    if(request.headers.get('Content-Type') != 'application/json'):
        return jsonify(f'Content-Type header must be application/json'), 400
    email = request.json['email']
    password = request.json['password']

    if email is None or '.' not in email or '@' not in email:
        return jsonify(message= 'invalid email'), 400

    if password is None or len(str(password).strip()) < 6 :
        return jsonify(message= 'password length must be less than 6'), 400

    password = (password).strip()
    email = str(email).lower().strip()

    userlist = db.session.query(User).filter_by(email = email).all()
    if (len(userlist) != 1):
        return jsonify(message= 'Invalid user'), 400

    if encrypt(password) != userlist[0].password:
        return jsonify(message= 'Incorrect password'), 400

    event = LoginEvent(
        user_id = str(userlist[0].id),
        timestamp = datetime.datetime.utcnow()
    )
    db.session.add(event)
    db.session.commit()

    return jsonify(UserSchema().dump(userlist[0]))


@app.route('/signup', methods = ['POST'])
def signup():
    if(request.headers.get('Content-Type') != 'application/json'):
        return jsonify(f'Content-Type header must be application/json'), 400
    fname = request.json['fname']
    lname = request.json['lname']
    email = request.json['email']
    password = request.json['password']

    if fname is None or len(str(fname).strip()) == 0:
        return jsonify(message= 'invalid first name'), 400

    if lname is None or len(str(lname).strip()) == 0:
        return jsonify(message= 'invalid last name'), 400

    if email is None or '.' not in email or '@' not in email:
        return jsonify(message = 'invalid email'), 400

    if password is None or len(str(password).strip()) < 6 :
        return jsonify('password length must be less than 6'), 400
    email = str(email).lower().strip()

    if (len(db.session.query(User).filter_by(email = email).all()) > 0):
        return jsonify(message = 'Email already exists'), 400

    fname = str(fname).strip()
    lname = str(lname).strip()
    token = encrypt(email)
    password = encrypt(password)
    user = User(first_name=fname,
                    last_name=lname,
                    email=email,
                    password=password,
                    token = token,
                    admin_stat = 0)

    db.session.add(user)
    db.session.commit()

    print (f'fname: {fname}, lname: {lname}')

    return jsonify(UserSchema().dump(user)), 201

# Create initaiate password retrieval
@app.route('/initpassretrieval', methods  = ['POST'])
def init_passretrieval():
    email = request.json['email']

    if email is None or '.' not in email or '@' not in email:
        return jsonify(message = 'invalid email'), 400

    email = str(email).lower().strip()
    userlist = db.session.query(User).filter_by(email=email).all()
    if (len(userlist) != 1):
        return jsonify(message='Invalid user'), 401

    code = gen_random_code(6)
    while len(db.session.query(Verification).filter_by(code=code).all()) > 0:
        code = gen_random_code(6)

    verification = Verification(
        user_id = userlist[0].id,
        timestamp = datetime.datetime.utcnow(),
        code=code
    )
    db.session.add(verification)
    db.session.commit()

    scheduler.add_job(destroyVerificationEvent, 'interval', id=code, minutes=authentication_minutes, args = [code])
    send_email(email,
               f'Hello {userlist[0].first_name},\n\nSorry about your password. Continue your password retrieval with this code.\n\n'
               f' {code}.\n\n'
               f'\nThis code would expire in the next {authentication_minutes} minutes.', subject='Giddy Authentication')
    return jsonify('done')


@app.route('/authret/code/<int:code>', methods=['POST'])
def confirm_retrieval_code(code):
    code = str(code)
    print(f'code: {code}')
    if code is None or len(code)!=6:
        return jsonify(message='Invalid code'), 404

    verification = db.session.query(Verification).filter_by(code=code).first()
    if verification is None:
        return jsonify(message='Code not found'), 404

    user = db.session.query(User).filter_by(id=verification.user_id).first()
    if user is None:
        return jsonify(message='User not found'), 404

    usermail = user.email

    return jsonify({'valid': True, 'email':usermail})


@app.route('/password/change', methods = ['POST'])
def change_password():
    code = request.json['code']
    password = request.json['password']

    if code is None or len(code)!=6:
        return jsonify(message='Invalid code'), 404

    verification = db.session.query(Verification).filter_by(code=code).first()
    if verification is None:
        return jsonify(message='Code not found'), 404

    user = User.query.get(verification.user_id)
    if user is None:
        return jsonify(message='User not found'), 404

    if password is None or len(str(password).strip()) < 6 :
        return jsonify('password length must be less than 6'), 400

    user.password = encrypt(password)
    db.session.delete(verification)
    db.session.commit()

    return jsonify(message = 'done')


def send_email(email:str, message:str,  subject:str = ''):
    emailsend = config('AUTH_EMAIL')
    print(f'sending email: {emailsend} {email}')
    msg = Message( subject=subject, body= message,
        sender= emailsend,
        recipients=[email]
    )
    mail.send(msg)


def destroyVerificationEvent(code:str):
    print(f'job ran: {code}')
    try:
        verification = db.session.query(Verification).filter_by(code=code).first()
        if verification is not None:
            print('detected verification')

            db.session.delete(verification)
            db.session.commit()

        scheduler.remove_job(code)
    except  Exception:
        print(f'job: {code} does not exist')


def gen_random_code(str_size):
    allowed_chars='0123456789'
    return ''.join(random.choice(allowed_chars) for x in range(str_size))


def random_string_generator(str_size):
    allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.,;!@#$%^&*_?><0123456789'
    return ''.join(random.choice(allowed_chars) for x in range(str_size))


def encrypt(raw_password, salt='b57b5c1c5ae168997a33b908f3bb315f'):
    # generate new salt, and hash a password
    salt_size = 32
    rounds = 12000

    if raw_password:
        encrypted = hashlib.md5(str(raw_password + salt).encode()).hexdigest()
    else:
        encrypted = None

    return encrypted

def passlib_encryption_verify(raw_password, enc_password):
    """
    @returns TRUE or FALSE
    """
    if raw_password and enc_password:
        # verifying the password
        response = str(encrypt(raw_password)) == str(enc_password)
    else:
        response = None

    return response

class User(db.Model):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique= True)
    password = Column(String)
    token = Column(String)
    admin_stat = Column(Integer)

class Verification(db.Model):
    __tablename__ = 'verification'
    id = Column(Integer, primary_key= True)
    user_id = Column(String)
    code = Column(String)
    timestamp = Column(DateTime)

class LoginEvent(db.Model):
    __tablename__ = 'event'
    id = Column(Integer, primary_key= True)
    user_id = Column(String)
    timestamp = Column(DateTime)

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email','admin_stat','token')

class PlanetSchema( ma.Schema):
    class Meta:
        fields = ['planet_id', 'planet_name', 'planet_type', 'home_star', 'mass', 'radius', 'distance']

if __name__ == '__main__':
    app.run()
    db.create_all()