import datetime
import secrets

from flask import make_response
from flask_restful import Resource, reqparse

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    set_refresh_cookies,
    unset_jwt_cookies,
)

import flask_app.db as db
import flask_app.emails as emails


class UserRegistration(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', help='This field cannot be blank', required=True)
        parser.add_argument('password', help='This field cannot be blank', required=True)
        parser.add_argument('email', help='This field cannot be blank', required=True)
        parser.add_argument('phone', help='This field cannot be blank', required=True)
        parser.add_argument('fname', help='This field cannot be blank', required=True)
        parser.add_argument('lname', help='This field cannot be blank', required=True)
        data = parser.parse_args()

        email_verification_string = ''.join(secrets.token_hex(16))

        user_data = db.UserData(
            email=data['email'],
            phone=data['phone'],
            fname=data['fname'],
            lname=data['lname'],
        )

        user_parameters = db.UserParameters(
            email_verification_string=email_verification_string,
        )

        user_settings = db.UserSettings(
            newsletter=True,
        )

        new_user = db.User(
            username=data['username'],
            # password=db.User.generate_hash(data['password']),
            password=data['password'],
            data=user_data,
            parameters=user_parameters,
        )
        try:
            # new_user.save()
            new_user.save(new_password_check=True)
            emails.send_verification_email(data['email'], email_verification_string)
            return {'message': 'User {} was created.'.format(data['username'])}

        except ValueError as err:
            print(err)
            return {'errors': err.args[0]}, 400
        except:
            return {'error': 'Something went wrong'}, 400


class UserLogin(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', help='This field cannot be blank', required=True)
        parser.add_argument('password', help='This field cannot be blank', required=True)
        parser.add_argument('remember', type=bool)
        data = parser.parse_args()
        # Check if username exist
        try:
            current_user = db.User.objects(username=data['username']).get()
        except:
            return {'errors': {'general': 'Wrong credentials.'}}, 400

        if not db.User.verify_hash(data['password'], current_user.password):
            return {'errors': {'general': 'Wrong credentials.'}}, 400

        if not current_user.parameters.email_verified:
            return {'errors': {'general': 'Email not verified'}}, 400

        identity = {
            'role': current_user.role,
            'id': str(current_user.id),
        }
        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)

        resp = make_response(
            {
                'message': 'Logged in as User {}'.format(str(current_user.id)),
                'access_token': access_token,
            }, 200
        )

        if data['remember']:
            max_age = 31536000
        else:
            max_age = None

        set_refresh_cookies(resp, refresh_token, max_age=max_age)

        return resp

    # def options(self):
    #     return 200, {'Access-Control-Allow-Credentials': 'true'}


class UserLogoutAccess(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()['jti']
        try:
            revoked_token = db.RevokedToken(jti=jti)
            revoked_token.save()
            return {'message': 'Access token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogoutRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        jti = get_jwt()['jti']
        exp = get_jwt()['exp']
        try:
            revoked_token = db.RevokedToken(
                jti=jti,
                expiration_date=datetime.datetime.fromtimestamp(exp, datetime.timezone.utc).isoformat()
            )
            revoked_token.save()

            resp = make_response({'message': 'Refresh token has been revoked'})
            unset_jwt_cookies(resp)
            return resp
        except:
            return {'message': 'Something went wrong'}, 500


class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        identity = get_jwt_identity()
        access_token = create_access_token(identity=identity)
        return {'access_token': access_token}


class UserEmailVerify(Resource):
    def get(self, email_verification_string):
        # user_id = email_verification_string
        try:
            user = db.User.objects(parameters__email_verification_string=email_verification_string).get()
        except:
            return {'error': 'Verification string {} doesn\'t match any user'.format(email_verification_string)}, 400

        if not user.parameters.email_verified:
            # User.objects(email_verification_string=email_verification_string).update_one(set__email_verified=True)
            user.parameters.email_verified = True
            user.save()
            return {'message': 'Email verified'}, 200
        else:
            return {'error': 'Email already verified'}, 400


class PasswordResetSendEmail(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email')
        data = parser.parse_args()

        def common_return_message():
            return 200

        try:
            current_user = db.User.objects(data__email=data.email).get()
        except:
            return common_return_message()

        rest_password_token = secrets.token_hex(16)
        rest_password = db.ResetPassword(
            username=current_user.username,
            token=db.ResetPassword.generate_hash(rest_password_token),
            date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
        try:
            rest_password.save()
        except:
            return common_return_message()

        emails.send_reset_password_email(data['email'], rest_password_token)
        return common_return_message()


class PasswordResetPasswordChange(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token')
        parser.add_argument('password')
        data = parser.parse_args()

        reset_password = None
        try:
            yesterday = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat()
            reset_passwords = db.ResetPassword.objects(date__gt=yesterday)

            for doc in reset_passwords:
                if db.ResetPassword.verify_hash(data.token, doc.token):
                    current_user = db.User.objects(username=doc.username).get()
                    reset_password = doc
                    # doc.delete()
                    break
            if not current_user:
                raise
        except:
            return {'message': 'token not found'}, 400

        try:
            # current_user.password = db.User.generate_hash(data.password)
            current_user.password = data.password
            current_user.save(new_password_check=True)
        except ValueError as err:
            return {'errors': err.args[0]}, 400
        except:
            return {'error': 'Something went wrong'}, 400
        reset_password.delete()
        return {'message': 'password changed'}, 200
