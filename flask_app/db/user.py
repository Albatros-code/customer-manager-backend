import re
import secrets
import mongoengine
import requests
import json
import random

from passlib.hash import pbkdf2_sha256 as sha256

from flask_app.db.base import BaseDocument


def validate_phone(phone):
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

    if not re.search("^\\d{2}$", val):
        raise mongoengine.ValidationError("Not valid age.")


def validate_password(val: str):
    if len(val) < 60:
        raise mongoengine.ValidationError("Wrong password.")


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

    def save(self, new_password_check: bool = False, *args, **kwargs):
        errors = validate_new_password(self, new_password_check)
        super().save(errors=errors)

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

    # def validate_new_password(self):
    #     validate_new_password(self.password)
    @classmethod
    def generate_random_user(cls):
        random_name = requests.get("https://randomuser.me/api/?nat=gb&inc=name")
        login = f'user{random.randint(100000, 999999)}'

        user_data = UserData(
            phone=f'{random.randint(100000000, 999999999)}',
            fname=json.loads(random_name.text)['results'][0]['name']['first'],
            lname=json.loads(random_name.text)['results'][0]['name']['last'],
            email=f'{login}@email.com',
            age=f'{random.randint(20, 70)}',
        )
        user_settings = UserSettings(
            newsletter=False
        )
        user_parameters = UserParameters(
            email_verified=True,
            email_verification_string='emailverificationstring',
        )
        user = cls(
            role='user',
            username=login,
            password='password',
            data=user_data,
            settings=user_settings,
            parameters=user_parameters,
        )

        return user


def validate_new_password(doc: User, validate: bool = False):
    if not validate: return {}

    if len(doc.password) < 8:
        # raise mongoengine.ValidationError("8 digit required.")
        return {"password": {doc.password: "8 digit required"}}

    doc.password = doc.generate_hash(doc.password)
