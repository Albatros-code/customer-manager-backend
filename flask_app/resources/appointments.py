import datetime

from flask_restful import Resource, reqparse
from flask import request

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)

import flask_app.db as db
import flask_app.util as util

from flask_app.util import from_ISO_string


class Appointments(Resource):
    @jwt_required()
    def get(self):
        if not get_jwt_identity()['role'] == 'admin':
            return {'message': 'Forbidden'}, 403

        data = appointments_check_args(request.args)

        query_params = {
            "date__gt": data['start_date'].isoformat(),
            "date__lt": data['end_date'].isoformat()
        }

        appointments = db.Appointment.objects(**query_params).order_by('date')
        settings = db.Settings.objects().first()

        users_data = {str(x.id): x.user for x in appointments}
        users = db.User.objects(id__in=users_data.values())
        users = {str(x.id): {'name': f'{x.data.fname} {x.data.lname}', 'phone': x.data.phone} for x in users}

        response_data = []
        for appointment in appointments:
            current_date = util.from_ISO_string(appointment.date)
            if int(current_date.strftime('%H')) >= settings.start_hour and int(
                    current_date.strftime('%H')) < settings.end_hour:
                appointment_data = {
                    'id': str(appointment.id),
                    'service': appointment.service,
                    'date': appointment.date,
                    'duration': appointment.duration,
                    'user_id': appointment.user,
                    'user': users[appointment.user]['name'],
                    'phone': users[appointment.user]['phone'],
                }
                response_data.append(appointment_data)

        date_range = '{}:{}'.format(data['start_date'].strftime('%Y-%m-%d'), (data['end_date']).strftime('%Y-%m-%d'))

        return {'appointments': response_data, 'date_range': date_range}, 200

        # return response_data, 200

    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('service', help='This field cannot be blank', required=True)
        parser.add_argument('duration', help='This field cannot be blank', required=True)
        parser.add_argument('date', help='This field cannot be blank', required=True)
        data = parser.parse_args()
        current_user = get_jwt_identity()['id']

        new_appointment = db.Appointment(
            user=current_user,
            service=data['service'],
            duration=data['duration'],
            date=data['date'],
        )
        try:
            new_appointment.save()
            return {'message': 'Service: "{}" was scheduled for {}.'.format(data['service'], data['date'])}

        except:
            return {'error': 'Something went wrong'}, 400


class Appointment(Resource):

    @jwt_required()
    def delete(self, id):

        try:
            appointment = db.Appointment.objects(id=id).get()
        except:
            return {'error': 'Appointment does not exist.'}, 404

        if not get_jwt_identity()['role'] == 'admin' and not get_jwt_identity()['id'] == str(appointment['user']):
            return {'message': 'Forbidden'}, 403

        if appointment.date <= util.to_ISO_string(util.datetime_now_local()) and get_jwt_identity()['role'] != 'admin':
            return {'error': 'Appointment cannot be deleted.'}, 400

        appointment.delete()

        return {'message': 'Appointment deleted successfully.'}


def appointments_check_args(args):
    def check_start_date(val):
        try:
            date = util.from_ISO_string(val)  # .replace(hour=0, minute=0, second=0, microsecond=0)
        except:
            return defaults['start_date']

        return date

    def check_end_date(val):
        try:
            end_date = util.from_ISO_string(val)
        except:
            end_date = defaults['end_date']

        if end_date <= checked_arguments['start_date']:
            end_date = defaults['end_date']

        return end_date

    arguments = {
        "start_date": check_start_date,
        "end_date": check_end_date,
    }

    checked_arguments = {}

    default_start_date = util.datetime_now_local().replace(hour=0, minute=0, second=0, microsecond=0)
    defaults = {
        "start_date": default_start_date,
        "end_date": checked_arguments.get('start_date', default_start_date) + datetime.timedelta(days=7),
    }

    for (item, check_func) in arguments.items():
        val = args.get(item)
        if val is None:
            checked_arguments[item] = defaults[item]
        else:
            action = arguments.get(item)
            checked_arguments[item] = action(val)

    return checked_arguments
