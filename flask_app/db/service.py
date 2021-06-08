import mongoengine
from flask_app.db.base import BaseDocument


def validate_name(val):
    if val == '':
        raise mongoengine.ValidationError("Can't be blank")


def validate_duration(val):
    if val == '':
        raise mongoengine.ValidationError("Can't be blank")


def validate_price(val):
    if val == '':
        raise mongoengine.ValidationError("Can't be blank")


class Service(BaseDocument):
    name = mongoengine.StringField(validation=validate_name)
    duration = mongoengine.IntField(validation=validate_duration)
    price = mongoengine.IntField(validation=validate_price)

    # def objects(self, *args, **kwargs):
