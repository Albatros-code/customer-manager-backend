import re
import secrets
import mongoengine

from passlib.hash import pbkdf2_sha256 as sha256

from flask_app.db.base import BaseDocument


def validate_phone(phone):
    # phone structure
    if not re.search("^\\d{9}$", phone):
        raise mongoengine.ValidationError("9 digit number required.")


def validate_fname(val: str):
    if not re.search("^[A-Za-z]*$", val):
        raise mongoengine.ValidationError("Not valid first name.")


def validate_lname(val: str):
    if not re.search("^[A-Za-z]+$|^[A-Za-z]+-[A-Za-z]+$", val):
        raise mongoengine.ValidationError("Not valid last name.")


def validate_email(val: str):
    if not re.search("(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\\\])", val):
        raise mongoengine.ValidationError("Not valid email.")


def validate_age(val):
    pass
    # if val == '11':
    #     raise mongoengine.ValidationError("Age must be two digit.")


def validate_password(val: str):
    if len(val) < 8:
        raise mongoengine.ValidationError("8 digit required.")


class UserData(mongoengine.EmbeddedDocument):
    phone = mongoengine.StringField(unique=True, validation=validate_phone)
    fname = mongoengine.StringField(validation=validate_fname)
    lname = mongoengine.StringField(validation=validate_lname)
    email = mongoengine.EmailField(unique=True, validation=validate_email)
    age = mongoengine.StringField(validation=validate_age)


class UserSettings(mongoengine.EmbeddedDocument):
    newsletter = mongoengine.BooleanField(default=False)


class UserParameters(mongoengine.EmbeddedDocument):
    email_verified = mongoengine.BooleanField(default=False)
    email_verification_string = mongoengine.StringField(default=''.join(secrets.token_hex(16)))


USER_ROLE = ('user', 'admin')


# class User(mongoengine.Document):
class User(BaseDocument):
    role = mongoengine.StringField(choices=USER_ROLE, default='user')
    username = mongoengine.StringField(unique=True)
    password = mongoengine.StringField(min_length=8, validation=validate_password)
    data = mongoengine.EmbeddedDocumentField(UserData)
    settings = mongoengine.EmbeddedDocumentField(UserSettings)
    parameters = mongoengine.EmbeddedDocumentField(UserParameters)

    # def clean(self):
    #     errors = self.validate_doc()
    #     if errors:
    #         raise Exception(errors)


    @staticmethod
    def get_unique_fields():
        return ['username', 'data__phone', 'data__email']

    # Generate hash from password by encryption using sha256
    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    # Verify hash and password
    @staticmethod
    def verify_hash(password, hash_):
        return sha256.verify(password, hash_)
