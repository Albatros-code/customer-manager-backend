import mongoengine


class RevokedToken(mongoengine.Document):
    jti = mongoengine.StringField()
    expiration_date = mongoengine.StringField()

    @classmethod
    def is_jti_blocklisted(cls, jti):
        query = cls.objects(jti=jti)
        return bool(query)
