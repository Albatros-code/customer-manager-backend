import json
from flask_restful import Resource, reqparse
from flask import Response
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

import flask_app.db as db


class Services(Resource):
    def get(self):
        data_json = db.Service.objects.to_json()
        return Response(data_json, mimetype="application/json", status=200)


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