import mongoengine


class Service(mongoengine.Document):
    name = mongoengine.StringField()
    time = mongoengine.IntField()
    prize = mongoengine.IntField()

    # def objects(self, *args, **kwargs):