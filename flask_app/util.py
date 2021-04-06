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
            # print(f'{hour}:{minute}')
            current_string = f'{date_string_now}T{hour}:{minute}'
            dateObj = local_timezone.localize(datetime.datetime.strptime(current_string, "%Y-%m-%dT%H:%M"))
            # print(dateObj)
            # print(dateObj<now_local)
            if dateObj < now_local:
                del data[dateObj.strftime("%Y-%m-%d")][dateObj.strftime("%H")][dateObj.strftime("%M")]

    # print(now_utc)
    # print(now_utc.tzinfo)
    # print('---')
    # print(now_local)
    # print(now_local.tzinfo)
    # print('---')
    # print(date_string_now)


    return data

# def from_ISO_string(iso_string):
    # return datetime.datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc)


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


def datetime_new_local(day, hour, minute):
    local_timezone = pytz.timezone("Europe/Warsaw")
    date = datetime.datetime.strptime(f'{day}T{hour}:{minute}:00.000', "%Y-%m-%dT%H:%M:%S.%f")
    date_local = date.astimezone(local_timezone)
    return date_local


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

# local_timezone = pytz.timezone("Europe/Warsaw")
# now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=123)
# now_local = now.replace(tzinfo=pytz.utc).astimezone(local_timezone)
# print(to_ISO_string(now_local))


# day = datetime.datetime.now(datetime.timezone.utc)
# start_hour = 12
# end_hour = 20
# interval = 15
# generateTimeSpace(day, start_hour, end_hour, interval)
# # print(generateTimeSpace(day, start_hour, end_hour, interval))
#
# iso_string = '2021-01-31T18:00:00.000Z'
#
# local_timezone = pytz.timezone("Europe/Warsaw")
# utc_time = datetime.datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%S.%fZ")
# local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_timezone)
#
# # print(local_time)
# delta = datetime.timedelta(minutes=15)
# print(local_time + delta)


# print(datetime.datetime.now())
# now = datetime.datetime.now()
# timezone = pytz.timezone("Europe/Warsaw")
# now_aware = timezone.localize(now)
# print(now.isoformat())
# print(now_aware.isoformat())

# d = datetime.datetime(1990, 11, 13)
# print(d)
# print(d.isoformat())
# print(d.strftime("%Y/%m/%d"))

# d = pytz.utc.localize(datetime.datetime.utcnow())
# d = datetime.datetime.now(datetime.timezone.utc)

# isoString = str(d.isoformat())
# print(isoString)
# d = datetime.datetime.fromisoformat(isoString)
# print(d)
# print(d.isoformat())

# d = datetime.datetime.now()
# iso = d.isoformat()
# print(iso)

# iso = "2021-01-23T15:30:00.957Z"
# # d = datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc)
# print(from_ISO_string(iso))