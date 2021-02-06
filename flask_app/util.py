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
    local_timezone = pytz.timezone("Europe/Warsaw")
    utc_time = datetime.datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_timezone)
    return local_time





day = datetime.datetime.now(datetime.timezone.utc)
start_hour = 12
end_hour = 20
interval = 15
generateTimeSpace(day, start_hour, end_hour, interval)
# print(generateTimeSpace(day, start_hour, end_hour, interval))

iso_string = '2021-01-31T18:00:00.000Z'

local_timezone = pytz.timezone("Europe/Warsaw")
utc_time = datetime.datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%S.%fZ")
local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_timezone)

# print(local_time)
delta = datetime.timedelta(minutes=15)
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