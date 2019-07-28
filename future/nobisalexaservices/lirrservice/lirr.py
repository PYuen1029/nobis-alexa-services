"""

"""
import datetime

from robobrowser import RoboBrowser

MTA_LIRR_SCHEDULE_URL = 'http://lirr42.mta.info/'


def get_next_itineraries(from_station, to_station, departure_time, num_itineraries=4):
    """

    :param from_station:
    :param to_station:
    :return:
    """
    browser = RoboBrowser(history=True)
    browser.open(MTA_LIRR_SCHEDULE_URL)
    lirr_form = browser.get_form(attrs={'name': 'index'})
    # Form Labels are the select list vales, Form options are the Option Ids
    station_name_to_id = dict(zip(lirr_form.fields['FromStation'].labels,
                                  lirr_form.fields['FromStation'].options))
    from_station_id = station_name_to_id[from_station]
    to_station_id = station_name_to_id[to_station]
    lirr_form['FromStation'] = from_station_id
    lirr_form['ToStation'] = to_station_id
    lirr_form['RequestDate'] = departure_time.strftime("%m/%d/%Y")
    # LIRR Form Departure Time is only available in 15 minute increments
    lirr_form['RequestTime'] = round_to_next_quarter(departure_time).strftime("%I:%M")
    lirr_form['RequestAMPM'] = round_to_next_quarter(departure_time).strftime("%p")

    # submit the form
    # The Lirr Form has two submit buttons, one is {name: 'schedules'},
    # the other is {name: 'fares'}
    browser.submit_form(lirr_form, submit=lirr_form['schedules'])

    # The schedule table is unlabeled
    trs = browser.select('div table tr')
    itineraries = []

    for tr in trs:
        cells = tr.find_all('td', class_='schedulesTD')
        if len(cells) > 2:
            blank, departure, arrival, alert, transfer, transfer_departure, duration, special_message, ticket_type = cells
            itineraries.append(
                Itinerary(from_station, departure.text, arrival.text, alert.text, transfer.text,
                          transfer_departure.text,
                          duration.text, special_message.text, ticket_type.text))
        if len(itineraries) >= num_itineraries:
            break
    return itineraries


class Itinerary:

    def __init__(self, departure_station, departure_time, arrival_time, alert, transfer_station,
                 transfer_departure_time, travel_duration,
                 special_message, ticket_type):
        self.departure_time = departure_time
        self.departure_station = departure_station
        self.arrival_time = arrival_time
        self.alert = alert
        self.transfer_station = transfer_station
        self.transfer_departure_time = transfer_departure_time
        self.travel_duration = travel_duration
        self.special_message = special_message
        self.ticket_type = ticket_type

    def requires_transfer(self):
        return len(self.transfer_station) > 0

    def has_alert(self):
        return len(self.alert) > 0

    def __str__(self):
        msg = f'Departing at {self.departure_time} from {self.departure_station}. '
        msg += f' This trip requires at transfer at {transfer_station} ' \
               f'and departs {transfer_station} at {transfer_departure_time}. ' if self.requires_transfer() else ''
        msg += f' There is an alert on this itinerary' if self.has_alert() else ""


def round_to_next_quarter(dt):
    return round_to_next_interval(dt, interval_timedelta=datetime.timedelta(minutes=15))


def round_to_next_interval(dt, interval_timedelta):
    """ Rounds dt to the next interval_timedelta

    For the purposes of train scheduling, when rounding to the next time interval,
    you don't want ever to round up eg, if it's 11:05, its useless to get times for 11:00
    If our schedule is once every 15 minutes, interval_timedelta rounds dt to the next 15 minutes

    :param dt: a Datetime
    :param interval_timedelta: a TimeDelta up to an hour away

    :return: The ceiling of dt in interval_timedelta chunk
    """
    assert interval_timedelta.total_seconds() <= 60 * 60, "interval_timedelta must be within an hour"
    # how many seconds have passed this hour
    num_seconds = dt.minute * 60 + dt.second + dt.microsecond * 1e-6
    interval_seconds = interval_timedelta.total_seconds()
    # how many seconds until the next quarter
    # Intervalize an hour by intervals
    hourly_intervals = [x for x in range(0, 60 * 60 + 1, int(interval_seconds)) if x >= num_seconds]
    delta = hourly_intervals[0] - num_seconds

    return dt + datetime.timedelta(seconds=delta)
