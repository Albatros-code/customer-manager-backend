import mongoengine

from flask_app.db.base import BaseDocument


def validate_hour(val):
    if type(val) == str: # or not re.search("^[0-9]+$", val):
        raise mongoengine.ValidationError("Not a number.")
    if not 24 >= val > 0:
        raise mongoengine.ValidationError("Not a valid hour.")


def validate_time_interval(val):
    if type(val) == str: # or not re.search("^[0-9]+$", val):
        raise mongoengine.ValidationError("Not a number.")
    if not 60 >= val >= 5 or 60 % val != 0:
        raise mongoengine.ValidationError("Not a valid interval.")


class Settings(BaseDocument):
    start_hour = mongoengine.IntField(validation=validate_hour)
    end_hour = mongoengine.IntField(validation=validate_hour)
    time_interval = mongoengine.IntField(validation=validate_time_interval)
    working_days = mongoengine.DictField()

    def save(self, *args, **kwargs):
        errors = validate_hours(self)
        super().save(errors=errors)


def validate_hours(doc: Settings):
    try:
        validate_hour(doc.start_hour)
        validate_hour(doc.end_hour)
    except:
        return {}

    if doc.start_hour > doc.end_hour:
        return {"start_hour": {doc.start_hour: "Bigger than end hour."},
                "end_hour": {doc.end_hour: "Smaller than start hour."}}
