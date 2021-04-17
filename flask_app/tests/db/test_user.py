import unittest
import mongoengine
import flask_app.db as db


class TestUser(unittest.TestCase):

    @staticmethod
    def new_user():
        user_data = db.UserData(
            phone="123456789",
            fname="John",
            lname="Rambo",
            email="email@email.com",
            age="30",
        )
        user_settings = db.UserSettings(
            newsletter=False
        )
        user_parameters = db.UserParameters(
            email_verified=True,
            email_verification_string='emailverificationstring',
        )
        user = db.User(
            role='user',
            username='User1',
            password='password',
            data=user_data,
            settings=user_settings,
            parameters=user_parameters,
        )

        return user

    @classmethod
    def setUp(cls):
        mongoengine.connect('mongoenginetest', host='mongomock://localhost')

    @classmethod
    def tearDown(cls):
        mongoengine.disconnect()

    def test_save_user_to_database(self):
        user = self.new_user()
        user.save(new_password_check=True)

        new_user = db.User.objects().first()
        assert new_user.role == 'user'
        assert new_user.username == 'User1'
        assert db.User.verify_hash('password', new_user.password)

        assert new_user.data.phone == '123456789'
        assert new_user.data.fname == 'John'
        assert new_user.data.lname == 'Rambo'
        assert new_user.data.email == 'email@email.com'
        assert new_user.data.age == "30"

        assert not new_user.settings.newsletter

        assert new_user.parameters.email_verified
        assert new_user.parameters.email_verification_string == 'emailverificationstring'

    def test_generate_random_user(self):
        user = db.User.generate_random_user()
        user.save(new_password_check=True)

        new_user = db.User.objects().first()
        self.assertIsNotNone(new_user)
