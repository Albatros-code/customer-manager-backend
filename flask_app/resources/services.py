import json
from flask_restful import Resource, reqparse
from flask import request
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

import flask_app.db as db


class Services(Resource):
    def get(self):
        db_data = db.Service.objects()
        db_list = []
        for item in db_data:
            item_dict = item.to_mongo().to_dict()
            item_dict['id'] = str(item.id)
            del item_dict['_id']
            db_list.append(item_dict)

        return {'total': db_data.count(with_limit_and_skip=False), 'data': db_list}


class Service(Resource):
    @jwt_required()
    def get(self, id):
        if not get_jwt_identity()['role'] == 'admin':
            return {'message': 'Forbidden'}, 403
        try:
            db_doc = db.Service.objects(id=id).get()
        except:
            return {'err': 'no service found'}, 404

        doc_dict = db_doc.to_mongo().to_dict()
        doc_dict['id'] = str(db_doc.id)
        del doc_dict['_id']

        return {'doc': doc_dict}, 200

    @jwt_required()
    def put(self, id):
        if not get_jwt_identity()['role'] == 'admin':
            return {'message': 'Forbidden'}, 403

        data = request.get_json()
        new_values = data['service']

        doc = db.Service.objects(id=id).first()

        for key in new_values:
            # print(key + ' ' + str(new_values[key]))
            setattr(doc, key, new_values[key])

        try:
            doc.save(clean=True)
        except Exception as err:
            return {'errors': err.args[0]}, 400

        return {'message': 'Service updated.'}

    @jwt_required()
    def delete(self, id):

        try:
            doc = db.Service.objects(id=id).get()
        except:
            return {'error': 'Appointment does not exist.'}, 404

        if not get_jwt_identity()['role'] == 'admin':
            return {'message': 'Forbidden'}, 403

        doc.delete()

        return {'message': 'Service deleted successfully.'}


class AdminServices(Resource):
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

        services_data = db.Service.objects(**query_params).order_by(order_by).skip(skip).limit(limit)
        services_list = []
        for service in services_data:
            service_dict = service.to_mongo().to_dict()
            service_dict['id'] = str(service.id)
            del service_dict['_id']
            services_list.append(service_dict)

        return {'total': services_data.count(with_limit_and_skip=False), 'data': services_list}

    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name')
        parser.add_argument('duration')
        parser.add_argument('price')
        data = parser.parse_args()

        if data['name']:
            name = data['name']
        else:
            name = ''

        if data['duration']:
            duration = data['duration']
        else:
            duration = ''

        if data['price']:
            price = data['price']
        else:
            price = ''

        new_doc = db.Service(
            name=name,
            duration=duration,
            price=price,
        )

        try:
            # new_doc.save(clean=True)
            new_doc.save()
            return {'message': 'Service: "{}" was created.'.format(data['name'])}
        except Exception as err:
            return {'errors': err.args[0]}, 400

        return {'error': 'Something went wrong'}, 400
