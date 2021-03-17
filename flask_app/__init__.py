import os
import mongoengine
# flask base
from flask import Flask
# flask api stuff
from flask_restful import Api
from . import resources
# database
# from .mongoDB import db, User, RevokedToken
# from . import mongoDB as db
import flask_app.db as db
from .scheduler import scheduler
# JWT stuff
from flask_jwt_extended import JWTManager
# Cors
from flask_cors import CORS


def create_app():
    # create and configure the app
    app = Flask(__name__,
                # static_url_path='/react-app',
                # instance_relative_config=True,
                # static_folder="react-app",
                # template_folder="react-app"
                )
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY'),
        JWT_TOKEN_LOCATION=('headers', 'cookies'),
        JWT_BLACKLIST_ENABLED=True,
        JWT_BLACKLIST_TOKEN_CHECKS=['access', 'refresh'],
        CORS_SUPPORTS_CREDENTIALS=True,
        CORS_ORIGINS="http://localhost:3000",
        # CORS_ORIGINS="localhost:3000",
        JWT_COOKIE_CSRF_PROTECT=False,
        # JWT_ACCESS_TOKEN_EXPIRES = 15
    )

    # app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    # db = mongoengine
    mongoengine.connect('project1', host=os.environ.get('MONGO_URI'))
    api = Api(app)
    jwt = JWTManager(app)
    CORS(app)
    scheduler.start()

    # cors = CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(header, payload):
        jti = payload['jti']
        return db.RevokedToken.is_jti_blocklisted(jti)

    # Serve React App
    # @app.route('/', defaults={'path': ''})
    # @app.route('/<path:path>')
    # def serve(path):
    #     print("--- hited path: /", path)
    #     if path != "" and os.path.exists(app.static_folder + '/' + path):
    #         return send_from_directory(app.static_folder, path)
    #     else:
    #         return send_from_directory(app.static_folder, 'index.html')

    api.add_resource(resources.UserRegistration, '/registration')
    api.add_resource(resources.UserLogin, '/login')
    api.add_resource(resources.UserLogoutAccess, '/logout/access')
    api.add_resource(resources.UserLogoutRefresh, '/logout/refresh')
    api.add_resource(resources.TokenRefresh, '/token/refresh')
    api.add_resource(resources.UserEmailVerify, '/registration/<string:email_verification_string>')
    api.add_resource(resources.ResetPassword, '/reset-password')
    api.add_resource(resources.UserUpdate, '/user/update')
    # api.add_resource(resources.ResetPassword, '/reset-password/<string:reset_password_string>')

    api.add_resource(resources.AllUsers, '/users')
    api.add_resource(resources.SecretResource, '/secret')

    api.add_resource(resources.AllServices, '/services')
    api.add_resource(resources.UserHistory, '/history')
    api.add_resource(resources.Appointment, '/appointment')
    api.add_resource(resources.AvailableDates, '/available-dates')

    api.add_resource(resources.AllAppointments, '/admin/appointments')

    # @app.after_request
    # def apply_caching(response):
    #     response.headers["Access-Control-Allow-Origin"] = "*"
    #     return response

    return app
