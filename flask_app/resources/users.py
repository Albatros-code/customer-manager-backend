import json

from flask_restful import Resource, reqparse
from flask import Response, request

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)

import flask_app.db as db

from .utils.common import (
    db_interface_table_params
)


class Users(Resource):
    @jwt_required()
    def get(self):
        if not get_jwt_identity()['role'] == 'admin':
            return {'message': 'Forbidden'}, 403

        parser = reqparse.RequestParser()
        parser.add_argument('pagination')
        parser.add_argument('page')
        parser.add_argument('order')
        parser.add_argument('filter')
        data = parser.parse_args()

        if data['filter']:
            query_params = json.loads(data['filter'])
        else:
            query_params = {}

        if not data['order']:
            data['order'] = ''

        order_by = data['order'].replace("ascend_", "-").replace("descend_", "+")

        if data['page'] and data['pagination']:
            skip = (int(data['page']) - 1) * int(data['pagination'])
        else:
            skip = None

        if data['pagination']:
            limit = int(data['pagination'])
        else:
            limit = None

        try:
            users_data = db.User.objects(**query_params).order_by(order_by).skip(skip).limit(limit)
            users_data.count(with_limit_and_skip=False)
        except:
            return {'total': 0, 'data': []}

        users_list = []
        for user in users_data:
            user_dict = user.to_mongo().to_dict()
            user_dict['id'] = str(user.id)
            del user_dict['_id']
            del user_dict['password']
            del user_dict['role']
            users_list.append(user_dict)

        return {'total': users_data.count(with_limit_and_skip=False), 'data': users_list}
        # return {'total': 0, 'data': []}


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

        return {'doc': user}, 200

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

    @jwt_required()
    def delete(self, id):

        try:
            doc = db.User.objects(id=id).get()
        except:
            return {'error': 'User does not exist.'}, 404

        if not get_jwt_identity()['role'] == 'admin' and not get_jwt_identity()['id'] == str(doc['id']):
            return {'message': 'Forbidden'}, 403

        # if doc.date <= util.to_ISO_string(util.datetime_now_local()) and get_jwt_identity()['role'] != 'admin':
        #     return {'error': 'Appointment cannot be deleted.'}, 400

        doc.delete()

        return {'message': 'User deleted successfully.'}


class UserAppointments2(Resource):
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


class UserAppointments(Resource):
    @jwt_required()
    def get(self, id):
        if not get_jwt_identity()['role'] == 'admin' and not get_jwt_identity()['id'] == id:
            return {'message': 'Forbidden'}, 403

        (query_params, order_by, skip, limit) = db_interface_table_params(request.args)

        db_data = db.Appointment.objects(user=id, **query_params).order_by(order_by).skip(skip).limit(limit)
        db_list = []
        for item in db_data:
            item_dict = item.to_mongo().to_dict()
            item_dict['id'] = str(item.id)
            del item_dict['_id']
            db_list.append(item_dict)

        return {'total': db_data.count(with_limit_and_skip=False), 'data': db_list}
