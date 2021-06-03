import mongoengine
from flask_app.db.base import BaseDocument

from flask_app.resources.utils.appointments import (
    validate_new_appointment
)


def validate_duration(val):
    if not isinstance(val, int):
        raise mongoengine.ValidationError("Not valid number.")


# def validate_date(val):
#     if isinstance(val, dict):
#         print(val)
#         # raise mongoengine.ValidationError(val['error'])
#         raise mongoengine.ValidationError("error msg")


# class Appointment(mongoengine.Document):
class Appointment(BaseDocument):
    user = mongoengine.StringField()
    service = mongoengine.StringField()
    date = mongoengine.StringField()
    duration = mongoengine.IntField(validation=validate_duration)

    def save(self, new_password_check: bool = False, *args, **kwargs):
        if not validate_new_appointment(self, allow_past=True):
            errors = {
                "date": {self.date: "Collision with other date."},
                "duration": {self.duration: "Collision with other date."},
            }
        else:
            errors = {}
        super().save(errors=errors)
