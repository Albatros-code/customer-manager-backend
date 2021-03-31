import datetime
import math
import secrets
import json

from flask_restful import Resource, reqparse
from flask import Response, make_response

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

import flask_app.db as db
import flask_app.util as util
import flask_app.emails as emails


# class UserUpdate(Resource):
#     @jwt_required()
#     def post(self):
#         parser = reqparse.RequestParser()
#         parser.add_argument('username', help='This field cannot be blank', required=True)
#         parser.add_argument('user_data', help='This field cannot be blank', required=True)
#         data = parser.parse_args()
#
#         username = data.username
#         current_user = get_jwt_identity()['username']
#         current_role = get_jwt_identity()['role']
#         user_data = json.loads(data.user_data)
#
#         if username == current_user:
#             user = db.User.objects(username=username).get()
#             # print(user.data)
#             user_data_obj = user.data
#
#             for key in user_data:
#                 setattr(user_data_obj, key, user_data[key])
#
#             try:
#                 user.save(clean=True)
#             except Exception as err:
#                 return {'errors': err.args[0]}, 400

# not auth routes

# class AllServices(Resource):
#     def get(self):
#         data_json = db.Service.objects.to_json()
#         # current_user = get_jwt_identity()['username']
#         # print(current_user)
#         return Response(data_json, mimetype="application/json", status=200)


# class UserHistory(Resource):
#     @jwt_required()
#     def get(self):
#         current_user = get_jwt_identity()['username']
#         data_json = db.Appointment.objects(username=current_user).order_by('-date').to_json()
#         return Response(data_json, mimetype="application/json", status=200)
#         # return {'message': 'no elo'}, 200


# parser_appointment = reqparse.RequestParser()
# parser_appointment.add_argument('service', help='This field cannot be blank', required=True)
# parser_appointment.add_argument('duration', help='This field cannot be blank', required=True)
# parser_appointment.add_argument('date', help='This field cannot be blank', required=True)
#
#
# class Appointment(Resource):
#     @jwt_required()
#     def post(self):
#         data = parser_appointment.parse_args()
#         current_user = get_jwt_identity()['id']
#
#         new_appointment = db.Appointment(
#             user=current_user,
#             service=data['service'],
#             duration=data['duration'],
#             date=data['date'],
#         )
#         try:
#             new_appointment.save()
#             return {'message': 'Service: "{}" was scheduled for {}.'.format(data['service'], data['date'])}
#
#         except:
#             return {'error': 'Something went wrong'}, 400

    # @jwt_required()
    # def get(self):
    #     current_user = get_jwt_identity()['username']
    #     now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    #     appointments = db.Appointment.objects(username=current_user, date__gt=now).order_by('date')
    #     data = []
    #     for appointment in appointments:
    #         appointment = {
    #             'service': appointment.service,
    #             'date': appointment.date,
    #             'duration': appointment.duration
    #         }
    #         data.append(appointment)
    #
    #     return data, 200





# admin

# parser_all_appointments = reqparse.RequestParser()
# parser_all_appointments.add_argument('start_date')
# parser_all_appointments.add_argument('end_date')


# class AllAppointments(Resource):
#     @jwt_required()
#     def get(self):
#         data = parser_all_appointments.parse_args()
#         username = get_jwt_identity()['username']
#         role = get_jwt_identity()['role']
#         user = db.User.objects(username=username).get()
#
#         if user.role != role:
#             return {'message': 'Unauthorized'}, 401
#
#         if data['start_date']:
#             start_date = data['start_date']
#         else:
#             start_date = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0,
#                                                                               microsecond=0).isoformat()
#
#         if data['end_date']:
#             end_date = data['end_date']
#         else:
#             end_date = '3000'
#             # end_date = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
#
#         appointments = db.Appointment.objects(date__gt=start_date, date__lt=end_date).order_by('date')  # .limit(5)
#         data = []
#         for appointment in appointments:
#             appointment = {
#                 'service': appointment.service,
#                 'date': appointment.date,
#                 'duration': appointment.duration
#             }
#             data.append(appointment)
#
#         return data, 200


# class AvailableDates(Resource):
#     def post(self):
#         parser = reqparse.RequestParser()
#         parser.add_argument('start_hour', help='This field cannot be blank', required=True)
#         parser.add_argument('end_hour', help='This field cannot be blank', required=True)
#         parser.add_argument('interval', help='This field cannot be blank', required=True)
#         data = parser.parse_args()
#
#         start_hour = int(data['start_hour'])
#         end_hour = int(data['end_hour'])
#         interval = int(data['interval'])
#
#         day = datetime.datetime.now()
#         time_space = util.generateTimeSpace(day, start_hour, end_hour, interval)
#
#         # now = "2021-01-21T12:00:45.363Z"
#         now = datetime.datetime.now(datetime.timezone.utc).replace(hour=start_hour, minute=0, second=0, microsecond=0)
#         appointments = db.Appointment.objects(date__gt=now.isoformat()).order_by('date')
#         # print([item.date for item in appointments])
#         for appointment in appointments:
#             time_obj = util.from_ISO_string(appointment.date)
#             space = math.ceil(int(appointment.duration) / interval)
#             for i in range(space):
#                 # print(timeObj)
#                 try:
#                     del time_space[time_obj.strftime("%Y-%m-%d")][time_obj.strftime("%H")][time_obj.strftime("%M")]
#                 except KeyError:
#                     pass
#                 time_obj = time_obj + datetime.timedelta(minutes=interval)
#
#         return time_space, 200

