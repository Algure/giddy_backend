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

from app.mod_one.models import Course, Document, Video, CBT, School, Faculty, Department, News, Advert

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


def gen_random_code(str_size)-> str:
    allowed_chars='0123456789'
    return ''.join(random.choice(allowed_chars) for x in range(str_size))

def seed_database():
    piclist =  [
    'https://images.unsplash.com/photo-1520342868574-5fa3804e551c?ixlib=rb-0.3.5&ixid=eyJhcHBfaWQiOjEyMDd9&s=6ff92caffcdd63681a35134a6770ed3b&auto=format&fit=crop&w=1951&q=80',
    'https://images.unsplash.com/photo-1522205408450-add114ad53fe?ixlib=rb-0.3.5&ixid=eyJhcHBfaWQiOjEyMDd9&s=368f45b0888aeb0b7b08e3a1084d3ede&auto=format&fit=crop&w=1950&q=80',
    'https://images.unsplash.com/photo-1519125323398-675f0ddb6308?ixlib=rb-0.3.5&ixid=eyJhcHBfaWQiOjEyMDd9&s=94a1e718d89ca60a6337a6008341ca50&auto=format&fit=crop&w=1950&q=80',
    'https://images.unsplash.com/photo-1523205771623-e0faa4d2813d?ixlib=rb-0.3.5&ixid=eyJhcHBfaWQiOjEyMDd9&s=89719a0d55dd05e2deae4120227e6efc&auto=format&fit=crop&w=1953&q=80',
    'https://images.unsplash.com/photo-1508704019882-f9cf40e475b4?ixlib=rb-0.3.5&ixid=eyJhcHBfaWQiOjEyMDd9&s=8c6e5e3aba713b17aa1fe71ab4f0ae5b&auto=format&fit=crop&w=1352&q=80',
    'https://images.unsplash.com/photo-1519985176271-adb1088fa94c?ixlib=rb-0.3.5&ixid=eyJhcHBfaWQiOjEyMDd9&s=a0c8d632e977f94e5d312d9893258f59&auto=format&fit=crop&w=1355&q=80'
    ]
    db.drop_all()
    db.create_all()
    # Create 5 schools
    for i in range(1,6):
        school = School(name= f'School {i}00{i}' )
        db.session.add(school)
    db.session.commit()

    print('seeded schools')
    #Create 5 faculties per school
    for school in db.session.query(School).all():
        faculty = Faculty(
            name=str('Engineering'),
            school_id=str(school.id))
        db.session.add(faculty)
        faculty = Faculty(
            name=str('Sciences'),
            school_id=str(school.id))
        db.session.add(faculty)
        faculty = Faculty(
            name=str('Health Tech'),
            school_id=str(school.id))
        db.session.add(faculty)
        faculty = Faculty(
            name=str('Commerce'),
            school_id=str(school.id))
        db.session.add(faculty)
    db.session.commit()
    print('seeded faculties')

    # Create 5 departments per faculty
    for faculty in db.session.query(Faculty).all():
        for i in range(1,2):
            dept = Department(
                name=str(f'Department {i}00{i}'),
                school_id=str(faculty.school_id),
                faculty_id=str(faculty.id))
            db.session.add(dept)
        db.session.commit()
    print('seeded departments')

    # Create 5 courses per department
    # Publish courses
    for dept in db.session.query(Department).all():
        for i in range(1,2):
            course = Course(
                name= f'Course {i}',
                dept=str(dept.name),
                school=str(school.name),
                description=gen_random_code(1000),
                category=gen_random_code(10),
                pic_url=random.choice(piclist),
                uploader_id=str(0),
                is_published=True,
                total_tutorials=5,
                dept_id=str(dept.id),
                faculty_id=str(dept.faculty_id),
                school_id=str(dept.school_id),
                total_past_questions=5,
                total_videos=5,
                clicks=5,
                extras='')
            db.session.add(course)
    db.session.commit()
    print('seeded courses')

    # for course in db.session.query(Course).all():
    #     # Create 5 videos per course
    #     # Create 5 past questions per course
    #     # Create 5 tutorials per course
    #     # Create 5 CBT per course˚
    #     for i in range(1,2):
    #         video = Video(name=f'Video {i}',
    #                       url=random.choice(piclist),
    #                       size= '3MB',
    #                       time_in_secs='11',
    #                       pic_url='https://flutter.github.io/assets-for-api-docs/assets/videos/bee.mp4',
    #                       course_id=str(course.id),
    #                       uploader_id='0',
    #                       date=datetime.datetime.utcnow(),
    #                       clicks=0,
    #                       extras='')
    #         db.session.add(video)
    #
    #         document = Document(
    #             name= f'Past Question {i}',
    #             description='',
    #             size='3 MB',
    #             doctype='pq',
    #             course_id=course.id,
    #             url='',
    #             clicks=0,
    #             date=datetime.datetime.utcnow(),
    #             extras='')
    #         db.session.add(document)
    #         tut = Document(
    #             name= f'Tutorial {i}',
    #             description='',
    #             size='3 MB',
    #             doctype='tut',
    #             course_id=course.id,
    #             url='',
    #             clicks=0,
    #             date=datetime.datetime.utcnow(),
    #             extras='')
    #         db.session.add(tut)
    #         cbt = CBT(name=f'Computer Based Test {i}',
    #                   data='',
    #                   description=gen_random_code(100),
    #                   course_id=str(course.id),
    #                   date=datetime.datetime.utcnow(),
    #                   clicks=0)
    #         db.session.add(cbt)
    #         db.session.commit()
    #
    #         course.past_questions.append(document)
    #         course.tutorials.append(tut)
    #         course.videos.append(video)
    #         course.cbt.append(cbt)
    #         db.session.commit()
    print('seeded course components')

    # : Create News objects- 10
    # : Create Advert objects- 10
    for i in range(1, 10):
        news = News(
            title=f'News {i}000{i}',
            description=gen_random_code(100),
            user_id='',
            extras= random.choice(piclist),
            timestamp=datetime.datetime.utcnow())
        db.session.add(news)
    print('seeded news')

    for i in range(1, 10):
        advert = Advert(
            text=f'Advert {i}000',
            image_url=random.choice(piclist) if i <=5 else '',
            action_link=random.choice(piclist),
            mode= 'text' if i <=5 else 'image',
            timestamp=datetime.datetime.utcnow())
        db.session.add(advert)
    print('seeded adverts')

    db.session.commit()

with app.app_context():
    # db.create_all()
    wa.whoosh_index(app, Course)
    wa.whoosh_index(app, Document)
    wa.whoosh_index(app, CBT)
    wa.whoosh_index(app, Video)

    if db.engine.url.drivername == 'sqlite':
        migrate.init_app(app, db, render_as_batch=True)
    else:
        migrate.init_app(app, db)
    seed_database()


mail = Mail(app)

scheduler = BackgroundScheduler()

migrate = Migrate(app, db)
# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return ('Not found'), 404

# Import a module / component using its blueprint handler variable (mod_auth)
from app.mod_one.controllers import mod_one as version1, gen_random_code

# Register blueprint(s)
app.register_blueprint(version1, )
