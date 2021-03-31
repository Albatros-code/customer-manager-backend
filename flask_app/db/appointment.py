import mongoengine


class Appointment(mongoengine.Document):
    user = mongoengine.StringField()
    service = mongoengine.StringField()
    date = mongoengine.StringField()
    duration = mongoengine.StringField()
