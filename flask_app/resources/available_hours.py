import datetime

from flask_restful import Resource
from flask import request

import flask_app.db as db
import flask_app.util as util

from flask_jwt_extended import (
    jwt_required,
)

from .utils.appointments import (
    create_available_hours_obj,
)


class AvailableSlots(Resource):
    @jwt_required()
    def get(self):
        data = available_hours_check_args(request.args)

        query_params = {
            "date__gt": data['start_date'].isoformat(),
            "date__lt": data['end_date'].isoformat()
        }

        appointments = db.Appointment.objects(**query_params).order_by('date')

        available_hours_obj = create_available_hours_obj(
            appointments,
            data['start_date'],
            data['end_date'],
            data['start_hour'],
            data['end_hour'],
            data['interval'],
            data['service']
        )

        date_range = '{}:{}'.format(data['start_date'].strftime('%Y-%m-%d'), (data['end_date']).strftime('%Y-%m-%d'))

        return {'slots': available_hours_obj, 'date_range': date_range}, 200


def available_hours_check_args(args):
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

    def check_start_hour(val):
        try:
            start_hour = int(val)
        except:
            return defaults['start_hour']

        if start_hour < 0 or start_hour > 24:
            return defaults['start_hour']

        return start_hour

    def check_end_hour(val):
        try:
            end_hour = int(val)
        except:
            return defaults['end_hour']

        if end_hour < 0 or end_hour > 24 or end_hour <= checked_arguments['start_hour']:
            return defaults['end_hour']

        return end_hour

    def check_interval(val):
        try:
            interval = int(val)
        except:
            return defaults['interval']

        if interval <= 0 or interval > 60:
            return defaults['interval']

        return interval

    def check_service(val):
        try:
            service = db.Service.objects(name=val).get()
        except:
            return defaults['service']

        return service

    arguments = {
        "start_date": check_start_date,
        "end_date": check_end_date,
        "start_hour": check_start_hour,
        "end_hour": check_end_hour,
        "interval": check_interval,
        "service": check_service
    }

    checked_arguments = {}

    settings = db.Settings.objects().first()
    default_start_date = util.datetime_now_local().replace(hour=0, minute=0, second=0, microsecond=0)
    defaults = {
        "start_date": default_start_date,
        "end_date": checked_arguments.get('start_date', default_start_date) + datetime.timedelta(days=7),
        "start_hour": settings.start_hour,
        "end_hour": settings.end_hour,
        "interval": settings.time_interval,
        "service": None,
    }

    for (item, check_func) in arguments.items():
        val = args.get(item)
        if val is None:
            checked_arguments[item] = defaults[item]
        else:
            action = arguments.get(item)
            checked_arguments[item] = action(val)

    return checked_arguments


