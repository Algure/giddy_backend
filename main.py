import datetime
import hashlib
import random
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from flask import Flask, jsonify, request
# from database import User, UserSchema, Verification
from sqlalchemy import Column, Integer, Float, String, DateTime
from flask_apscheduler import APScheduler

app = Flask(__name__)

db = SQLAlchemy(app)
ma = Marshmallow(app)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+ os.path.join(basedir, 'planets.db')
migrate = Migrate(app, db)


@app.cli.command('db_create')
def db_create_all():
    db.create_all()
    print('Database created')

@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database dropped')

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

# TODO: Create verify password retrieval code
# TODO: Create retrieve password endpoint

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