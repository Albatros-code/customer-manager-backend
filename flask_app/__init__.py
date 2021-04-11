import os
import mongoengine

from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS

import flask_app.db as db
from flask_app.resources import resources
from .scheduler import scheduler


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY'),
        JWT_TOKEN_LOCATION=('headers', 'cookies'),
        JWT_BLACKLIST_ENABLED=True,
        JWT_BLACKLIST_TOKEN_CHECKS=['access', 'refresh'],
        CORS_SUPPORTS_CREDENTIALS=True,
        CORS_ORIGINS=[os.environ.get('FRONTEND_HOST')],
        JWT_COOKIE_CSRF_PROTECT=False,
        JWT_COOKIE_SECURE=True,
        JWT_COOKIE_SAMESITE='None',
        # JWT_SESSION_COOKIE=False,
    )

    mongoengine.connect('project1', host=os.environ.get('MONGO_URI'))
    api = Api(app)
    jwt = JWTManager(app)
    CORS(app)
    scheduler.start()

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(header, payload):
        jti = payload['jti']
        return db.RevokedToken.is_jti_blocklisted(jti)

    for (resource, url) in resources:
        api.add_resource(resource, url)

    return app
