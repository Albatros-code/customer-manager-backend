from flask_restful import Resource
from flask import Response

import flask_app.db as db


class Settings(Resource):
    def get(self):
        settings = db.Settings.objects().first().to_mongo().to_dict()
        del settings['_id']
        return settings, 200


class SettingsDefault(Resource):
    def get(self):

        settings = db.Settings.objects().first()

        if settings is None:
            settings = db.Settings()

        default_settings = {
            'startHour': 12,
            'endHour': 20,
            'timeInterval': 15,
        }

        for (setting, val) in default_settings.items():
            setattr(settings, setting, val)

        settings.save()

        return {'message': 'Settings set successfully.'}