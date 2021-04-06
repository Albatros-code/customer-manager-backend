import json
from flask_restful import Resource
from flask import Response, request

from flask_restful import (
    reqparse,
)

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)

import flask_app.db as db


class Users(Resource):
    @jwt_required()
    def get(self):
        if not get_jwt_identity()['role'] == 'admin':
            return {'message': 'Forbidden'}, 403

        # current_user = db.User.objects(username=identity['username']).get()

        data_json = db.User.objects.to_json()
        return Response(data_json, mimetype="application/json", status=200)
        # return json.loads(data_json)

    def delete(self):
        return {'message': 'Delete all users'}


class User(Resource):
    @jwt_required()
    def get(self, id):
        if not get_jwt_identity()['role'] == 'admin' and not get_jwt_identity()['id'] == id:
            return {'message': 'Forbidden'}, 403
        try:
            user_doc = db.User.objects(id=id).get()
        except:
            return {'err': 'no user found'}, 404
        user_dict = user_doc.to_mongo().to_dict()
        user = {
            'id': str(user_doc.id),
            'data': user_dict.get('data', {}),
            'settings': user_dict.get('settings', {}),
        }

        return {'user': user}, 200

    @jwt_required()
    def put(self, id):
        if not get_jwt_identity()['role'] == 'admin' and not get_jwt_identity()['id'] == id:
            return {'message': 'Forbidden'}, 403

        data = request.get_json()

        try:
            user_doc = db.User.objects(id=id).get()
        except:
            return {'errors': 'Wrong ID'}

        fields_to_update = [
            ('data', db.UserData),
            ('settings', db.UserSettings),
        ]

        for (field, doc) in fields_to_update:
            new_values = data['user'].get(field, None)

            if new_values is not None:
                if user_doc[field] is None:
                    user_doc[field] = doc()

                for key in new_values:
                    setattr(user_doc[field], key, new_values[key])

        try:
            user_doc.save(clean=True)
        except Exception as err:
            return {'errors': err.args[0]}, 400

        return {'message': f'User {id} updated.'}


class UserAppointments(Resource):
    @jwt_required()
    def get(self, id):
        if not get_jwt_identity()['role'] == 'admin' and not get_jwt_identity()['id'] == id:
            return {'message': 'Forbidden'}, 403

        appointments = db.Appointment.objects(user=id).order_by('-date').limit(20)

        data = []
        for appointment in appointments:
            appointment = {
                'id': str(appointment.id),
                'user': appointment.user,
                'service': appointment.service,
                'date': appointment.date,
                'duration': appointment.duration
            }
            data.append(appointment)

        return data, 200

