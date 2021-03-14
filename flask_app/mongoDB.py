import mongoengine as db
import os
import re
import datetime
import secrets
from passlib.hash import pbkdf2_sha256 as sha256


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
