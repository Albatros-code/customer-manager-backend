from flask import request
from flask_restful import Resource
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
)

import flask_app.db as db


class Settings(Resource):
    def get(self):

        settings = db.Settings.objects().first()

        if settings is None:
            settings = db.Settings()

            default_settings = {
                'start_hour': 12,
                'end_hour': 20,
                'time_interval': 15,
                'working_days': {
                    '0': True,
                    '1': True,
                    '2': True,
                    '3': True,
                    '4': True,
                    '5': True,
                    '6': True,
                }
            }

            for (setting, val) in default_settings.items():
                setattr(settings, setting, val)

            settings.save()

        settings = settings.to_mongo().to_dict()
        del settings['_id']
        return settings, 200

    @jwt_required()
    def put(self):
        if not get_jwt_identity()['role'] == 'admin':
            return {'message': 'Forbidden'}, 403

        data = request.get_json()
        new_values = data['settings']

        settings = db.Settings.objects().first()

        for key in new_values:
            setattr(settings, key, new_values[key])

        try:
            settings.save(clean=True)
        except Exception as err:
            return {'errors': err.args[0]}, 400

        return {'message': 'Settings updated.'}


class SettingsDefault(Resource):
    def get(self):

        settings = db.Settings.objects().first()

        if settings is None:
            settings = db.Settings()

        default_settings = {
            'start_hour': 12,
            'end_hour': 20,
            'time_interval': 15,
        }

        for (setting, val) in default_settings.items():
            setattr(settings, setting, val)

        settings.save()

        return {'message': 'Settings set successfully.'}