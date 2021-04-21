import json


def db_interface_table_params(args):
    filter_obj = args.get('filter')
    order = args.get('order')
    page = args.get('page')
    pagination = args.get('pagination')

    if filter_obj:
        query_params = json.loads(filter_obj)
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
