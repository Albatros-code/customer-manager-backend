import datetime

from flask_restful import Resource, reqparse

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
        if not get_jwt_identity()['role'] == 'admin' and not get_jwt_identity()['role'] == 'user':
            return {'message': 'Forbidden'}, 403

        limited = False
        if get_jwt_identity()['role'] == 'user':
            limited = True

        parser = reqparse.RequestParser()
        parser.add_argument('start_date')
        parser.add_argument('end_date')
        data = parser.parse_args()

        start_date = util.from_ISO_string(data['start_date'])
        if not start_date:
            start_date = util.datetime_now_local().replace(hour=0, minute=0, second=0, microsecond=0)

        end_date = util.from_ISO_string(data['end_date'])
        if end_date and util.to_ISO_string(end_date) < util.to_ISO_string(start_date):
            end_date = None
        if not end_date:
            end_date = start_date + datetime.timedelta(days=7)

        query_params = {
            "date__gt": start_date.isoformat(),
            "date__lt": end_date.isoformat()
        }

        appointments = db.Appointment.objects(**query_params).order_by('date')  # .limit(5)
        data = []
        i = 0
        for appointment in appointments:
            if not limited:
                appointment = {
                    'service': appointment.service,
                    'date': appointment.date,
                    'duration': appointment.duration
                }
            else:
                i += 1
                appointment = {
                    # 'no': i,
                    'date': appointment.date,
                    'duration': appointment.duration
                }
            data.append(appointment)

        return data, 200

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