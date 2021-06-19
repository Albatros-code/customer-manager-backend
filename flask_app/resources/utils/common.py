import json
from flask_app.util import (
    datetime_new_local,
    to_ISO_string
)


def db_interface_table_params(args):
    filter_obj = args.get('filter')
    order = args.get('order')
    page = args.get('page')
    pagination = args.get('pagination')

    if filter_obj:
        query_params = json.loads(filter_obj)
        if 'date__gt' in query_params:
            date_obj_lt = datetime_new_local(query_params['date__gt'], '00', '00', '00', '000')
            query_params['date__gt'] = to_ISO_string(date_obj_lt)
        if 'date__lt' in query_params:
            date_obj_lt = datetime_new_local(query_params['date__lt'], '23', '59', '59', '999')
            query_params['date__lt'] = to_ISO_string(date_obj_lt)
    else:
        query_params = {}
    if not order:
        order = ''

    order_by = order.replace("ascend_", "-").replace("descend_", "+")

    if page and pagination:
        skip = (int(page) - 1) * int(pagination)
    else:
        skip = None

    if pagination:
        limit = int(pagination)
    else:
        limit = None

    return query_params, order_by, skip, limit
