import datetime
import math
import secrets
import json

from flask_restful import Resource, reqparse
from flask import Response, make_response
from mongoengine import ValidationError, NotUniqueError
from pymongo.errors import DuplicateKeyError

from .mongoDB import User, RevokedToken
from . import mongoDB as db
from . import util as util
from . import emails

# import pytz
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    set_refresh_cookies,
    unset_jwt_cookies,
)

from flask_cors import cross_origin

parser_register = reqparse.RequestParser()
parser_register.add_argument('username', help='This field cannot be blank', required=True)
parser_register.add_argument('password', help='This field cannot be blank', required=True)
parser_register.add_argument('email', help='This field cannot be blank', required=True)
parser_register.add_argument('phone', help='This field cannot be blank', required=True)
parser_register.add_argument('fname', help='This field cannot be blank', required=True)
parser_register.add_argument('lname', help='This field cannot be blank', required=True)


class UserRegistration(Resource):
    @cross_origin()
    def post(self):
        data = parser_register.parse_args()

        # Check uniqueness of username, email and phone
        errors = {}
        for key_name in ['username', 'email', 'phone']:
            try:
                field = User.objects(**{key_name: data[key_name]}).get()
                if field:
                    errors[key_name] = '{} is already taken.'.format(data[key_name])
            except:
                pass

        if errors != {}:
            return {'errors': errors}, 400

        email_verification_string = ''.join(secrets.token_hex(16))

        user_data = db.UserData(
            email=data['email'],
            phone=data['phone'],
            fname=data['fname'],
            lname=data['lname'],
        )

        user_parameters = db.UserParameters(
            email_verification_string=email_verification_string,
        )

        new_user = User(
            username=data['username'],
            password=User.generate_hash(data['password']),
            data=user_data,
            parameters=user_parameters,
        )
        try:
            new_user.save()
            # saved_user = db.User.objects(username=data['username']).get()
            # email_verification_string = saved_user.id
            emails.send_verification_email(data['email'], email_verification_string)
            return {'message': 'User {} was created.'.format(data['username'])}

        except:
            return {'error': 'Something went wrong'}, 400


parser_login = reqparse.RequestParser()
parser_login.add_argument('username', help='This field cannot be blank', required=True)
parser_login.add_argument('password', help='This field cannot be blank', required=True)


class UserLogin(Resource):
    @cross_origin()
    def post(self):
        data = parser_login.parse_args()
        # Check if username exist
        try:
            current_user = db.User.objects(username=data['username']).get()
        except:
            # return {'errors': {'username': 'User {} doesn\'t exist'.format(data['username'])}}, 400
            return {'errors': {'general': 'Wrong credentials.'}}, 400

        if not User.verify_hash(data['password'], current_user.password):
            # return {'errors': {'password': 'Wrong password'}}, 400
            return {'errors': {'general': 'Wrong credentials.'}}, 400

        if not current_user.parameters.email_verified:
            return {'errors': {'general': 'Email not verified'}}, 400

        identity = {
            'username': data['username'],
            'role': current_user.role,
            # 'data': {
            #     'name': 'John',
            #     'phoneNumber': '123-456-789',
            # }
        }
        access_token = create_access_token(identity=identity).decode('utf-8')
        refresh_token = create_refresh_token(identity=identity).decode('utf-8')

        resp = make_response(
            {
                'message': 'Logged in as {}'.format(current_user.username),
                'access_token': access_token,
                'user_data': current_user.data.to_mongo()
            }, 200
        )

        # resp.set_cookie('refresh_token_cookie', value = refresh_token, httponly=True)
        set_refresh_cookies(resp, refresh_token)

        return resp

    # def options(self):
    #     return 200, {'Access-Control-Allow-Credentials': 'true'}


class UserLogoutAccess(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()['jti']
        try:
            revoked_token = RevokedToken(jti=jti)
            revoked_token.save()
            return {'message': 'Access token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogoutRefresh(Resource):
    @cross_origin()
    @jwt_required(refresh=True)
    def post(self):
        jti = get_jwt()['jti']
        exp = get_jwt()['exp']
        try:
            revoked_token = RevokedToken(
                jti=jti,
                expiration_date=datetime.datetime.fromtimestamp(exp, datetime.timezone.utc).isoformat()
            )
            revoked_token.save()

            resp = make_response({'message': 'Refresh token has been revoked'})
            unset_jwt_cookies(resp)
            return resp, 200
        except:
            return {'message': 'Something went wrong'}, 500


class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        identity = get_jwt_identity()
        current_user = db.User.objects(username=identity['username']).get()
        access_token = create_access_token(identity=identity).decode('utf-8')
        return {'access_token': access_token,
                'user_data': current_user.data.to_mongo()}


class UserEmailVerify(Resource):
    def get(self, email_verification_string):
        # user_id = email_verification_string
        try:
            user = db.User.objects(parameters__email_verification_string=email_verification_string).get()
        except:
            return {'error': 'Verification string {} doesn\'t match any user'.format(email_verification_string)}, 400

        if not user.parameters.email_verified:
            # db.User.objects(email_verification_string=email_verification_string).update_one(set__email_verified=True)
            user.parameters.email_verified = True
            user.save()
            return {'message': 'Email verified'}, 200
        else:
            return {'error': 'Email already verified'}, 400


class ResetPassword(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('action', help='This field cannot be blank', required=True)
        parser.add_argument('email')
        parser.add_argument('token')
        parser.add_argument('password')

        data = parser.parse_args()

        def return_message():
            return 200

        def send_email():
            try:
                current_user = db.User.objects(data__email=data.email).get()
            except:
                return return_message()

            rest_password_token = secrets.token_hex(16)
            rest_password = db.ResetPassword(
                username=current_user.username,
                token=db.ResetPassword.generate_hash(rest_password_token),
                date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            )
            try:
                rest_password.save()
            except:
                return return_message()

            emails.send_reset_password_email(data['email'], rest_password_token)
            return return_message()

        def change_password():
            # token_hash = db.ResetPassword.generate_hash(data.token)

            try:
                yesterday = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat()
                reset_passwords = db.ResetPassword.objects(date__gt=yesterday)

                for doc in reset_passwords:
                    if db.ResetPassword.verify_hash(data.token, doc.token):
                        current_user = db.User.objects(username=doc.username).get()
                        doc.delete()
                        break
                if not current_user: raise
            except:
                return {'message': 'token not found'}, 400

            print('change password')
            print(current_user.username)
            print(data.password)
            try:
                current_user.password = db.User.generate_hash(data.password)
                current_user.save()
            except:
                return {'message': 'password change failed'}

            return {'message': 'changing password'}, 200

        switcher = {
            "send_email": send_email,
            "change_password": change_password
        }

        action = switcher.get(data.action, return_message)

        return action()

    # def get(self):
    #     parser = reqparse.RequestParser()
    #     parser.add_argument('token')
    #     parser.add_argument('check')
    #     data = parser.parse_args()
    #
    #     if data.token:
    #         try:
    #             reset_password = db.ResetPassword.objects(token=db.ResetPassword.verify_hash(data.token)).get()
    #         except:
    #             return {'error': 'ERROR'}, 400
    #     else:
    #         return {'error': 'ERROR'}, 400
    #
    #     if bool(data.check):
    #         return {'message': 'token is valid'}
    #
    #     return {'message': f'Your token was {data.token}.'}


class UserUpdate(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', help='This field cannot be blank', required=True)
        parser.add_argument('user_data', help='This field cannot be blank', required=True)
        data = parser.parse_args()

        username = data.username
        current_user = get_jwt_identity()['username']
        current_role = get_jwt_identity()['role']
        user_data = json.loads(data.user_data)
        # print(username)
        # print(user_data)

        if username == current_user:
            user = db.User.objects(username=username).get()
            # print(user.data)
            user_data_obj = user.data
            user.elo = 'elo'

            current_user_data = {}
            for key in user_data:
                if hasattr(user_data_obj, key):
                    setattr(user_data_obj, key, user_data[key])

            # user_data_obj.age = 'age'
            # for key in user_data_obj:
            #     print(key)
            # new_user_data = db.UserData(
            #     fname='UpdatedName',
            #     lname='UpdatedName',
            #     email='email@email.com',
            #     phone='123456789'
            # )
            # user.data = new_user_data
            # user_data_obj.save()
            print(db.UserData.get_unique_fields(user_data_obj))
            try:
                user.validate()
                # user.save()
            except ValidationError as err:
                print(err)
                print(ValidationError.to_dict(err))
                return {'errors': ValidationError.to_dict(err)}, 400
            except NotUniqueError as err:
                print(err)
            # except DuplicateKeyError as err:
            #     print(err)


# not auth routes

class AllServices(Resource):
    def get(self):
        data_json = db.Service.objects.to_json()
        # current_user = get_jwt_identity()['username']
        # print(current_user)
        return Response(data_json, mimetype="application/json", status=200)


class UserHistory(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()['username']
        data_json = db.Appointment.objects(username=current_user).order_by('-date').to_json()
        return Response(data_json, mimetype="application/json", status=200)
        # return {'message': 'no elo'}, 200


parser_appointment = reqparse.RequestParser()
parser_appointment.add_argument('service', help='This field cannot be blank', required=True)
parser_appointment.add_argument('duration', help='This field cannot be blank', required=True)
parser_appointment.add_argument('date', help='This field cannot be blank', required=True)


class Appointment(Resource):
    @jwt_required()
    def post(self):
        data = parser_appointment.parse_args()
        current_user = get_jwt_identity()['username']

        new_appointment = db.Appointment(
            username=current_user,
            service=data['service'],
            duration=data['duration'],
            date=data['date'],
        )
        try:
            new_appointment.save()
            return {'message': 'Service: "{}" was scheduled for {}.'.format(data['service'], data['date'])}

        except:
            return {'error': 'Something went wrong'}, 400

    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()['username']
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        appointments = db.Appointment.objects(username=current_user, date__gt=now).order_by('date')
        data = []
        for appointment in appointments:
            appointment = {
                'service': appointment.service,
                'date': appointment.date,
                'duration': appointment.duration
            }
            data.append(appointment)

        return data, 200


class AllUsers(Resource):
    @jwt_required()
    def get(self):
        data_json = User.objects.to_json()
        return Response(data_json, mimetype="application/json", status=200)
        # return json.loads(data_json)

    def delete(self):
        return {'message': 'Delete all users'}


# admin

parser_all_appointments = reqparse.RequestParser()
parser_all_appointments.add_argument('start_date')
parser_all_appointments.add_argument('end_date')


class AllAppointments(Resource):
    @jwt_required()
    def get(self):
        data = parser_all_appointments.parse_args()
        username = get_jwt_identity()['username']
        role = get_jwt_identity()['role']
        user = db.User.objects(username=username).get()

        if user.role != role:
            return {'message': 'Unauthorized'}, 401

        if data['start_date']:
            start_date = data['start_date']
        else:
            start_date = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0,
                                                                              microsecond=0).isoformat()

        if data['end_date']:
            end_date = data['end_date']
        else:
            end_date = '3000'
            # end_date = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

        appointments = db.Appointment.objects(date__gt=start_date, date__lt=end_date).order_by('date')  # .limit(5)
        data = []
        for appointment in appointments:
            appointment = {
                'service': appointment.service,
                'date': appointment.date,
                'duration': appointment.duration
            }
            data.append(appointment)

        return data, 200


parser_available_dates = reqparse.RequestParser()
parser_available_dates.add_argument('start_hour', help='This field cannot be blank', required=True)
parser_available_dates.add_argument('end_hour', help='This field cannot be blank', required=True)
parser_available_dates.add_argument('interval', help='This field cannot be blank', required=True)


class AvailableDates(Resource):
    # @cross_origin()
    # @jwt_required()
    def post(self):
        print('-------------------- preparing available dates')
        # now = datetime.datetime.now()
        data = parser_available_dates.parse_args()

        start_hour = int(data['start_hour'])
        end_hour = int(data['end_hour'])
        interval = int(data['interval'])

        day = datetime.datetime.now()
        time_space = util.generateTimeSpace(day, start_hour, end_hour, interval)

        # now = "2021-01-21T12:00:45.363Z"
        now = datetime.datetime.now(datetime.timezone.utc).replace(hour=start_hour, minute=0, second=0, microsecond=0)
        appointments = db.Appointment.objects(date__gt=now.isoformat()).order_by('date')
        # print([item.date for item in appointments])
        for appointment in appointments:
            time_obj = util.from_ISO_string(appointment.date)
            space = math.ceil(int(appointment.duration) / interval)
            for i in range(space):
                # print(timeObj)
                try:
                    del time_space[time_obj.strftime("%Y-%m-%d")][time_obj.strftime("%H")][time_obj.strftime("%M")]
                except KeyError:
                    pass
                time_obj = time_obj + datetime.timedelta(minutes=interval)

        return time_space, 200


class SecretResource(Resource):
    @jwt_required()
    def get(self):
        return {
            'answer': 42
        }
