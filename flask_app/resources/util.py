from flask_restful import Resource

import flask_app.util as util


class CurrentDate(Resource):
    def get(self):
        date_local = util.datetime_now_local()
        date_local_2 = util.datetime_new_local('2021-01-01', '10', '30')
        return {'local_date': date_local.strftime('%Y-%m-%d %H:%M'),
                'local_date_@': date_local_2.strftime('%Y-%m-%d %H:%M')}, 200
