import mongoengine
import os
import datetime
import secrets
from passlib.hash import pbkdf2_sha256 as sha256

db = mongoengine
db.connect('project1', host=os.environ.get('MONGO_URI'))


class User(db.Document):
    role = db.StringField(default='user')
    username = db.StringField(unique=True)
    password = db.StringField(min_length=8)
    email = db.EmailField(unique=True)
    email_verified = db.BooleanField(default=False)
    email_verification_string = db.StringField(
        default=''.join(secrets.token_hex(16)))
    phone = db.StringField(unique=True)
    fname = db.StringField()
    lname = db.StringField()

    # username=db.StringField(unique=True)
    # password=db.StringField(min_length=8),

    # Generate hash from password by encryption using sha256
    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    # Verify hash and password
    @staticmethod
    def verify_hash(password, hash_):
        return sha256.verify(password, hash_)


class ResetPassword(db.Document):
    username = db.StringField()
    token = db.StringField()
    date = db.StringField()

    # Generate hash from password by encryption using sha256
    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    # Verify hash and password
    @staticmethod
    def verify_hash(password, hash_):
        return sha256.verify(password, hash_)


class Appointment(db.Document):
    username = db.StringField()
    service = db.StringField()
    date = db.StringField()
    duration = db.StringField()


class Service(db.Document):
    name = db.StringField()
    time = db.IntField()
    prize = db.IntField()


class RevokedToken(db.Document):
    jti = db.StringField()
    expiration_date = db.StringField()


    @classmethod
    def is_jti_blocklisted(cls, jti):
        query = cls.objects(jti=jti)
        return bool(query)
