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


video_course_table = Table('video_course_table', Base.metadata,
    Column('Users_id', ForeignKey('Users.id')),
    Column('Video_id', ForeignKey('Video.id'))
)

tutorials_course_table = Table('tutorials_course_table', Base.metadata,
    Column('Users_id', ForeignKey('Users.id')),
    Column('Document_id', ForeignKey('Document.id'))
)

pq_course_table = Table('pq_course_table', Base.metadata,
    Column('Users_id', ForeignKey('Users.id')),
    Column('Document_id', ForeignKey('Document.id'))
)

cbt_course_table = Table('cbt_course_table', Base.metadata,
    Column('Users_id', ForeignKey('Users.id')),
    Column('CBT_id', ForeignKey('CBT.id'))
)

video_bookmarks_table = Table('video_bookmarks_table', Base.metadata,
    Column('Users_id', ForeignKey('Users.id')),
    Column('Video_id', ForeignKey('Video.id'))
)

document_bookmarks_table = Table('document_bookmarks_table', Base.metadata,
    Column('Users_id', ForeignKey('Users.id')),
    Column('Document_id', ForeignKey('Document.id'))
)

course_bookmarks_table = Table('course_bookmarks_table', Base.metadata,
    Column('Users_id', ForeignKey('Users.id')),
    Column('Course_id', ForeignKey('Course.id'))
)

cbt_bookmarks_table = Table('cbt_bookmarks_table', Base.metadata,
    Column('Users_id', ForeignKey('Users.id')),
    Column('CBT_id', ForeignKey('CBT.id'))
)

class User(db.Model):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique= True)
    password = Column(String)
    token = Column(String)
    admin_stat = Column(Integer)
    # Migration
    reflink = Column(String)
    video_bookmarks = relationship("Video", secondary= video_bookmarks_table)
    document_bookmarks = relationship("Document", secondary = document_bookmarks_table)
    course_bookmarks = relationship("Course", secondary = course_bookmarks_table)
    cbt_bookmarks = relationship("CBT", secondary = cbt_bookmarks_table)


class Video(db.Model):
    __searchable__ = ['name']
    __tablename__ = 'Video'
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


class Course(db.Model):
    __searchable__ = ['name','description','school','dept']
    __tablename__ = 'Course'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    dept = Column(String)
    school = Column(String)
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
    tutorials = relationship("Document", secondary=tutorials_course_table, cascade="all, delete-orphan")
    past_questions = relationship("Document", secondary=pq_course_table, cascade="all, delete-orphan")
    videos = relationship("Video", secondary=video_course_table, cascade="all, delete-orphan")
    cbt = relationship("CBT", secondary=cbt_course_table , cascade="all, delete-orphan")


class Document(db.Model):
    __searchable__ = ['name','description']
    __tablename__ = 'Document'
    id = Column(Integer, primary_key= True)
    name = Column(String)
    description = Column(String)
    doctype = Column(String)
    size = Column(String)
    course_id = Column(String)
    url = Column(String)
    clicks = Column(Integer)
    extras = Column(String)


class CBT(db.Model):
    __searchable__ = ['name','description']
    __tablename__ = 'CBT'
    id = Column(Integer, primary_key= True)
    name = Column(String)
    description = Column(String)
    data = Column(String)
    course_id = Column(String)
    clicks = Column(Integer)


class News(db.Model):
    __seachable__ = ['title','description',]
    __tablename__ = 'News'
    id = Column(Integer, primary_key= True)
    title = Column(String)
    description = Column(String)
    user_id = Column(String)
    timestamp = Column(DateTime)
    extras = Column(String)


class Advert(db.Model):
    __tablename__ = 'Advert'
    id = Column(Integer, primary_key= True)
    text = Column(String)
    image_url = Column(String)
    action_link = Column(String)
    mode = Column(String)
    timestamp = Column(DateTime)


class CalenderEvent(db.Model):
    __tablename__ = 'CalenderEvent'
    id = Column(Integer, primary_key= True)
    date_created = Column(DateTime)
    date_of_activity = Column(DateTime)
    activity = Column(String)
    user_id = Column(String)


class DownloadEvent(db.Model):
    __tablename__ = 'DownloadEvent'
    id = Column(Integer, primary_key= True)
    doc_type = Column(String)
    object_id = Column(String)
    timestamp = Column(DateTime)
    user_id = Column(String)


class Category(db.Model):
    __tablename__ = 'Category'
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


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email','admin_stat','token')

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
