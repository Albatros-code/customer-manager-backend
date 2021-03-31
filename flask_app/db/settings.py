import mongoengine


class Settings(mongoengine.Document):
    startHour = mongoengine.IntField()
    endHour = mongoengine.IntField()
    timeInterval = mongoengine.IntField()
