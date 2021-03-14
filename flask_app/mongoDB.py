import mongoengine as db
import os
import re
import datetime
import secrets
from passlib.hash import pbkdf2_sha256 as sha256


# db = mongoengine
# db.connect('project1', host=os.environ.get('MONGO_URI'))

class BaseDocument(db.Document):
    # meta = {'allow_inheritance': True}
    meta = {'abstract': True,}

    def validate_doc(self):
        return validate_doc(self)


def validate_phone(phone):
    # uniqueness
    # if User.objects(data__phone=phone).count() > 0:
    #     raise mongoengine.ValidationError("Phone already taken, select another")

    # print()

    # phone structure
    if not re.search("^\\d{9}$", phone):
        raise db.ValidationError("9 digit number required")


def validate_age(val):
    if val == '11':
        raise db.ValidationError("Age can't be 11.")


def validate_password(val: str):
    if len(val) < 8:
        raise db.ValidationError("8 digit required.")


class UserData(db.EmbeddedDocument):
    # phone = db.StringField(validation=validate_phone)
    phone = db.StringField(unique=True, validation=validate_phone)
    fname = db.StringField()
    lname = db.StringField()
    email = db.EmailField(unique=True)
    age = db.IntField(unique=True, validation=validate_age)

    @classmethod
    def get_class(cls):
        return cls

    @classmethod
    def get_unique_fields(cls, doc):
        unique_fields = ['phone', 'age']
        return_dict = {}
        for field in unique_fields:
            print(f'In loop {field}')
            try:
                print(cls.objects(phone=doc[field]).get())
            except:
                pass
            return_dict[field] = doc[field]
        return return_dict
        # return {'phone': user_data.phone, 'age': user_data.age}
        #
        # def clean(self):
        #     print('clean run')
        #     if hasattr(self, 'id'):
        #         print(self.id)
        #
        #     try:
        #         self.validate(clean=False)
        #     except db.ValidationError as err:
        #         print(db.ValidationError.to_dict(err))

        # unique_vals = [self.phone, self.age]
        #
        # for unique in unique_vals:
        #     if unique == "123456789":
        #         print('clean method; phone is {}'.format(self.phone))
        #         raise mongoengine.ValidationError({"phone": "clean error"})


class UserSettings(db.EmbeddedDocument):
    newsletter = db.BooleanField(default=False)


class UserParameters(db.EmbeddedDocument):
    email_verified = db.BooleanField(default=False)
    email_verification_string = db.StringField(default=''.join(secrets.token_hex(16)))


USER_ROLE = ('user', 'admin')


# class User(db.Document):
class User(BaseDocument):
    role = db.StringField(choices=USER_ROLE, default='user')
    username = db.StringField(unique=True)
    password = db.StringField(min_length=8, validation=validate_password)
    data = db.EmbeddedDocumentField(UserData)
    settings = db.EmbeddedDocumentField(UserSettings)
    parameters = db.EmbeddedDocumentField(UserParameters)

    # def clean(self):
    #     if hasattr(self, 'id'):
    #         pass
    #
    #     unique_fields = ['username']
    #     errors = {}
    #
    #     for field in unique_fields:
    #         try:
    #             # existing_doc = self.objects(**{field: field}).get()
    #             print(self[field])
    #             existing_doc = User.objects(username=self[field]).get()
    #         except db.DoesNotExist:
    #             print(f'Field {field} is unique')
    #             continue
    #
    #         errors[field] = {self[field]: "Not unique"}
    #
    #     if errors != {}:
    #         raise db.ValidationError(errors)
    #
    #     try:
    #         self.validate(clean=False)
    #     except db.ValidationError as err:
    #         pass
            # print(db.ValidationError.to_dict(err))

    @staticmethod
    def get_unique_fields():
        return ['username', 'data__phone', 'data__email']

    @classmethod
    def get_class(cls):
        return cls

    # Generate hash from password by encryption using sha256
    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    # Verify hash and password
    @staticmethod
    def verify_hash(password, hash_):
        return sha256.verify(password, hash_)


def validate_doc(doc):
    if hasattr(doc, 'id'):
        pass

    unique_fields = type(doc).get_unique_fields()
    errors = {}
    field_errors = {}

    unique_errors = get_unique_errors(doc, unique_fields)

    try:
        doc.validate(clean=False)
    except db.ValidationError as err:
        field_errors = format_field_errors(doc, db.ValidationError.to_dict(err))

    print('\nfield')
    print(field_errors)
    print('unique')
    print(unique_errors)

    # errors = merge_errors([field_errors, unique_errors], self)
    errors = merge_dicts([field_errors, unique_errors])

    if errors != {}:
        return errors

def get_unique_errors(document, unique_fields):
    unique_errors = {}

    def check_uniqueness(field_name, current_document, errors, query):
        resolved = field_name.split('__', 1)
        if len(resolved) > 1:
            inner_errors = {}
            errors[resolved[0]] = inner_errors
            check_uniqueness(resolved[1], current_document[resolved[0]], inner_errors, query)
            return

        try:
            document_class = type(document)
            unique_doc = document_class.objects(**{query: current_document[field_name]}).get()
        except db.DoesNotExist:
            return

        if unique_doc.id == document.id:
            return

        errors[field_name] = {current_document[field_name]: 'Not unique'}

    for field in unique_fields:
        check_uniqueness(field, document, unique_errors, field)

    return unique_errors


def format_field_errors(document, field_errors):
    formatted_dict = {}

    def format_field(current_doc, field_errors, formatted_dict):
        for field in field_errors:
            if isinstance(field_errors[field], dict):
                inner_dict = {}
                formatted_dict[field] = inner_dict
                format_field(current_doc[field], field_errors[field], inner_dict)
                continue

            formatted_dict[field] = {current_doc[field]: field_errors[field]}

    format_field(document, field_errors, formatted_dict)
    return formatted_dict


def merge_dicts(dicts):
    print('\n')
    new_dict = {}

    def add_to_new_dict(dict_to_add, new_dict):
        for (key, val) in dict_to_add.items():
            if isinstance(val, dict):
                if key in new_dict:
                    next_dict = new_dict[key]
                else:
                    next_dict = {}
                    new_dict[key] = next_dict

                add_to_new_dict(val, next_dict)
            else:
                new_dict[key] = val

    for item in dicts:
        add_to_new_dict(item, new_dict)

    return new_dict


def merge_errors(error_lists, document):
    merged_errors = {}

    def traverse_dicts(lists, current_document, field_name, merged_errors):
        if isinstance(current_document[field_name], db.EmbeddedDocument):
            new_error_lists = [x[field_name] for x in error_lists if field_name in x]
            if len(new_error_lists) == 0:
                return
            merged_errors_inner = {}
            merged_errors[field_name] = merged_errors_inner

            for field in current_document[field_name]:
                traverse_dicts(new_error_lists, current_document[field_name], field, merged_errors_inner)
            return

        merged_dicts = {}
        for list in lists:
            if field_name in list:
                merged_dicts.update(list[field_name])

        if merged_dicts != {}:
            merged_errors[field_name] = merged_dicts

    for field in document:
        traverse_dicts(error_lists, document, field, merged_errors)

    return merged_errors


class ResetPassword(db.Document):
    username = db.StringField()
    token = db.StringField()
    date = db.StringField()

    # Generate hash from password by encryption using sha256
    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    # Verify hash and password
    @staticmethod
    def verify_hash(password, hash_):
        return sha256.verify(password, hash_)


class Appointment(db.Document):
    username = db.StringField()
    service = db.StringField()
    date = db.StringField()
    duration = db.StringField()


class Service(db.Document):
    name = db.StringField()
    time = db.IntField()
    prize = db.IntField()


class RevokedToken(db.Document):
    jti = db.StringField()
    expiration_date = db.StringField()

    @classmethod
    def is_jti_blocklisted(cls, jti):
        query = cls.objects(jti=jti)
        return bool(query)
