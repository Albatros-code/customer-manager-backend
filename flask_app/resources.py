import datetime
import math
import os

from flask_restful import Resource, reqparse, fields, marshal_with
from flask import Response, make_response, redirect

from .mongoDB import User, RevokedToken
from . import mongoDB as db
from . import util as util
from mongoengine import NotUniqueError
# import pytz
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    jwt_refresh_token_required,
    get_jwt_identity,
    get_raw_jwt,
    set_refresh_cookies,
    unset_jwt_cookies)

from flask_cors import cross_origin

parser_login = reqparse.RequestParser()
parser_login.add_argument('username', help = 'This field cannot be blank', required = True)
parser_login.add_argument('password', help = 'This field cannot be blank', required = True)

parser_register = reqparse.RequestParser()
parser_register.add_argument('username', help = 'This field cannot be blank', required = True)
parser_register.add_argument('password', help = 'This field cannot be blank', required = True)
parser_register.add_argument('email', help = 'This field cannot be blank', required = True)
parser_register.add_argument('phone', help = 'This field cannot be blank', required = True)
parser_register.add_argument('fname', help = 'This field cannot be blank', required = True)
parser_register.add_argument('lname', help = 'This field cannot be blank', required = True)

class UserRegistration(Resource):
    @cross_origin()
    def post(self):
        data = parser_register.parse_args()

        # Check uniqueness of username, email and phone
        errors = {}
        for key_name in ['username', 'email', 'phone']:
            print(key_name)
            try:
                field = User.objects(**{key_name : data[key_name]}).get()
                if field:
                    errors[key_name] = '{} is already taken.'.format(data[key_name])
            except:
                pass
        if errors != {}:
            return {'errors': errors}, 400

        new_user = User(
            username=data['username'],
            password=User.generate_hash(data['password']),
            email=data['email'],
            phone=data['phone'],
            fname=data['fname'],
            lname=data['lname'],
            role='user'
        )
        try:
            new_user.save()
            return {'message': 'User {} was created.'.format(data['username'])}

        except:
            return {'error': 'Something went wrong'}, 400

class UserLogin(Resource):
    @cross_origin()
    def post(self):
        data = parser_login.parse_args()
        # Check if username exist
        try:
            current_user = User.objects(username = data['username']).get()
        except:
            return {'errors': {'username':'User {} doesn\'t exist'.format(data['username'])}}, 400
                
        if User.verify_hash(data['password'], current_user.password):
            identity = {
                'username': data['username'],
                'role': current_user.role,
                'data': {
                    'name': 'John',
                    'phoneNumber': '123-456-789',
                }
            }
            access_token = create_access_token(identity = identity)
            refresh_token = create_refresh_token(identity = identity)

            resp = make_response(
                {
                    'message': 'Logged in as {}'.format(current_user.username),
                    'access_token': access_token,
                    # 'refresh_token': refresh_token
                }, 200
            )
            # resp.set_cookie('refresh_token_cookie', value = refresh_token, httponly=True)
            set_refresh_cookies(resp, refresh_token)
            return resp
        else:
            return {'errors': {'password': 'Wrong password'}}, 400
    
    # def options(self):
    #     return 200, {'Access-Control-Allow-Credentials': 'true'}
      
      
class UserLogoutAccess(Resource):
    @jwt_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedToken(jti = jti)
            revoked_token.save()
            return {'message': 'Access token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500
      
      
class UserLogoutRefresh(Resource):
    @cross_origin()
    @jwt_refresh_token_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedToken(jti = jti)
            revoked_token.save()

            resp = make_response({'message': 'Refresh token has been revoked'})
            unset_jwt_cookies(resp)
            return resp, 200
        except:
            return {'message': 'Something went wrong'}, 500
      
      
class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity = current_user)
        return {'access_token': access_token}

class UserEmailVerify(Resource):
    def get(self, user_ID, verification_string):
        try:
            user = db.User.objects(id = user_ID).get()
        except:
            return {'errors': 'User {} doesn\'t exist'.format(user_ID)}, 400
        
        if verification_string == user.email_verification_string:
            db.User.objects(id = user_ID).update_one(set__email_verified=True)
            print(user.email_verification_string)
            elo = os.environ.get('FRONTEND_HOST')
            return redirect(f'{elo}/login', code=302)

# not auth routes

class AllServices(Resource):
    def get(self):
        data_json = db.Service.objects.to_json()
        # current_user = get_jwt_identity()['username']
        # print(current_user)
        return Response(data_json, mimetype="application/json", status=200)

class UserHistory(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()['username']
        data_json = db.Appointment.objects(username=current_user).to_json()
        return Response(data_json, mimetype="application/json", status=200)


parser_appointment = reqparse.RequestParser()
parser_appointment.add_argument('service', help = 'This field cannot be blank', required = True)
parser_appointment.add_argument('duration', help = 'This field cannot be blank', required = True)
parser_appointment.add_argument('date', help = 'This field cannot be blank', required = True)

class Appointment(Resource):
    @jwt_required
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
    
    @jwt_required
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
    @jwt_required
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
    @jwt_required
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
            start_date = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

        if data['end_date']:
            end_date = data['end_date']
        else:
            end_date = '3000'
            # end_date = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

        appointments = db.Appointment.objects(date__gt=start_date, date__lt=end_date).order_by('date') #.limit(5)
        data = []
        for appointment in appointments:
            appointment = {
                'service': appointment.service,
                'date': appointment.date,
                'duration': appointment.duration
            }
            data.append(appointment)

        return data, 200

parser_avaiable_dates = reqparse.RequestParser()
parser_avaiable_dates.add_argument('start_hour', help = 'This field cannot be blank', required = True)
parser_avaiable_dates.add_argument('end_hour', help = 'This field cannot be blank', required = True)
parser_avaiable_dates.add_argument('interval', help = 'This field cannot be blank', required = True)

class AvaiableDates(Resource):
    def post(self):
        # now = datetime.datetime.now()
        data = parser_avaiable_dates.parse_args()

        start_hour = int(data['start_hour'])
        end_hour = int(data['end_hour'])
        interval = int(data['interval'])

        day = datetime.datetime.now()
        timeSpace = util.generateTimeSpace(day, start_hour, end_hour, interval)

        # now = "2021-01-21T12:00:45.363Z"
        # get appointments after now
        now = datetime.datetime.now(datetime.timezone.utc).replace(hour=start_hour, minute=0, second=0, microsecond=0)
        appointments = db.Appointment.objects(date__gt=now.isoformat()).order_by('date')
        # print([item.date for item in appointments])
        for appointment in appointments:
            timeObj = util.from_ISO_string(appointment.date)
            space = math.ceil(int(appointment.duration)/interval)
            for i in range(space):
                # print(timeObj)
                try: 
                    del timeSpace[timeObj.strftime("%Y-%m-%d")][timeObj.strftime("%H")][timeObj.strftime("%M")]
                except KeyError:
                    pass
                timeObj = timeObj + datetime.timedelta(minutes=(interval))
        return timeSpace, 200
      
      
class SecretResource(Resource):
    @jwt_required
    def get(self):
        return {
            'answer': 42
        }