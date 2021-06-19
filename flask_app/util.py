import datetime
import pytz
import json


def generateTimeSpace(day, start_hour, end_hour, interval):

    def minutes():
        minutes = {}
        current_minutes = 0
        while current_minutes < 60:
            minutes['%02d' % current_minutes] = True
            current_minutes += interval
        return minutes

    def hours():
        hours = {}
        current_hour = start_hour
        while current_hour <= end_hour:
            hours['%02d' % current_hour] = minutes()
            current_hour += 1
        return hours

    data = {}

    for i in range(14):
        current_day = day + datetime.timedelta(days=i)
        # if current_day.strftime("%w") != '0' and current_day.strftime("%w") != '6':
        day_string = (current_day).strftime("%Y-%m-%d")
        data[day_string] = hours()

    # delete all aviable hours before now
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    local_timezone = pytz.timezone("Europe/Warsaw")
    now_local = now_utc.replace(tzinfo=pytz.utc).astimezone(local_timezone)
    
    date_string_now = now_local.strftime('%Y-%m-%d')

    current_day_dict = json.loads(json.dumps(data[date_string_now]))
    
    for hour in current_day_dict:
        hours = current_day_dict[hour]
        for minute in hours:
            current_string = f'{date_string_now}T{hour}:{minute}'
            dateObj = local_timezone.localize(datetime.datetime.strptime(current_string, "%Y-%m-%dT%H:%M"))
            if dateObj < now_local:
                del data[dateObj.strftime("%Y-%m-%d")][dateObj.strftime("%H")][dateObj.strftime("%M")]

    return data


def from_ISO_string(iso_string):
    if iso_string is None:
        return
    local_timezone = pytz.timezone("Europe/Warsaw")
    utc_time = datetime.datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_timezone)
    return local_time


def to_ISO_string(date_obj):
    date_utc = date_obj.astimezone(pytz.utc)
    return date_utc.strftime('%Y-%m-%dT%H:%M:%S.') + date_utc.strftime('%fZ')[3:]


def datetime_now_local():
    local_timezone = pytz.timezone("Europe/Warsaw")
    now = datetime.datetime.now(datetime.timezone.utc)
    now_local = now.astimezone(local_timezone)
    return now_local


def datetime_new_local(day, hour, minute, second='00', microseconds='000'):
    now = datetime.datetime.now(datetime.timezone.utc)
    local_timezone = pytz.timezone("Europe/Warsaw")
    date_local = now.astimezone(local_timezone)

    date = date_local.strptime(f'{day}T{hour}:{minute}:{second}.{microseconds}', "%Y-%m-%dT%H:%M:%S.%f")
    return date


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