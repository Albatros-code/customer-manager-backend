import mongoengine
from passlib.hash import pbkdf2_sha256 as sha256


class ResetPassword(mongoengine.Document):
    username = mongoengine.StringField()
    token = mongoengine.StringField()
    date = mongoengine.StringField()

    # Generate hash from password by encryption using sha256
    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    # Verify hash and password
    @staticmethod
    def verify_hash(password, hash_):
        return sha256.verify(password, hash_)
