import mongoengine


class BaseDocument(mongoengine.Document):
    # meta = {'allow_inheritance': True}
    meta = {'abstract': True}

    def clean(self):
        errors = self.validate_doc()
        if errors:
            raise Exception(errors)

    def validate_doc(self):
        return validate_doc(self)


def validate_doc(doc):

    unique_fields = type(doc).get_unique_fields()

    unique_errors = get_unique_errors(doc, unique_fields)

    try:
        field_errors = {}
        doc.validate(clean=False)
    except mongoengine.ValidationError as err:
        field_errors = format_field_errors(doc, mongoengine.ValidationError.to_dict(err))

    # print('\nfield')
    # print(field_errors)
    # print('unique')
    # print(unique_errors)

    errors = merge_dicts([field_errors, unique_errors])

    if errors != {}:
        return errors


def get_unique_errors(document, unique_fields):
    unique_errors = {}
    unique_errors_list = []

    def check_uniqueness(field_name, current_document, errors, query):
        resolved = field_name.split('__', 1)
        if len(resolved) > 1:
            inner_errors = {}
            errors[resolved[0]] = inner_errors
            unique = check_uniqueness(resolved[1], current_document[resolved[0]], inner_errors, query)
            return unique

        try:
            unique_doc = type(document).objects(**{query: current_document[field_name]}).get()
        except mongoengine.DoesNotExist:
            return True

        if unique_doc.id == document.id:
            return True

        errors[field_name] = {current_document[field_name]: 'Not unique'}
        return False

    for field in unique_fields:
        single_error = {}
        # check_uniqueness(field, document, unique_errors, field)
        unique = check_uniqueness(field, document, single_error, field)
        if not unique:
            unique_errors_list.append(single_error)

    return merge_dicts(unique_errors_list)


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


# def merge_errors(error_lists, document):
#     merged_errors = {}
#
#     def traverse_dicts(lists, current_document, field_name, merged_errors):
#         if isinstance(current_document[field_name], mongoengine.EmbeddedDocument):
#             new_error_lists = [x[field_name] for x in error_lists if field_name in x]
#             if len(new_error_lists) == 0:
#                 return
#             merged_errors_inner = {}
#             merged_errors[field_name] = merged_errors_inner
#
#             for field in current_document[field_name]:
#                 traverse_dicts(new_error_lists, current_document[field_name], field, merged_errors_inner)
#             return
#
#         merged_dicts = {}
#         for list in lists:
#             if field_name in list:
#                 merged_dicts.update(list[field_name])
#
#         if merged_dicts != {}:
#             merged_errors[field_name] = merged_dicts
#
#     for field in document:
#         traverse_dicts(error_lists, document, field, merged_errors)
#
#     return merged_errors
