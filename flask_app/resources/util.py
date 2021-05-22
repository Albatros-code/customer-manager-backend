import datetime
import random
import math
from flask_restful import Resource
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)

import flask_app.util as util
import flask_app.db as db
from flask_app.resources.appointments import (
    validate_new_appointment
)


class CurrentDate(Resource):
    def get(self):
        date_local = util.datetime_now_local()
        date_local_2 = util.datetime_new_local('2021-01-01', '10', '30')
        return {'local_date': date_local.strftime('%Y-%m-%d %H:%M'),
                'local_date_@': date_local_2.strftime('%Y-%m-%d %H:%M')}, 200


class DatabaseReset(Resource):

    @jwt_required()
    def put(self):
        if not get_jwt_identity()['role'] == 'admin':
            return {'message': 'Forbidden'}, 403

        # delete appointments of all user but not User1 and User2
        user_ids = [str(x.id) for x in db.User.objects(username__in=['User1', 'User2'])]
        db.Appointment.objects(user__nin=user_ids).delete()

        # delete users other than User1 and User2
        db.User.objects(username__nin=['User1', 'User2']).delete()

        # create new users
        users_no = 50
        users = []
        for i in range(users_no):
            new_user = db.User.generate_random_user()
            new_user.password = db.User.generate_hash(new_user.password)
            users.append(new_user)

        # add new users to database
        db.User.objects.insert(users)

        # create appointments for new users (4 weeks, starting from current, monday to sunday)
        services = db.Service.objects()
        settings = db.Settings.objects().first()

        now = util.datetime_now_local()
        start_date = (now - datetime.timedelta(days=now.weekday()))
        start_date = start_date.replace(hour=settings.start_hour, minute=0, second=0, microsecond=0)
        end_date = start_date + datetime.timedelta(days=28)

        query_params = {
            "date__gt": start_date.isoformat(),
            "date__lt": end_date.isoformat()
        }
        scheduled_appointments = db.Appointment.objects(**query_params).order_by('date')

        # generate appointments while current date is before specified end date
        appointments = []
        current_date = start_date
        i = 0
        while util.to_ISO_string(current_date) < util.to_ISO_string(end_date):
            service = random.choice(services)
            user = users[i]

            new_appointment = db.Appointment(
                user=str(user.id),
                service=str(service.id),
                date=util.to_ISO_string(current_date),
                duration=service.time
            )

            # validate if new appointments fits in to available slots
            result = validate_new_appointment(new_appointment, scheduled_appointments, settings, service,
                                              allow_past=True)

            if result:
                appointments.append(new_appointment)

            # calculate date for next appointment
            slot_count = math.ceil(int(new_appointment.duration) / int(settings.time_interval))
            delay = random.choice([1, 2, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]) * 15
            current_date = current_date + datetime.timedelta(minutes=slot_count * settings.time_interval + delay)

            if settings.start_hour > int(current_date.strftime('%H')) or int(
                    current_date.strftime('%H')) >= settings.end_hour:
                current_date = (current_date + datetime.timedelta(days=1)).replace(hour=settings.start_hour, minute=0)

            # get next user number
            i = (i + 1) % users_no

        # add new appointments to database
        if len(appointments) > 0:
            db.Appointment.objects.insert(appointments)

        return {'message': f'{users_no}  new users with {len(appointments)} new appointments created successfully.'}
