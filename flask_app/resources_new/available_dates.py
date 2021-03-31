import datetime
import math

from flask_restful import Resource, reqparse

import flask_app.db as db
import flask_app.util as util

class AvailableDates(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('start_hour', help='This field cannot be blank', required=True)
        parser.add_argument('end_hour', help='This field cannot be blank', required=True)
        parser.add_argument('interval', help='This field cannot be blank', required=True)
        data = parser.parse_args()

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