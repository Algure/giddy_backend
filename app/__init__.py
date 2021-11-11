# Import flask and template operators
from flask import Flask, render_template
import datetime
import hashlib
import random

from decouple import config
from flask_cors import CORS
from flask_migrate import Migrate
import os
from flask import Flask, jsonify, request
# from database import User, UserSchema, Verification
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail, Message

import flask_whooshalchemy as wa

from app.mod_one.models import Course, Document, Video, CBT

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
# Define the database object which is imported
# by modules and controllers
from .mod_one.models import db
from .mod_one.models import ma
from .mod_one.models import Base

ma.init_app(app)
migrate = Migrate(app, db)
# cors = CORS(app)
cors = CORS(app, resources={r"/foo": {"origins": "*"}})


# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+ os.path.join(basedir, 'planets.db')
app.config['SCHEDULER_API_ENABLED'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'f702b77be1a9e9'
app.config['MAIL_PASSWORD'] = '666dd4298133e8'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['WHOOSH_BASE'] = 'whoosh'
app.config['CORS_HEADERS'] = 'Content-Type'


db.init_app(app) #Add this line Before migrate line
with app.app_context():
    # db.create_all()
    if db.engine.url.drivername == 'sqlite':
        migrate.init_app(app, db, render_as_batch=True)
    else:
        migrate.init_app(app, db)

mail = Mail(app)

scheduler = BackgroundScheduler()

migrate = Migrate(app, db)
# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return ('Not found'), 404

# Import a module / component using its blueprint handler variable (mod_auth)
from app.mod_one.controllers import mod_one as version1

# Register blueprint(s)
app.register_blueprint(version1)

wa.whoosh_index(app, Course)
wa.whoosh_index(app, Document)
wa.whoosh_index(app, Video)
wa.whoosh_index(app, CBT)

