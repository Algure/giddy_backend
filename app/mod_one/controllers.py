# Import the database object from the main app module
from decouple import config

from app import db

from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail, Message
from flask import Flask, render_template, jsonify, request, Blueprint
import datetime
import hashlib
import random

# Import module models (i.e. User)
from app.mod_one.models import *
from app.mod_one.models import Course
from app.mod_one.models import Document
from app.mod_one.models import  Video
from app.mod_one.models import CBT
from app.mod_one.models import LoginEvent
from app.mod_one.models import User
from app.mod_one.models import DownloadEvent
from app.mod_one.models import CalenderEvent
from app.mod_one.models import Verification
from app.mod_one.models import News
from app.mod_one.models import Advert

from app.mod_one.models import CourseSchema
from app.mod_one.models import DocumentSchema
from app.mod_one.models import VideoSchema
from app.mod_one.models import CBTSchema
from app.mod_one.models import UserSchema
from app.mod_one.models import  NewsSchema
from app.mod_one.models import AdSchema
from app.mod_one.models import CalendarSchema

# Define the blueprint: 'auth', set its url prefix: app.url/v1
mod_one = Blueprint('one', __name__, url_prefix='/v1')

from app import db
from app import app
from app import scheduler
from app import mail


authentication_minutes = 50
public_query_limit = 50


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
    return  'welcome to Giddy'

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


@app.route('/admin/analytics', methods= ['POST', 'GET'])
def fetch_analytics():
    token = request.json['token']
    start = request.json['start']
    end = request.json['end']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404
    if user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 400

    start_time = datetime.datetime.utcnow() - datetime.timedelta(days = 7)
    if start is not None:
        date_data = str(start).split(',')
        if len(date_data) >= 5:
            try:
                start_time = datetime.datetime(int(date_data[0]), int(date_data[1]), int(date_data[2]),
                                               int(date_data[3]), int(date_data[4]))
            except:
                return jsonify(message='Invalid request format: `start`.'), 400

    end_time = datetime.datetime.utcnow()
    if end is not None:
        date_data = str(start).split(',')
        if len(date_data) >= 5:
            try:
                end_time = datetime.datetime(int(date_data[0]), int(date_data[1]), int(date_data[2]),
                                             int(date_data[3]), int(date_data[4]))
            except:
                return jsonify(message='Invalid request format: `end`.'), 400

    eventslist = db.session.query(DownloadEvent).filter(DownloadEvent.user_id == str(user.id)). \
        filter(DownloadEvent.timestamp >= start_time).filter(CalenderEvent.timestamp <= end_time).all()

    loginlist = db.session.query(LoginEvent).filter(LoginEvent.user_id == str(user.id)). \
        filter(LoginEvent.timestamp >= start_time).filter(LoginEvent.timestamp <= end_time).all()

    users = 0
    videos = 0
    courses = 0
    tutorials = 0
    past_questions = 0
    cbts = 0

    for event in eventslist:
        if event.doc_type == 'video':
            videos += 1
        elif event.doc_type == 'course':
            courses += 1
        elif event.doc_type == 'tut':
            tutorials += 1
        elif event.doc_type == 'pq':
            past_questions += 1
        elif event.doc_type == 'cbt':
            cbts += 1

    users = len(loginlist)

    return jsonify({'users':users, 'videos':videos, 'courses':courses, 'tutorials':tutorials,
                    'past_questions':past_questions, 'cbts':cbts})

# class LoginEvent(db.Model):
#     __tablename__ = 'event'
#     id = Column(Integer, primary_key=True)
#     user_id = Column(String)
#     timestamp = Column(DateTime)
    # Fetch total users downloaded logged in period
    # Fetch total videos  downloaded in period
    # Fetch total courses downloaded in period
    # fetch total tutorials downloaded in period
    # fetch total past questions downloaded in period
    # fetch total cbts downloaded in period

@app.route('/signup', methods = ['POST'])
def signup():
    print('runnning')
    try:
        fname = request.json['fname']
        lname = request.json['lname']
        email = request.json['email']
        password = request.json['password']
    except Exception as e:
        print(f'exception: {e} trace: {e.__traceback__}')

    print('done 1')
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
    token = gen_random_code(str_size=110)
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

@app.route('/user/bookmark/course', methods= ['POST', 'DELETE'])
def bookmark_course():
    token = request.json['token']
    course_id = request.json['course_id']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    try:
        course_id = int(course_id)
    except:
        return jsonify('Invalid course id'), 400

    course = db.session.query(Course).filter_by(id = course_id).first()
    if course is None:
        return jsonify(message='Course not found'), 404

    if request.method == 'POST' and course not in user.course_bookmarks:
        user.course_bookmarks.add(course)
        db.session.commit()
    elif request.method == 'DELETE' and course in user.course_bookmarks:
        user.course_bookmarks.remove(course)
        db.session.commit()

    return jsonify('done')


@app.route('/user/bookmark/video', methods= ['POST', 'DELETE'])
def bookmark_video():
    token = request.json['token']
    video_id = request.json['video_id']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    try:
        video_id = int(video_id)
    except:
        return jsonify('Invalid video id'), 400

    video = db.session.query(Video).filter_by(id = video_id).first()
    if video is None:
        return jsonify(message='Video not found'), 404

    if request.method == 'POST' and video not in user.video_bookmarks:
        user.video_bookmarks.add(video)
        db.session.commit()
    elif request.method == 'DELETE' and video in user.video_bookmarks:
        user.video_bookmarks.remove(video)
        db.session.commit()

    return jsonify('done')


@app.route('/user/bookmark/document', methods= ['POST', 'DELETE'])
def bookmark_document():
    token = request.json['token']
    document_id = request.json['document_id']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    try:
        document_id = int(document_id)
    except:
        return jsonify('Invalid document id'), 400

    document = db.session.query(Document).filter_by(id = document_id).first()
    if document is None:
        return jsonify(message='Document not found'), 404

    if request.method == 'POST' and document not in user.document_bookmarks:
        user.document_bookmarks.add(document)
        db.session.commit()
    elif request.method == 'DELETE' and document in user.document_bookmarks:
        user.document_bookmarks.remove(document)
        db.session.commit()

    return jsonify('done')


@app.route('/user/bookmark/cbt', methods= ['POST', 'DELETE'])
def bookmark_cbt():
    token = request.json['token']
    cbt_id = request.json['cbt_id']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    try:
        cbt_id = int(cbt_id)
    except:
        return jsonify('Invalid CBT id'), 400

    cbt = db.session.query(CBT).filter_by(id = cbt_id).first()
    if cbt is None:
        return jsonify(message='CBT not found'), 404

    if request.method == 'POST' and cbt not in user.cbt_bookmarks:
        user.cbt_bookmarks.add(cbt)
        db.session.commit()
    elif request.method == 'DELETE' and cbt in user.cbt_bookmarks:
        user.cbt_bookmarks.remove(cbt)
        db.session.commit()

    return jsonify('done')


@app.route('/user/bookmark/cbtfetch', methods= ['POST', 'GET'])
def fetch_user_cbts():
    token = request.json['token']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    cbts = user.cbt_bookmarks.all()

    return jsonify(CBTSchema().dump(cbts,many=True))


@app.route('/user/bookmark/videosfetch', methods= ['POST', 'GET'])
def fetch_user_videos():
    token = request.json['token']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    videos = user.video_bookmarks.all()

    return jsonify(VideoSchema().dump(videos,many=True))


@app.route('/user/bookmark/coursesfetch', methods= ['POST', 'GET'])
def fetch_user_courses():
    token = request.json['token']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    courses = user.course_bookmarks.all()

    return jsonify(CourseSchema().dump(courses,many=True))


@app.route('/user/bookmark/documentsfetch', methods= ['POST', 'GET'])
def fetch_user_documents():
    token = request.json['token']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    docs = user.document_bookmarks.all()

    return jsonify(CourseSchema().dump(docs,many=True))


@app.route('/course/create', methods = ['POST'])
def create_course():
    token = request.json['token']
    name = request.json['name']
    dept = request.json['dept']
    school = request.json['school']
    description = request.json['description']
    category = request.json['category']
    pic_url = request.json['pic_url']
    extras = request.json['extras']

    if name is None or  token is None:
        return jsonify(message='Invalid request: body must contain: name and token'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 400

    course = Course(
        name = str(name) if name is not None else '',
        dept = str(dept) if dept is not None else '',
        school = str(school) if school is not None else '',
        description = str(description) if description is not None else '',
        category = str(category) if category is not None else  '',
        pic_url = str(pic_url) if pic_url is not None else '',
        uploader_id = str(user.id),
        is_published = False,
        total_tutorials = 0,
        total_past_questions=0,
        total_videos = 0,
        clicks = 0,
        extras = str(extras) if extras is not None else  '',
    )

    db.session.add(course)
    db.session.commit()

    return jsonify(CourseSchema().dump(course)) , 200


@app.route('/course/update', methods = ['POST'])
def update_course():
    token = request.json['token']
    id = request.json['id']
    name = request.json['name']
    dept = request.json['dept']
    school = request.json['school']
    description = request.json['description']
    category = request.json['category']
    pic_url = request.json['pic_url']
    extras = request.json['extras']

    if token is None or  id is None:
        return jsonify(message='Invalid request: body must contain: id and token'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 400

    course = db.session.query(Course).filter_by(id = int(id)).first()
    if course is None :
            return jsonify(message='Course not found'), 404

    if name is not None:
        course.name = name

    if dept is not None:
        course.dept = dept

    if school is not None:
        course.school = school

    if description is not None:
        course.description = description

    if category is not None:
        course.category = category

    if pic_url is not None:
        course.pic_url = pic_url

    if extras is not None:
        course.extras = extras

    db.session.commit()

    return jsonify(CourseSchema().dump(course)) , 200


@app.route('/course/publish', methods = ['POST'])
def publish_course():
    token = request.json['token']
    id = request.json['id']

    if token is None or  id is None:
        return jsonify(message='Invalid request: body must contain: id and token'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 400

    course = db.session.query(Course).filter_by(id = int(id)).first()
    if course is None :
            return jsonify(message='Course not found'), 404

    if course.is_published == True:
        return jsonify(message='Course already published'), 400

    if len(str(course.name).strip()) == 0:
        return jsonify(message='Invalid course name'), 400

    if course.materials == 0 and course.total_videos == 0 and course.total_past_questions == 0:
        return jsonify(message='Course has no learning resources'), 400

    course.is_published = True

    db.session.commit()

    return jsonify(message = 'done')


@app.route('/course/delete', methods = ['POST'])
def delete_course():
    token = request.json['token']
    id = request.json['id']

    if token is None or  id is None:
        return jsonify(message='Invalid request: body must contain: id and token'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 400

    course = db.session.query(Course).filter_by(id = int(id)).first()
    if course is None :
            return jsonify(message='Course not found'), 404

    db.session.delete(course)
    db.session.commit()

    return jsonify(message = 'done'), 204


@app.route('/course/fetch-trending', methods= ['POST', 'GET'])
def fetch_trending_courses():
    token = request.json['token']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    latest_courses = db.session.query(Course).order_by(Course.clicks.desc()).\
        limit(public_query_limit).all()

    return jsonify(CourseSchema().dump(latest_courses,many=True))


@app.route('/course/downloadlink', methods= ['POST', 'GET'])
def download_course():
    token = request.json['token']
    course_id = request.json['course_id']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    try:
        course_id = int(course_id)
    except:
        return jsonify('Invalid video id'), 400

    course = db.session.query(Course).filter_by(id = course_id).first()
    if course is None:
        return jsonify(message='Course not found'), 404

    if int(user.admin_stat) == 0:
        click = 0
        try:
            click = int(course.clicks)
        except:
            pass
        click += 1
        course.clicks = click
        event = DownloadEvent(doc_type='course',
                    object_id=str(course.id),
                    user_id=str(user.id),
                    timestamp=datetime.datetime.utcnow())
        db.session.add(event)

    db.session.commit()

    return jsonify(CourseSchema().dump(course))


@app.route('/video/create', methods = ['POST'])
def create_video():
    token = request.json['token']
    name = request.json['name']
    url = request.json['url']
    size = request.json['size']
    time_in_secs = request.json['time_in_secs']
    pic_url = request.json['pic_url']
    course_id = request.json['course_id']

    if name is None or  url is None or size is None or time_in_secs is None or token is None:
        return jsonify(message='Invalid request: body must contain: name, url, time_in_secs and token'), 400

    try:
        time_in_secs = int(time_in_secs)
    except :
        return jsonify(message=' Invalid time_in_secs parameter'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 400

    if course_id is None:
        course_id = ''

    if not str(url).startswith('http'):
        return jsonify(message='Invalid media url'), 400

    video = Video(name = str(name),
                  url = str(url),
                  size = str(size),
                  time_in_secs = time_in_secs,
                  pic_url = str(pic_url),
                  course_id = course_id,
                  uploader_id = user.id,
                  clicks = 0,
                  extras = '')

    db.session.add(video)
    db.session.commit()

    if course_id != '':
        try:
            course =  db.session.query(Course).filter_by(id=course_id).first()
            course.videos.append(video)
            course.total_videos = len(db.session.query(Video).filter_by(course_id=course_id).all())
            db.session.commit()
        except:
            pass
    return jsonify(message = 'done')


@app.route('/video/update', methods = ['POST'])
def update_video():
    token = request.json['token']
    video_id = request.json['id']
    name = request.json['name']
    url = request.json['url']
    size = request.json['size']
    time_in_secs = request.json['time_in_secs']
    pic_url = request.json['pic_url']
    extras = request.json['extras']

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 400

    video = db.session.query(Video).filter_by(id = video_id).first()
    if video is None:
        return jsonify(message='Video not found'), 404

    if name is not None:
        video.name = str(name)

    if size is not None:
        video.size = str(size)

    if url is not None:
        if str(url).startswith('http'):
            video.url = url

    if pic_url is not None:
        video.pic_url = str(pic_url)

    if extras is not None:
        video.extras = extras

    if time_in_secs is not None:
        try:
            time_in_secs = int(time_in_secs)
            video.time_in_secs = time_in_secs
        except :
            print('Invalid time_in_secs')

    db.session.commit()

    return jsonify(message = 'done')


@app.route('/video/delete', methods= ['POST'])
def delete_video():
    token = request.json['token']
    video_id = request.json['id']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 400

    video = db.session.query(Video).filter_by(id=video_id).first()
    if video is None:
        return jsonify(message='Video not found'), 404

    db.session.delete(video)
    db.session.commit()

    return jsonify(message='done'), 204


@app.route('/video/fetch-latest', methods= ['POST', 'GET'])
def fetch_latest_video():
    token = request.json['token']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    latest_videos = db.session.query(Video).order_by(Video.id.desc()).limit(public_query_limit).all()

    return jsonify(VideoSchema().dump(latest_videos,many=True))


@app.route('/video/fetch-trending', methods= ['POST', 'GET'])
def fetch_trending_videos():
    token = request.json['token']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    latest_videos = db.session.query(Video).order_by(Video.clicks.desc()).limit(public_query_limit).all()

    return jsonify(VideoSchema().dump(latest_videos,many=True))


@app.route('/course/videos', methods= ['POST', 'GET'])
def fetch_course_videos():
    token = request.json['token']
    course_id = request.json['course_id']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    try:
        course_id = int(course_id)
    except:
        return jsonify('Invalid course id'), 400

    videos = db.session.query(Video).filter_by(course_id = course_id).all()

    return jsonify(VideoSchema().dump(videos,many=True))


@app.route('/video/downloadlink', methods= ['POST', 'GET'])
def download_video():
    token = request.json['token']
    video_id = request.json['video_id']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    try:
        video_id = int(video_id)
    except:
        return jsonify('Invalid video id'), 400

    video = db.session.query(Video).filter_by(id = video_id).first()
    if video is None:
        return jsonify(message='Video not found'), 404

    if int(user.admin_stat) == 0:
        click = 0
        try:
            click = int(video.clicks)
        except:
            pass
        click += 1
        video.clicks = click
        event = DownloadEvent(doc_type='video',
                    object_id=str(video.id),
                    user_id=str(user.id),
                    timestamp=datetime.datetime.utcnow())
        db.session.add(event)

    db.session.commit()

    return jsonify({'link': video.url})


@app.route('/document/create', methods = ['POST'])
def create_document():
    token = request.json['token']
    name = request.json['name']
    description = request.json['description']
    doctype = request.json['doctype']
    size = request.json['size']
    course_id = request.json['course_id']
    url = request.json['url']
    extras = request.json['extras']

    if name is None or  url is None or size is None or doctype is None or token is None:
        return jsonify(message='Invalid request: body must contain: name, url, time_in_secs and token'), 400

    if len(doctype) == 0:
        return jsonify(message=' Invalid  document type [doctype]'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 404

    if course_id is None:
        course_id = ''

    if description is None:
        description = ''

    if not str(url).startswith('http'):
        return jsonify(message='Invalid media url'), 404

    document = Document(
                    name = str(name),
                  description = description if description is not None else '',
                  size = str(size),
                  doctype = str(doctype),
                    url = str(url),
                  clicks = 0,
                  extras = extras if extras is not None else '')

    db.session.add(document)
    db.session.commit()

    if course_id != '':
        try:
            course = db.session.query(Course).filter_by(id=course_id).first()
            if doctype == 'tut':
                course.materials.append(document)
                course.total_tutorials = len(db.session.query(Document).filter_by(course_id = course_id).filter_by(doctype = doctype).all())
            elif doctype == 'pq':
                course.past_questions.append(document)
                course.total_past_questions = len(db.session.query(Document).filter_by(course_id=course_id).filter_by(doctype = doctype).all())
            db.session.commit()
        except:
            print('add course error')

    return jsonify(message = 'done')


@app.route('/document/update', methods = ['POST'])
def update_document():
    token = request.json['token']
    doc_id = request.json['id']
    name = request.json['name']
    url = request.json['url']
    size = request.json['size']
    extras = request.json['extras']

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 404

    document = db.session.query(Document).filter_by(id = doc_id).first()
    if document is None:
        return jsonify(message='Document not found'), 404

    if name is not None:
        document.name = str(name)

    if size is not None:
        document.size = str(size)

    if url is not None:
        if str(url).startswith('http'):
            document.url = url

    if extras is not None:
        document.extras = extras

    db.session.commit()

    return jsonify(message = 'done')


@app.route('/document/delete', methods= ['POST'])
def delete_document():
    token = request.json['token']
    doc_id = request.json['id']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 404

    document = db.session.query(Document).filter_by(id=doc_id).first()
    if document is None:
            return jsonify(message='Document not found'), 404

    db.session.delete(document)
    db.session.commit()

    return jsonify(message='done'), 204


@app.route('/document/downloadlink', methods= ['POST', 'GET'])
def download_document():
    token = request.json['token']
    doc_id = request.json['doc_id']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    try:
        doc_id = int(doc_id)
    except:
        return jsonify('Invalid video id'), 400

    document = db.session.query(Document).filter_by(id = doc_id).first()
    if document is None:
        return jsonify(message='Document not found'), 404



    if int(user.admin_stat) == 0:
        click = 0
        try:
            click = int(document.clicks)
        except:
            pass
        click += 1
        document.clicks = click

        event = DownloadEvent(doc_type=document.doctype,
                    object_id=str(document.id),
                    user_id=str(user.id),
                    timestamp=datetime.datetime.utcnow())

        db.session.add(event)

    db.session.commit()

    return jsonify({'link': document.url})


@app.route('/document/fetch-trending', methods= ['POST', 'GET'])
def fetch_trending_documents():
    token = request.json['token']
    doctype = request.json['doctype']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    if doctype is None:
        docs = db.session.query(Document).order_by(Document.clicks.desc()).limit(public_query_limit).all()
    else:
        docs = db.session.query(Document).filter_in(doctype = doctype).order_by(Document.clicks.desc()).limit(public_query_limit).all()

    return jsonify(DocumentSchema().dump(docs,many=True))


@app.route('/document/fetch-latest', methods= ['POST', 'GET'])
def fetch_latest_documents():
    token = request.json['token']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    latest_docs = db.session.query(Document).order_by(Document.id.desc()).limit(public_query_limit).all()

    return jsonify(DocumentSchema().dump(latest_docs,many=True))


@app.route('/course/document', methods= ['POST', 'GET'])
def fetch_course_documents():
    token = request.json['token']
    course_id = request.json['course_id']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    docs = db.session.query(Document).filter_by(course_id = course_id).all()

    return jsonify(DocumentSchema().dump(docs,many=True))

# CBT Functions

@app.route('/cbt/create', methods = ['POST'])
def create_cbt():
    token = request.json['token']
    course_id = request.json['course_id']
    name = request.json['name']
    description = request.json['description']
    data = request.json['data']

    if name is None:
        return jsonify(message='Invalid request: body must contain: name'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 404

    if course_id is None:
        course_id = ''


    cbt = CBT(name = str(name),
                  data = str(data) if data is not None else '',
                  description = str(description) if description is not None else '',
                  course_id = str(course_id) if course_id is not None else '',
                  clicks = 0)

    db.session.add(cbt)
    db.session.commit()

    if course_id != '':
        try:
            course = db.session.query(Course).filter_by(id=course_id).first()
            course.cbt.append(cbt)
            db.session.commit()
        except:
            pass
    return jsonify(message = 'done')


@app.route('/cbt/update', methods = ['POST'])
def update_cbt():
    token = request.json['token']
    id = request.json['id']
    name = request.json['name']
    description = request.json['description']
    data = request.json['data']

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 400

    cbt = db.session.query(CBT).filter_by(id = id).first()
    if cbt is None:
        return jsonify(message='CBT not found'), 404

    if name is not None:
        cbt.name = str(name)

    if data is not None:
        cbt.data = str(data)

    if description is not None:
        cbt.description = str(description)

    db.session.commit()

    return jsonify(message = 'done')


@app.route('/cbt/delete', methods= ['POST'])
def delete_cbt():
    token = request.json['token']
    cbt_id = request.json['id']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 400

    cbt = db.session.query(CBT).filter_by(id=cbt_id).first()
    if cbt is None:
            return jsonify(message='CBT not found'), 404

    db.session.delete(cbt)
    db.session.commit()

    return jsonify(message='done'), 204


@app.route('/course/cbt', methods= ['POST', 'GET'])
def fetch_course_cbts():
    token = request.json['token']
    course_id = request.json['course_id']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    cbts = db.session.query(CBT).filter_by(course_id = course_id).all()

    return jsonify(CBTSchema().dump(cbts,many=True))


@app.route('/cbt/fetch-trending', methods= ['POST', 'GET'])
def fetch_trending_cbts():
    token = request.json['token']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    cbts = db.session.query(CBT).order_by(CBT.clicks.desc()).limit(public_query_limit).all()

    return jsonify(CBTSchema().dump(cbts,many=True))


@app.route('/cbt/fetch-latest', methods= ['POST', 'GET'])
def fetch_latest_cbts():
    token = request.json['token']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    latest_cbts = db.session.query(CBT).order_by(CBT.id.desc()).limit(public_query_limit).all()

    return jsonify(CBTSchema().dump(latest_cbts,many=True))


@app.route('/cbt/downloadlink', methods= ['POST', 'GET'])
def download_cbt():
    token = request.json['token']
    cbt_id = request.json['cbt_id']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    try:
        cbt_id = int(cbt_id)
    except:
        return jsonify('Invalid CBT id'), 400

    cbt = db.session.query(CBT).filter_by(id = cbt_id).first()
    if CBT is None:
        return jsonify(message='CBT not found'), 404

    if int(user.admin_stat) == 0:
        click = 0
        try:
            click = int(cbt.clicks)
        except:
            pass
        click += 1
        cbt.clicks = click
        event = DownloadEvent(doc_type='cbt',
                    object_id=str(cbt.id),
                    user_id=str(user.id),
                    timestamp=datetime.datetime.utcnow())
        db.session.add(event)

    db.session.commit()

    return jsonify({'link': cbt.url})


# News APIs

@app.route('/news/create', methods = ['POST'])
def create_news():
    token = request.json['token']
    title = request.json['title']
    description = request.json['description']
    user_id = request.json['user_id']
    extras = request.json['extras']

    if token is None:
        return jsonify(message='Invalid request: body must contain: `title` and `token`.'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 404

    news = News(
        title = str(title),
                  description = str(description) if description is not None else '',
                  user_id = str(user_id) if user_id is not None else '',
                  extras = str(extras) if extras is not None else '',
                  timestamp = datetime.datetime.utcnow())

    db.session.add(news)
    db.session.commit()

    return jsonify(NewsSchema().dump(news))


@app.route('/news/update', methods = ['PATCH'])
def update_news():
    try:
        token = request.json['token']
        id = request.json['id']
        title = request.json['title']
        description = request.json['description']
        extras = request.json['extras']
        user_id = request.json['user_id']
    except:
        return jsonify(message="Incomplete paraneters"), 400

    if token is None:
        return jsonify(message='Invalid request: body must contain: `title` and `token`.'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 404

    news = db.session.query(News).filter_by(id=id).first()
    if news is None:
        return jsonify(message='News not found'), 404

    if title is not None:
        news.title = title

    if description is not None:
        news.description = description

    if extras is not None:
        news.extras = extras

    if user_id is not None:
        news.user_id = user_id

    db.session.commit()

    return jsonify(NewsSchema().dump(news))


@app.route('/news/delete', methods = ['DELETE'])
def delete_news():
    token = request.json['token']
    id = request.json['id']

    if token is None:
        return jsonify(message='Invalid request: body must contain: `title` and `token`.'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 404

    news = db.session.query(News).filter_by(id=id).first()
    if news is None:
        return jsonify(message='News not found'), 404

    db.session.delete(news)
    db.session.commit()

    return  jsonify(message='done'), 204


@app.route('/news/fetch-latest', methods= ['POST', 'GET'])
def fetch_latest_news():
    token = request.json['token']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    latest_news = db.session.query(News).order_by(News.id.desc()).limit(public_query_limit).all()

    return jsonify(NewsSchema().dump(latest_news,many=True))


@app.route('/news/inbox', methods= ['POST', 'GET'])
def fetch_user_inbox():
    token = request.json['token']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    inbox = db.session.query(News).filter(user_id = str(user.id)).all()

    # TODO: Confirm client satisfaction
    for news in inbox:
        db.session.delete(news)
    db.session.commit()

    return jsonify(NewsSchema().dump(inbox,many=True))

# ADVERT Functions

@app.route('/advert/create', methods = ['POST'])
def create_advert():
    token = request.json['token']
    text = request.json['text']
    image_url = request.json['image_url']
    action_link = request.json['action_link']
    mode = request.json['mode']

    if token is None or text is None:
        return jsonify(message='Invalid request: body must contain: `text` and `token`.'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 404

    advert = Advert(
                 text = str(text),
                  image_url = str(image_url) if image_url is not None else '',
                  action_link = str(action_link) if action_link is not None else '',
                  mode = str(mode) if mode is not None else '',
                  timestamp = datetime.datetime.utcnow())

    db.session.add(advert)
    db.session.commit()

    return jsonify( AdSchema().dump(advert))


@app.route('/advert/update', methods = ['PATCH'])
def update_advert():
    token = request.json['token']
    id = request.json['id']
    text = request.json['text']
    image_url = request.json['image_url']
    action_link = request.json['action_link']
    mode = request.json['mode']

    if token is None :
        return jsonify(message='Invalid request: body must contain: `token`.'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 404

    advert = db.session.query(Advert).filter_by(id=id).first()

    if text is not None:
        advert.text = text

    if image_url is not None:
        advert.image_url = image_url

    if action_link is not None:
        advert.action_link = action_link

    if mode is not None:
        advert.mode = mode

    db.session.commit()

    return jsonify(AdSchema().dump(advert))


@app.route('/advert/delete', methods = ['DELETE'])
def delete_advert():
    token = request.json['token']
    id = request.json['id']

    if token is None:
        return jsonify(message='Invalid request: body must contain: `title` and `token`.'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404
    elif user.admin_stat == 0:
        return jsonify(message='Unauthorised user'), 404

    advert = db.session.query(Advert).filter_by(id=id).first()
    if advert is None:
        return jsonify(message='Advert not found'), 404

    db.session.delete(advert)
    db.session.commit()

    return  jsonify(message='done'), 204


@app.route('/advert/fetch-latest', methods= ['POST', 'GET'])
def fetch_latest_ads():
    token = request.json['token']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404

    latest_ads = db.session.query(Advert).order_by(Advert.id.desc()).limit(public_query_limit).all()

    return jsonify(AdSchema().dump(latest_ads,many=True))

# Calendar Functions

@app.route('/calendar/event/create', methods = ['POST'])
def create_calevent():
    token = request.json['token']
    date_of_activity = request.json['date_of_activity']
    activity = request.json['activity']


    if token is None or date_of_activity is None:
        return jsonify(message='Invalid request: body must contain: `token` and `date_of_activity`.'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404

    date_data = str(date_of_activity).split(',')
    if len(date_of_activity) < 5:
        return jsonify(message='Invalid request format: `date_of_activity`.'), 400

    try:
        date = datetime.datetime(int(date_data[0]), int(date_data[1]), int(date_data[2]), int(date_data[3]), int(date_data[4]))
    except:
        return jsonify(message='Invalid request format: `date_of_activity`.'), 400

    calevent = CalenderEvent(
                 activity = str(activity),
                  user_id = str(user.id) ,
                    date_of_activity = date,
                  date_created = datetime.datetime.utcnow())

    db.session.add(calevent)
    db.session.commit()

    return jsonify(message = 'done')


@app.route('/calendar/event/update', methods = ['POST'])
def update_calevent():
    token = request.json['token']
    id = request.json['id']
    activity = request.json['activity']


    if token is None:
        return jsonify(message='Invalid request: body must contain: token.'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404

    calevent = db.session.query(CalenderEvent).filter_by(id=id).first()
    if calevent is None :
        return jsonify(message='Event not found'), 404

    if activity is not None:
        calevent.activity = activity

    db.session.commit()

    return jsonify(message = 'done')


@app.route('/calendar/event/delete', methods = ['POST'])
def delete_calevent():
    token = request.json['token']
    id = request.json['id']

    if token is None:
        return jsonify(message='Invalid request: body must contain: token.'), 400

    user = db.session.query(User).filter_by(token = token).first()
    if user is None :
        return jsonify(message='User not found'), 404

    calevent = db.session.query(CalenderEvent).filter_by(id=id).first()
    if calevent is None :
        return jsonify(message='Event not found'), 404

    db.session.delete(calevent)
    db.session.commit()

    return jsonify(message = 'done') , 204


@app.route('/calendar/fetch-period', methods= ['POST', 'GET'])
def fetch_latest_calevent():
    token = request.json['token']
    start = request.json['start']
    end = request.json['end']

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404
    # posts = Post.query.filter(Post.post_time <= end).filter(Post.post_time >= start)
    start_time = datetime.datetime(2000)
    if start is not None:
        date_data = str(start).split(',')
        if len(date_data) >= 5:
            try:
                start_time = datetime.datetime(int(date_data[0]), int(date_data[1]), int(date_data[2]),
                                         int(date_data[3]), int(date_data[4]))
            except:
                # return jsonify(message='Invalid request format: `date_of_activity`.'), 400
                pass

    end_time = datetime.datetime(2100)
    if end is not None:
        date_data = str(start).split(',')
        if len(date_data) >= 5:
            try:
                end_time = datetime.datetime(int(date_data[0]), int(date_data[1]), int(date_data[2]),
                                         int(date_data[3]), int(date_data[4]))
            except:
                # return jsonify(message='Invalid request format: `date_of_activity`.'), 400
                pass

    calendar = db.session.query(CalenderEvent).filter(CalenderEvent.user_id == str(user.id)).\
        filter(CalenderEvent.date_of_activity >= start_time).filter(CalenderEvent.date_of_activity <= end_time).all()

    return jsonify(CalendarSchema().dump(calendar,many=True))


@app.route('/search', methods= ['POST', 'GET'])
def search_tables():
    token = request.json['token']
    tables = request.json['tables']
    text = request.json['text']

    if text is None or len(str(text).strip()) == 0:
        return jsonify(message='Invalid request text'), 400

    user = db.session.query(User).filter_by(token=token).first()
    if user is None:
        return jsonify(message='User not found'), 404
    courses = []
    cbts = []
    docs = []
    videos = []

    if 'course' in tables or tables is None or str(tables).strip() == '':
        courses = Course.query.whoosh_search(text).all()

    if 'cbt' in tables or tables is None or str(tables).strip() == '':
        cbts = CBT.query.whoosh_search(text).limit(public_query_limit).all()

    if 'doc' in tables or tables is None or str(tables).strip() == '':
        docs = Document.query.whoosh_search(text).limit(public_query_limit).all()

    if 'video' in tables or tables is None or str(tables).strip() == '':
        videos = Video.query.whoosh_search(text).limit(public_query_limit).all()

    videos = list(VideoSchema().dump(videos, many= True))
    cbts = list(CBTSchema().dump(cbts, many= True))
    docs =list( DocumentSchema().dump(docs, many= True))
    courses = list(CourseSchema().dump(courses, many= True))

    for item in videos:
        endex = (len(courses) - 1) if len(courses) > 0 else 0
        courses.insert(random.randint(0,endex), item)

    for item in cbts:
        endex = (len(courses) - 1) if len(courses) > 0 else 0
        courses.insert(random.randint(0,endex), item)

    for item in docs:
        endex = (len(courses) - 1) if len(courses) > 0 else 0
        courses.insert(random.randint(0,endex), item)

    for item in videos:
        endex = (len(courses) - 1) if len(courses) > 0 else 0
        courses.insert(random.randint(0,endex), item)

    return jsonify(courses)


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
