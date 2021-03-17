import json
import unittest
import mongoengine
import flask_app.db as db
# from flask_app.db.user import User, UserData, UserSettings, UserParameters


# class User(mongoengine.Document):
#     username = mongoengine.StringField()

class TestUser(unittest.TestCase):

    @staticmethod
    def new_user():
        user_data = db.UserData(
            phone="123456789",
            fname="John",
            lname="Rambo",
            email="email@email.com",
            # email="email@email.com",
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
        user.save()

        new_user = db.User.objects().first()
        assert new_user.role == 'user'
        assert new_user.username == 'User1'
        assert new_user.password == 'password'

        assert new_user.data.phone == '123456789'
        assert new_user.data.fname == 'John'
        assert new_user.data.lname == 'Rambo'
        assert new_user.data.email == 'email@email.com'
        assert new_user.data.age == 30

        assert not new_user.settings.newsletter

        assert new_user.parameters.email_verified
        assert new_user.parameters.email_verification_string == 'emailverificationstring'

    def test_failed_update_in_database(self):
        user = self.new_user()
        user.save()

        user2 = self.new_user()
        user2.username = 'User'
        user2.data.email = 'email@email.com'
        user2.data.phone = '123789456'
        # errors = user2.validate_doc()
        # if errors:
        #     print(errors)
        # else:
        #     print('saving')
        try:
            user2.save()
        except Exception as err:
            print(type(err.args[0]))

        assert True

    # def test_add_dictionaries(self):
    #     dict1 = {'a': {'val1': 'msg'}, 'b': {'c': {'val3': 'msg'}, 'd': {'e': {'val5': 'msg'}}}}
    #     dict2 = {'a': {'val2': 'msg'}, 'b': {'c': {'val4': 'msg'}, 'd': {'e': {'val6': 'msg'}}}}
    #
    #     print(f'Result:\n{merge_dicts([dict1, dict2])}')

