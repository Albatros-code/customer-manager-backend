import mongoengine
from flask_app.db.base import BaseDocument


def validate_duration(val):
    if not isinstance(val, int):
        raise mongoengine.ValidationError("Not valid number.")


# class Appointment(mongoengine.Document):
class Appointment(BaseDocument):
    user = mongoengine.StringField()
    service = mongoengine.StringField()
    date = mongoengine.StringField()
    duration = mongoengine.IntField(validation=validate_duration)
