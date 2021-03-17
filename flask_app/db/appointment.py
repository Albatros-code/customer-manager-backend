import mongoengine


class Appointment(mongoengine.Document):
    username = mongoengine.StringField()
    service = mongoengine.StringField()
    date = mongoengine.StringField()
    duration = mongoengine.StringField()