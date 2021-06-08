import datetime
import json
import math

import flask_app.db as db
import flask_app.util as util


# function used to generate JSON object of True/False values for each time slot
def create_available_hours_obj(appointments, start_date, end_date, start_hour, end_hour, interval, service,
                               allow_past=False):
    available_hours_obj = create_available_hours_obj_base(start_date, end_date, start_hour, end_hour, interval,
                                                          allow_past)

    available_hours_obj = remove_reserved_slots(available_hours_obj, appointments, start_hour, end_hour, interval)

    if service:
        available_hours_obj = add_service_duration_restrictions(available_hours_obj, interval, end_hour, service)

    return available_hours_obj


def create_available_hours_obj_base(start_date, end_date, start_hour, end_hour, interval, allow_past=False):
    available_hours_obj = {}

    now_date = util.datetime_now_local()
    current_date = start_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)

    while current_date < end_date:
        # filter out slots before today
        if allow_past:
            available = True
        else:
            available = True if current_date > now_date else False

        current_slot = {
            current_date.strftime('%Y-%m-%d'): {
                current_date.strftime('%H'): {
                    current_date.strftime('%M'): available
                }
            }
        }

        available_hours_obj = util.merge_dicts([available_hours_obj, current_slot])

        current_date = current_date + datetime.timedelta(minutes=interval)
        if int(current_date.strftime('%H')) >= end_hour:
            current_date = current_date.replace(hour=start_hour, minute=0, second=0,
                                                microsecond=0) + datetime.timedelta(days=1)

    return available_hours_obj


def remove_reserved_slots(available_hours_obj_inp, appointments, start_hour, end_hour, interval):
    available_hours_obj = json.loads(json.dumps(available_hours_obj_inp))

    for appointment in appointments:
        current_date = util.from_ISO_string(appointment.date)
        # filter out appointments out of interesting hours
        if start_hour > int(current_date.strftime('%H')) or int(current_date.strftime('%H')) >= end_hour:
            continue

        def action_for_slot(current_slot):
            try:
                set_slot_val(available_hours_obj, current_slot, False)
            except KeyError:
                pass

        iterate_over_appointment_slots(action_for_slot, available_hours_obj, appointment, interval)

    return available_hours_obj


# allow to pass a callback that is executed for each time slot used by appointment
def iterate_over_appointment_slots(callback, available_hours_obj, appointment, interval):
    current_date = util.from_ISO_string(appointment.date)
    # get first previous slot
    first_slot = get_first_prev_slot(available_hours_obj, current_date)
    if first_slot is None:
        return False
    current_slot = current_date.replace(hour=int(first_slot['hour']), minute=int(first_slot['minute']))

    # calculate slots number
    duration = appointment.duration
    slot_count = math.ceil(int(duration) / int(interval))

    # update slots number with inconsistencies in duration/interval differences
    if util.to_ISO_string(current_slot) != util.to_ISO_string(current_date):
        service_end = current_date + datetime.timedelta(minutes=duration)
        last_slot_end = current_slot + datetime.timedelta(minutes=(slot_count * interval))
        if util.to_ISO_string(service_end) > util.to_ISO_string(last_slot_end):
            slot_count += 1

    # do actions for slots of appointment
    for slot in range(slot_count):
        callback(current_slot)

        current_slot = current_slot + datetime.timedelta(minutes=interval)


def get_first_prev_slot(available_hours_obj, date_obj):
    date = {
        "day": date_obj.strftime('%Y-%m-%d'),
        "hour": date_obj.strftime('%H'),
        "minute": date_obj.strftime('%M'),
    }

    day = date['day']
    hour = date['hour']
    minute = date['minute']

    if day in available_hours_obj.keys():
        if hour in available_hours_obj[day].keys():
            if minute in available_hours_obj[day][hour].keys():
                # remove founded slot
                # available_hours_obj[day][hour][minute] = False
                return date
            else:
                # get previous minute slot
                available_minutes = available_hours_obj[day][hour].keys()
                previous_minute_slot = [x for x in available_minutes if int(x) < int(minute)]
                if len(previous_minute_slot) > 0:
                    minute = max(previous_minute_slot)
                    # print(hour + ':' + minute + '  --- new slot')
                    # available_hours_obj[day][hour][minute] = False
                    date['minute'] = minute
                    return date
                else:
                    # get previous minute slot in previous hour slot
                    available_hours = available_hours_obj[day].keys()
                    previous_hour_slot = [x for x in available_hours if int(x) < int(hour)]
                    if len(previous_hour_slot) > 0:
                        hour = max(previous_hour_slot)
                        minute = max(available_hours_obj[day][hour].keys())
                        date['hour'] = hour
                        date['minute'] = minute
                        return date
    return None


def add_service_duration_restrictions(available_hours_obj_inp, interval, end_hour, service):
    available_hours_obj = json.loads(json.dumps(available_hours_obj_inp))
    slots_count = math.ceil(int(service.duration) / interval) - 1

    # add end hours to collections
    for key in available_hours_obj:
        end_hour_dict = {key: {str(end_hour): {'00': False}}}
        available_hours_obj = util.merge_dicts([available_hours_obj, end_hour_dict])

    # add reserved slots before other appointments and on the end
    for (day, hours) in available_hours_obj.items():
        for (hour, minutes) in hours.items():
            for (minute, val) in minutes.items():
                if not val:
                    day_obj = util.datetime_new_local(day, hour, minute)
                    prev_slot_obj = day_obj - datetime.timedelta(minutes=interval)

                    try:
                        prev_slot_val = get_slot_val(available_hours_obj, prev_slot_obj)
                    except KeyError:
                        # print(f'error on {prev_day} {prev_hour}:{prev_minute}')
                        continue

                    # check if previous slot is free
                    if prev_slot_val:
                        for slot in range(slots_count):
                            try:
                                # set prev slot not available
                                set_slot_val(available_hours_obj, prev_slot_obj, False)
                            except KeyError:
                                break
                            prev_slot_obj = prev_slot_obj - datetime.timedelta(minutes=interval)

    return available_hours_obj


def set_slot_val(available_hours_obj, slot_obj, val):
    day = slot_obj.strftime('%Y-%m-%d')
    hour = slot_obj.strftime('%H')
    minute = slot_obj.strftime('%M')
    available_hours_obj[day][hour][minute] = val


def get_slot_val(available_hours_obj, slot_obj):
    day = slot_obj.strftime('%Y-%m-%d')
    hour = slot_obj.strftime('%H')
    minute = slot_obj.strftime('%M')
    return available_hours_obj[day][hour][minute]


# function for checking if slots for appointment are available
def validate_new_appointment(new_appointment, appointments=None, settings=None, service=None,
                             allow_past=False):
    if not settings:
        settings = db.Settings.objects().first()

    if not service:
        service = db.Service.objects(name=new_appointment.service).first()

    current_date = util.from_ISO_string(new_appointment.date)

    # filter out appointments out of interesting hours
    if settings.start_hour > int(current_date.strftime('%H')) or int(current_date.strftime('%H')) >= settings.end_hour:
        return False

    start_date = current_date.replace(hour=settings.start_hour, minute=0, second=0, microsecond=0)
    end_date = current_date.replace(hour=settings.end_hour, minute=0, second=0, microsecond=0)

    if not appointments:
        query_params = {
            "date__gt": start_date.isoformat(),
            "date__lt": end_date.isoformat(),
            # "id__ne": new_appointment.id
        }

        if new_appointment.id:
            query_params["id__ne"] = new_appointment.id

        appointments = db.Appointment.objects(**query_params).order_by('date')

    # generate available slots for a day of interesting appointment
    available_slots = create_available_hours_obj(
        appointments,
        start_date,
        end_date,
        settings.start_hour,
        settings.end_hour,
        settings.time_interval,
        service,
        allow_past=allow_past
    )

    slots = get_slots_for_appointment(new_appointment, available_slots, settings)

    appointment_validation_result = check_slots_availability(slots, available_slots)

    return appointment_validation_result


def get_slots_for_appointment(new_appointment, available_hours_obj, settings):
    if not settings:
        settings = db.Settings.objects().first()

    slots = []

    def action_for_slot(current_slot):
        slots.append(current_slot)

    iterate_over_appointment_slots(action_for_slot, available_hours_obj, new_appointment, settings.time_interval)

    return slots


def check_slots_availability(slots, available_slots):

    for slot in slots:
        if not get_slot_val(available_slots, slot):
            return False
    return True
