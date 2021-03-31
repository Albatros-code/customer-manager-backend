from flask_restful import Resource
from flask import Response

import flask_app.db as db


class Services(Resource):
    def get(self):
        data_json = db.Service.objects.to_json()
        return Response(data_json, mimetype="application/json", status=200)