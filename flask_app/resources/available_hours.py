import datetime
import json
import math

from flask_restful import Resource
from flask import request

import flask_app.db as db
import flask_app.util as util

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)


class AvailableSlots(Resource):
    @jwt_required()
    def get(self):
        data = available_hours_check_args(request.args)

        query_params = {
            "date__gt": data['start_date'].isoformat(),
            "date__lt": data['end_date'].isoformat()
        }

        appointments = db.Appointment.objects(**query_params).order_by('date')

        available_hours_obj = create_available_hours_obj(
            appointments,
            data['start_date'],
            data['end_date'],
            data['start_hour'],
            data['end_hour'],
            data['interval'],
            data['service']
        )

        date_range = '{}:{}'.format(data['start_date'].strftime('%Y-%m-%d'), (data['end_date']).strftime('%Y-%m-%d'))

        return {'slots': available_hours_obj, 'date_range': date_range}, 200


def available_hours_check_args(args):
    def check_start_date(val):
        try:
            date = util.from_ISO_string(val)  # .replace(hour=0, minute=0, second=0, microsecond=0)
        except:
            return defaults['start_date']

        return date

    def check_end_date(val):
        try:
            end_date = util.from_ISO_string(val)
        except:
            end_date = defaults['end_date']

        if end_date <= checked_arguments['start_date']:
            end_date = defaults['end_date']

        return end_date

    def check_start_hour(val):
        try:
            start_hour = int(val)
        except:
            return defaults['start_hour']

        if start_hour < 0 or start_hour > 24:
            return defaults['start_hour']

        return start_hour

    def check_end_hour(val):
        try:
            end_hour = int(val)
        except:
            return defaults['end_hour']

        if end_hour < 0 or end_hour > 24 or end_hour <= checked_arguments['start_hour']:
            return defaults['end_hour']

        return end_hour

    def check_interval(val):
        try:
            interval = int(val)
        except:
            return defaults['interval']

        if interval <= 0 or interval > 60:
            return defaults['interval']

        return interval

    def check_service(val):
        try:
            service = db.Service.objects(name=val).get()
        except:
            return defaults['service']

        return service

    arguments = {
        "start_date": check_start_date,
        "end_date": check_end_date,
        "start_hour": check_start_hour,
        "end_hour": check_end_hour,
        "interval": check_interval,
        "service": check_service
    }

    checked_arguments = {}

    default_start_date = util.datetime_now_local().replace(hour=0, minute=0, second=0, microsecond=0)
    defaults = {
        "start_date": default_start_date,
        "end_date": checked_arguments.get('start_date', default_start_date) + datetime.timedelta(days=7),
        "start_hour": 0,
        "end_hour": 24,
        "interval": 15,
        "service": None,
    }

    for (item, check_func) in arguments.items():
        val = args.get(item)
        if val is None:
            checked_arguments[item] = defaults[item]
        else:
            action = arguments.get(item)
            checked_arguments[item] = action(val)

    return checked_arguments


def create_available_hours_obj(appointments, start_date, end_date, start_hour, end_hour, interval, service):

    available_hours_obj = create_available_hours_obj_base(start_date, end_date, start_hour, end_hour, interval)

    available_hours_obj = remove_reserved_slots(available_hours_obj, appointments, start_hour, end_hour, interval)

    if service:
        available_hours_obj = add_service_duration_restrictions(available_hours_obj, interval, end_hour, service)

    return available_hours_obj


def create_available_hours_obj_base(start_date, end_date, start_hour, end_hour, interval):
    available_hours_obj = {}

    now_date = util.datetime_now_local()
    current_date = start_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)

    while current_date < end_date:
        # filter out slots before today
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
    service_durations = {x.name: x.time for x in db.Service.objects()}

    for appointment in appointments:
        current_date = util.from_ISO_string(appointment.date)
        # filter out appointments out of interesting hours
        if start_hour > int(current_date.strftime('%H')) or int(current_date.strftime('%H')) >= end_hour:
            continue

        # get first previous slot
        first_slot = get_first_prev_slot(available_hours_obj, current_date)
        if first_slot is None:
            continue
        current_slot = current_date.replace(hour=int(first_slot['hour']), minute=int(first_slot['minute']))

        # calculate slots number
        duration = service_durations[appointment.service]
        slot_count = math.ceil(duration/interval)

        # update slots number with inconsistencies in duration/interval differences
        if util.to_ISO_string(current_slot) != util.to_ISO_string(current_date):
            service_end = current_date + datetime.timedelta(minutes=duration)
            last_slot_end = current_slot + datetime.timedelta(minutes=(slot_count*interval))
            if util.to_ISO_string(service_end) > util.to_ISO_string(last_slot_end):
                slot_count += 1

        # remove reserved slots for appointment
        for slot in range(slot_count):
            try:
                set_slot_val(available_hours_obj, current_slot, False)
            except KeyError:
                pass

            current_slot = current_slot + datetime.timedelta(minutes=interval)

    return available_hours_obj


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
    slots_count = math.ceil(int(service.time) / interval) - 1

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
