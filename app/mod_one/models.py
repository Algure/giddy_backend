# Import the database object (db) from the main application module
from sqlalchemy.orm import relationship

from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Table, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean

Base = declarative_base()
ma = Marshmallow()
db = SQLAlchemy()


video_course_table = Table('video_course_table', db.Model.metadata,
    Column('course_id', ForeignKey('course.id')),
    Column('video_id', ForeignKey('video.id'))
)

tutorials_course_table = Table('tutorials_course_table', db.Model.metadata,
    Column('course_id', ForeignKey('course.id'), primary_key=True),
    Column('document_id', ForeignKey('document.id'), primary_key=True)
)

pq_course_table = Table('pq_course_table', db.Model.metadata,
    Column('course_id', ForeignKey('course.id'), primary_key=True),
    Column('document_id', ForeignKey('document.id'), primary_key=True)
)

cbt_course_table = Table('cbt_course_table', db.Model.metadata,
    Column('course_id', ForeignKey('course.id')),
    Column('cbt_id', ForeignKey('cbt.id'))
)

video_bookmarks_table = Table('video_bookmarks_table', db.Model.metadata,
    Column('users_id', ForeignKey('users.id')),
    Column('video_id', ForeignKey('video.id'))
)

document_bookmarks_table = Table('document_bookmarks_table', db.Model.metadata,
    Column('users_id', ForeignKey('users.id'), primary_key=True),
    Column('Document_id', ForeignKey('document.id'), primary_key=True)
)

course_bookmarks_table = Table('course_bookmarks_table', db.Model.metadata,
    Column('users_id', ForeignKey('users.id'), primary_key=True),
    Column('course_id', ForeignKey('course.id'), primary_key=True)
)

cbt_bookmarks_table = Table('cbt_bookmarks_table', db.Model.metadata,
    Column('users_id', ForeignKey('users.id'), primary_key=True),
    Column('cbt_id', ForeignKey('cbt.id'), primary_key=True)
)

association_table = Table('association', Base.metadata,
    Column('left_id', ForeignKey('left.id')),
    Column('right_id', ForeignKey('right.id'))
)

class Parent(Base):
    __tablename__ = 'left'
    id = Column(Integer, primary_key=True)
    children = relationship("Child",
                    secondary=association_table)

class Child(Base):
    __tablename__ = 'right'
    id = Column(Integer, primary_key=True)

class Department(db.Model):
    __tablename__ = 'faculty'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    school_id = Column(String)
    faculty_id = Column(String)

class Faculty(db.Model):
    __tablename__ = 'faculty'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    school_id = Column(String)
    faculties = relationship("Department", cascade="all, delete-orphan")

class School(db.Model):
    __tablename__ = 'school'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    faculties = relationship("Faculty", cascade="all, delete-orphan")


class Course(db.Model):
    __searchable__ = ['name','description','school','dept']
    __tablename__ = 'course'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    dept = Column(String)
    dept_id = Column(String)
    faculty = Column(String)
    faculty_id = Column(String)
    school = Column(String)
    school_id = Column(String)
    description = Column(String)
    category = Column(String)
    pic_url = Column(String)
    uploader_id = Column(String)
    is_published = Column(Boolean)
    total_tutorials = Column(Integer)
    total_past_questions = Column(Integer)
    total_videos = Column(Integer)
    clicks = Column(Integer)
    extras = Column(String)
    tutorials = relationship("Document", secondary=tutorials_course_table)
    past_questions = relationship("Document", secondary=pq_course_table)
    videos = relationship("Video", secondary=video_course_table)
    cbt = relationship("CBT", secondary=cbt_course_table )

class Video(db.Model):
    __searchable__ = ['name']
    # __tablename__ = 'video'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    size = Column(String)
    time_in_secs = Column(Integer)
    pic_url = Column(String)
    course_id = Column(String)
    uploader_id = Column(String)
    clicks = Column(Integer)
    extras = Column(String)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'))


class Document(db.Model):
    __searchable__ = ['name','description']
    # __tablename__ = 'document'
    id = Column(Integer, primary_key= True)
    name = Column(String)
    description = Column(String)
    doctype = Column(String)
    size = Column(String)
    course_id = Column(String)
    url = Column(String)
    clicks = Column(Integer)
    extras = Column(String)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))


class CBT(db.Model):
    __searchable__ = ['name','description']
    __tablename__ = 'cbt'
    id = Column(Integer, primary_key= True)
    name = Column(String)
    description = Column(String)
    data = Column(String)
    course_id = Column(String)
    clicks = Column(Integer)


class News(db.Model):
    __seachable__ = ['title','description',]
    __tablename__ = 'news'
    id = Column(Integer, primary_key= True)
    title = Column(String)
    description = Column(String)
    user_id = Column(String)
    timestamp = Column(DateTime)
    extras = Column(String)


class Advert(db.Model):
    __tablename__ = 'advert'
    id = Column(Integer, primary_key= True)
    text = Column(String)
    image_url = Column(String)
    action_link = Column(String)
    mode = Column(String)
    timestamp = Column(DateTime)


class CalenderEvent(db.Model):
    __tablename__ = 'calenderevent'
    id = Column(Integer, primary_key= True)
    date_created = Column(DateTime)
    date_of_activity = Column(DateTime)
    activity = Column(String)
    user_id = Column(String)


class DownloadEvent(db.Model):
    __tablename__ = 'downloadevent'
    id = Column(Integer, primary_key= True)
    doc_type = Column(String)
    object_id = Column(String)
    timestamp = Column(DateTime)
    user_id = Column(String)


class Category(db.Model):
    __tablename__ = 'category'
    id = Column(Integer, primary_key= True)
    name = Column(String)


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

class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique= True)
    password = Column(String)
    token = Column(String)
    admin_stat = Column(Integer)
    # Migration 2
    verification_status = Column(String)
    education_level = Column(String)
    verification_date = Column(DateTime)
    school_name = Column(String)
    school_id = Column(String)
    faculty_name = Column(String)
    faculty_id = Column(String)
    department_name = Column(String)
    department_id = Column(String)
    level = Column(String)
    matric_no = Column(String)
    date_of_birth = Column(String)
    phone_number = Column(String)
    pin = Column(String)
    course_form_url = Column(String)

    ######################
    reflink = Column(String)
    video_bookmarks = relationship("Video", secondary= video_bookmarks_table)
    document_bookmarks =  relationship("Document", secondary = document_bookmarks_table)
    course_bookmarks = relationship("Course", secondary = course_bookmarks_table)
    cbt_bookmarks = relationship("CBT", secondary = cbt_bookmarks_table)


class UserSchema(ma.Schema):
    class Meta:
        fields = ['id', 'first_name', 'last_name', 'email','admin_stat','token','reflink','course_form_url','pin','phone_number','date_of_birth','matric_no','level','department_id','department_name','faculty_id','faculty_name','school_id','school_name','verification_date','education_level','verification_status']

class CalendarSchema( ma.Schema):
    class Meta:
        fields = ['id', 'date_created', 'date_of_activity', 'activity']

class CourseSchema( ma.Schema):
    class Meta:
        fields = ['id', 'name', 'dept', 'school', 'description', 'is_published','total_videos','extras','total_past_questions',
                  'category','total_tutorials', 'pic_url',  'clicks', 'uploader_id']

class AdSchema( ma.Schema):
    class Meta:
        fields = ['id', 'text', 'image_url', 'action_link', 'mode', 'timestamp']

class CBTSchema( ma.Schema):
    class Meta:
        fields = ['id', 'name', 'clicks', 'description']

class NewsSchema( ma.Schema):
    class Meta:
        fields = ['id', 'title', 'description', 'user_id', 'timestamp', 'extras']

class DocumentSchema( ma.Schema):
    class Meta:
        fields = ['id', 'name', 'description', 'doctype', 'size', 'clicks', 'extras']

class VideoSchema( ma.Schema):
    class Meta:
        fields = ['id', 'name', 'size', 'time_in_secs', 'extras',  'pic_url', 'course_id', 'clicks', 'uploader_id']

class PlanetSchema( ma.Schema):
    class Meta:
        fields = ['planet_id', 'planet_name', 'planet_type', 'home_star', 'mass', 'radius', 'distance']


class DepartmentSchema( ma.Schema):
    class Meta:
        fields = ['id', 'name', 'faculty_id', 'school_id']

class FacultySchema( ma.Schema):
    class Meta:
        fields = ['id', 'name', 'school_id']

class SchoolSchema( ma.Schema):
    class Meta:
        fields = ['id', 'name']

