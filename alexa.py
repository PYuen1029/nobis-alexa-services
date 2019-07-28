#!/usr/bin/env python3

import ast
import hashlib
import json
import logging
import pprint
import re
import os
import sys
from difflib import SequenceMatcher
from urllib.request import Request, urlopen
from pytz import timezone
import pytz
import requests
import time
import calendar
import urllib
import numbers

# import libraries in lib directory
from classes.dao import DAO

base_path = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(base_path, 'lib'))

from bs4 import BeautifulSoup
from flask import Flask
import records
from flask_ask import Ask, statement, question, session, convert_errors
from google.transit import gtfs_realtime_pb2
from datetime import date, datetime

app = Flask(__name__)
ask = Ask(app, "/")

logging.basicConfig(filename='app.log', level=logging.WARNING)
log = logging.getLogger()


# use it: log.warning('foo')


def call_stock_symbol_api(stock):
    if stock is None:
        return False
    url = 'http://d.yimg.com/aq/autoc?query={}&region=US&lang=en-US'.format(urllib.parse.quote_plus(stock))
    res = urlopen(Request(url))
    res_decode = res.read().decode()
    res_decode = json.loads(res_decode)
    result = res_decode.get('ResultSet').get('Result')
    # filter for NASDAQ only
    filtered_dict = [value for value in result if value.get('exchDisp') == 'NASDAQ']
    if len(filtered_dict) == 0:
        return False
    else:
        return filtered_dict[0].get('symbol')


class AlexaMaster:
    def __init__(self):
        # gets set dynamically in get_which_roommate_status
        pp = pprint.PrettyPrinter(indent=4)
        self.pp = pp

        self.slickdeal_result_word_count = 15
        self.events_result_word_count = 30
        self.slickdeal_result_length = 3
        self.roommates = None
        self.messages = []
        self.db = records.Database('sqlite:///phillip.db')
        self.dao = DAO(self.db)
        self.config = self.dao.get_config()

    def __del__(self):
        self.db.close()

    def subway_intent_action(self):
        self.get_train_status()

        ret_message = self.combine_messages(self.messages)

        return ret_message

    def crypto_intent_action(self, crypto):
        # if self.authenticate():
        self.get_crypto_status(crypto)

        ret_message = self.combine_messages(self.messages)

        ret = {
            'success': True,
            'message': ret_message
        }

        return ret
        # else:
        #     session.attributes['intended_action'] = 'crypto_intent_action'
        #
        #     return self.check_password()

    def move_car_intent_action(self):
        self.get_move_car_status()

        ret_message = self.combine_messages(self.messages)

        return ret_message

    def get_train_status(self):
        feed = gtfs_realtime_pb2.FeedMessage()
        rows = self.dao.query_first("SELECT * FROM train_lines WHERE active = 1")
        train_line_id = rows.get('feed_id')
        train_line_name = self.config.get('trains').get('train_line_name')
        train_stop_name = self.config.get('trains').get('stop_name')

        response = urllib.request.urlopen(
            'http://datamine.mta.info/mta_esi.php?key=GET_YOUR_OWN_MTA_KEY&feed_id={}'.format(
                train_line_id))
        feed.ParseFromString(response.read())
        data = self.get_stop_times(feed)
        train_direction = self.config.get('trains').get('direction')
        time_now = datetime.now()

        if len(data.get(train_direction)) == 0:
            ret_message = 'There is no {} stopping at {} heading {} right now.'.format(train_line_name, train_stop_name,
                                                                                       train_direction)

            self.messages.append(ret_message)

            return ret_message

        next_stop_time = min(data.get(train_direction))

        while next_stop_time - time_now == 0:
            data.get(train_direction).pop(0)
            next_stop_time = min(data.get(train_direction))

        if next_stop_time is None:
            ret_message = 'There is no {} heading {} right now.'.format(train_line_name, train_direction)

            self.messages.append(ret_message)

            return ret_message

        time_diff = next_stop_time - time_now
        minutes_diff = round(time_diff.seconds / 60)

        if minutes_diff > 100 or not isinstance(minutes_diff, numbers.Number):
            ret_message = 'Something went wrong with the API. Please try again later.'
        else:
            if minutes_diff == 1:
                minutes = '1 minute'
            else:
                minutes = minutes_diff, ' minutes'
            ret_message = 'The next {} stopping at {} heading {} is in {}'.format(train_line_name, train_stop_name,
                                                                                  train_direction, minutes)

        self.messages.append(ret_message)

        return ret_message

    def get_stop_times(self, feed):
        ret = {
            'Northbound': [],
            'Southbound': []
        }

        for entity in feed.entity:
            if entity.HasField('trip_update'):
                for stop_time_update in entity.trip_update.stop_time_update:
                    if stop_time_update.HasField('stop_id'):
                        if self.config.get('trains').get('northbound') == stop_time_update.stop_id:
                            ret['Northbound'].append(datetime.fromtimestamp(stop_time_update.arrival.time))
                        if self.config.get('trains').get('southbound') == stop_time_update.stop_id:
                            ret['Southbound'].append(datetime.fromtimestamp(stop_time_update.arrival.time))

        return ret

    def get_move_car_status(self):
        """
Will return whether client's car will need to be moved tomorrow.
        :return:
        """
        query = self.dao.query("SELECT * FROM days WHERE no_parking = 1")

        nyc_asp_twitter_response = self._nyc_asp_twitter_response()
        if nyc_asp_twitter_response:
            ret_statement = 'You do not have to move your car tomorrow, because of {}'.format(nyc_asp_twitter_response)
        else:
            days = []

            for i in query:
                days.append({
                    'id': i.get('id'),
                    'day': i.get('day'),
                    'linked_id': i.get('linked_day'),
                })

            day_num = datetime.today().weekday()
            # -1 because you have to move the car the day before
            if day_num == 6:
                day_check_num = 0
            else:
                day_check_num = day_num + 1

            day = calendar.day_name[day_check_num]

            ret_statement = ''
            # see if today is in days
            for day_obj in days:
                if day == day_obj['day']:
                    linked_day = next(
                        (check_linked_day for check_linked_day in days if
                         check_linked_day['linked_id'] == day_obj['id']),
                        '')

                    ret_statement = 'If your car is parked in a {} {} spot, you have to move your car'.format(
                        day_obj['day'], linked_day['day'])
                else:
                    ret_statement = 'You do not have to move your car tomorrow'
        self.messages.append(ret_statement)

        return ret_statement

    def get_crypto_status(self, crypto):
        # get data from db
        additional_query_string = ''

        if crypto != 'all':
            additional_query_string = ' and name like "%{}%"'.format(crypto)

        crypto_query = self.dao.query("SELECT * FROM cryptocoins WHERE active = 1" + additional_query_string)

        cryptocoins = []
        if len(crypto_query) == 0:
            match = self.match_crypto_symbol(crypto)

            if match:
                cryptocoins.append({
                    'id': match.get('id'),
                    'name': match.get('name'),
                    'short_name': match.get('symbol')
                })
        else:
            for i in crypto_query:
                cryptocoins.append({
                    'id': i.get('id'),
                    'name': i.get('name'),
                    'short_name': i.get('short_name')
                })

        if len(cryptocoins) == 0:
            ret_message = 'There was no crypto currency found with the name of, {}'.format(crypto)

            self.messages.append(ret_message)

            return ret_message

        # create the request url
        url = ','.join([crypto_short_name['short_name'] for crypto_short_name in cryptocoins])

        url = 'https://min-api.cryptocompare.com/data/pricemulti?fsyms={}&tsyms=USD'.format(url)

        # create request
        sess = requests.Session()

        # send request and get data
        html = sess.get(url)
        data = json.loads(html.content.decode('utf-8'))

        # parse data
        parsed_data = ast.literal_eval(str(data))
        # pp = pprint.PrettyPrinter(indent=4)

        coin_data = []

        for coin_type, coin_price in parsed_data.items():
            # iterate over sql data to find name of the coin that has a short_name of coin_type
            ret_info = {'name': item['name'] for item in cryptocoins if item['short_name'] == coin_type}
            # get the price
            ret_info['price'] = coin_price['USD']
            coin_data.append(ret_info)

        ret_message = '. '.join('The price of {} today is {}'.format(item['name'], item['price']) for item in coin_data)

        self.messages.append(ret_message)

        return ret_message

    def match_crypto_symbol(self, crypto):
        url = 'https://api.coinmarketcap.com/v2/listings/'
        ret = self._send_get_curl(url).get('data')

        match = [value for value in ret if self.similar(value.get('name'), crypto) > .8]

        if len(match) > 0:
            return match[0]
        else:
            return None

    def get_slickdeals_status(self, keyword):
        if keyword in ['all', 'frontpage', 'deals']:

            url = "https://slickdeals.net/"
            soup = self.html_parse_call(url)

            deals = soup.find_all(class_='itemTitle')
            deal_texts_total = [' '.join(i.get_text(strip=True).split()[:self.slickdeal_result_word_count])
                                for i in deals]
            deal_texts_section = deal_texts_total[:self.slickdeal_result_length]

            ret_message = "The top {} deals on Slickdeals are: Event {}".format(self.slickdeal_result_length,
                                                                                '. '.join(deal_texts_section))

        else:
            url = "https://slickdeals.net/newsearch.php?src=SearchBarV2&q={}".format(keyword)
            sess = requests.Session()
            html = sess.get(url)
            response = html.content.decode('utf-8')
            soup = BeautifulSoup(response, 'html.parser')
            deals = soup.find_all(class_='dealTitle')
            deal_texts_total = [' '.join(i.get_text(strip=True).split()[:self.slickdeal_result_word_count]) for index, i
                                in
                                enumerate(deals) if
                                index < self.slickdeal_result_length]

            ret_message = "The top {} results for {} on Slickdeals are: {}".format(self.slickdeal_result_length,
                                                                                   keyword, '. '.join(deal_texts_total))

        self.messages.append(ret_message)

        ret = {
            'success': True,
            'message': ret_message
        }

        return ret

    def get_stocks_status(self, stock):
        additional_query_string = ''

        if stock != 'all':
            additional_query_string = ' and name like "%{}%"'.format(stock)

        stocks_query = self.dao.query("SELECT * FROM stocks WHERE active = 1" + additional_query_string)

        stocks_data = []
        messages = []

        # if stocks_query returns empty, this means the stock isn't part of the stocks table. So try to get it from the name if possible
        if len(stocks_query) == 0:
            stock_symbol = call_stock_symbol_api(stock)
            if stock_symbol:
                stock_price = self.call_stock_price_api(stock_symbol)
                stock_message = "The price of {} is {}".format(stock, stock_price)
                messages.append(stock_message)

            else:
                messages.append('Sorry, no stock symbol was found for {}. Please try again.'.format(stock))

        else:
            # for each stock record
            for stock in stocks_query:
                stock_data = {'id': stock.get('id'), 'name': stock.get('name'),
                              'stock_symbol': stock.get('stock_symbol')}
                stocks_data.append(stock_data)

            for stock in stocks_data:
                # call the api
                stock_price = self.call_stock_price_api(stock['stock_symbol'])
                # store the message
                stock_message = "The price of {} is {}".format(stock['name'], stock_price)
                messages.append(stock_message)

        ret_message = '. '.join(messages)

        self.messages.append(ret_message)

        ret = {
            'success': True,
            'message': ret_message
        }

        return ret

    @staticmethod
    def call_stock_price_api(stock_symbol):
        if stock_symbol is None:
            return False

        sess = requests.Session()
        html = sess.get('https://api.iextrading.com/1.0/stock/{}/quote'.format(stock_symbol))
        data = json.loads(html.content.decode('utf-8'))
        return "${:.2f}".format(data['close'])

    def get_which_roommate_status(self):
        # get data from db
        roommates_query = self.dao.query("SELECT * FROM roommates")

        roommates = []

        for i in roommates_query:
            roommates.append({
                'id': i.get('id'),
                'name': i.get('name'),
                'short_name': i.get('short_name'),
                'next_up': i.get('next_up'),
            })

        # append to self so we don't have to do another database call
        session.attributes['roommates'] = roommates

        selected_roommate_data = None

        # return who is next up
        for roommate_datum in roommates:

            if roommate_datum['next_up']:
                selected_roommate_data = roommate_datum

            session.attributes['get_which_roommate_status_called'] = True

        return selected_roommate_data

    def update_roommate_status(self):

        next_roommate_id = None
        first_roommate = None

        for roommate_datum in session.attributes['roommates']:
            if roommate_datum['next_up']:
                first_roommate = roommate_datum

                # increment current_roommate['id'] to get next_roommate_id
                if roommate_datum['id'] == len(session.attributes['roommates']):
                    next_roommate_id = 1
                else:
                    next_roommate_id = roommate_datum['id'] + 1
        new_selected_roommate = None
        for roommate_datum in session.attributes['roommates']:
            if roommate_datum['id'] == next_roommate_id:
                new_selected_roommate = roommate_datum

        if new_selected_roommate is None:
            return 'Something went horribly wrong.'

        # set all roommates' next_up to 0 on db
        self.dao.query('UPDATE roommates SET next_up = 0')
        self.dao.query('UPDATE roommates SET next_up = 1 WHERE id = {}'.format(next_roommate_id))

        write_f = open('/var/www/html/alexa/roommate_log.txt', 'a')

        message = "{} completed a task on {}, so {} became next up to do something.".format(first_roommate['name'],
                                                                                            datetime.now().strftime(
                                                                                                "%B %d, %Y, %I:%M %p"),
                                                                                            new_selected_roommate[
                                                                                                'name'])

        write_f.write(message + '\n')

        # return message
        return 'Alright, {} is next up to do something.'.format(new_selected_roommate['short_name'])

    def get_city_events(self):
        # decide the city based on config
        today_string = datetime.today().strftime('%m-%d-%Y')

        url = 'http://www.welikela.com/losangeles/things-to-do/'.format(today_string)

        soup = self.html_parse_call(url)

        things_to_do_url = soup.select('.item-content h2 a')[0].get('href')

        url = things_to_do_url

        soup = self.html_parse_call(url)

        events = soup.select('div.post-entry p')

        event_texts = []

        counter = 0

        for idx, event in enumerate(events):
            regex = re.compile('<\w+>\d+\.</\w+>')

            if regex.search(str(event.contents[0])) is not None:
                counter += 1

                if counter > 4:
                    event_texts.append(' '.join(event.text.split()[:self.events_result_word_count]))

        if len(event_texts) > 0:
            ret_message = "Today's events on We Like LA are: {}".format('. Event '.join(event_texts))

            ret = {
                'success': True,
                'message': ret_message
            }
        else:
            ret = {
                'success': False,
                'message': 'No events were found on We Like LA.com'
            }

        return ret

    def get_lirr_time(self):
        url = 'http://lirr42.mta.info/'
        from_train_id = str(self.config.get('trains').get('from_lirr_station'))
        to_train_id = str(self.config.get('trains').get('to_lirr_station'))

        if from_train_id is None and to_train_id is None:
            return {
                'success': False,
                'message': 'You do not have LIRR stations set up yet.'
            }

        from_lirr_record = self.dao.query_first("SELECT * FROM lirr_stations WHERE mta_id = {}".format(from_train_id))
        to_lirr_record = self.dao.query_first("SELECT * FROM lirr_stations WHERE mta_id = {}".format(to_train_id))

        # go to url
        browser = RoboBrowser(history=True)
        browser.open(url)

        name_dict = {'name': 'index'}
        lirr_form = browser.get_form(attrs=name_dict)
        # change from station
        lirr_form['FromStation'] = from_train_id
        # change to station
        lirr_form['ToStation'] = to_train_id
        # change date to today
        now = datetime.now(tz=timezone('America/New_York'))
        today = now.strftime('%m/%d/%Y')
        minute = self.get_minute_string(now)
        time_now = now.strftime('%I') + ':' + minute
        self.pp.pprint(time_now)
        am_pm = now.strftime('%p')
        lirr_form['RequestDate'] = today
        # change time
        lirr_form['RequestTime'] = time_now
        lirr_form['RequestAMPM'] = am_pm

        # submit the form
        browser.submit_form(lirr_form, submit=lirr_form['schedules'])

        trs = browser.select('div table tr')
        idx = 0
        depart_times = []
        counter = 0

        for tr in trs:
            cells = tr.find_all('td', class_='schedulesTD')
            if len(cells) > 2:
                depart_times.append(cells[1].text)
                counter += 1
            if counter >= 5:
                break

        from_station_name = from_lirr_record.get('name')
        to_station_name = to_lirr_record.get('name')

        depart_times.pop(0)

        ret = {
            'success': True,
            'message': 'The next four trains will depart from {} at {} to {}'.format(from_station_name,
                                                                                     ', '.join(depart_times),
                                                                                     to_station_name)
        }

        return ret

    def get_phillip_report(self):
        crypto_status = self.get_crypto_status()

        l_train_status = self.get_train_status()

        move_car_status = self.get_move_car_status()

        ret_message = self.combine_messages(self.messages)

        return ret_message

    @staticmethod
    def combine_messages(statuses):
        valid_statuses = [status for status in statuses if status is not None]

        ret_message = '. '.join(valid_statuses)

        return ret_message

    @staticmethod
    def authenticate():
        return session.attributes['authenticated']

    def compare_provided_password(self, password):
        # get password from db
        query = self.dao.query("SELECT password FROM auth WHERE user = 'Phillip'")
        auth_query = query.cursor.fetchall()

        hashed_password = hashlib.sha224(password.lower().encode('utf-8')).hexdigest()

        if auth_query[0][0] == hashed_password:
            session.attributes['authenticated'] = True
            return True
        else:
            return False

    @staticmethod
    def check_password():
        session.attributes['password_check'] = True
        ret = {
            'success': False,
            'message': 'Please say your password.'
        }

        return ret

    def verify_user(self):
        access_key = self.config.get('user').get('access_key')
        return session.user.userId == access_key

    @staticmethod
    def _send_get_curl(url):
        res = requests.get(url)
        return res.json()

    @staticmethod
    def _send_curl(url, data={}, headers={}):
        data = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(url, data, headers)
        res = urllib.request.urlopen(req)
        return json.load(res)

    @staticmethod
    def _nyc_asp_twitter_response():
        url = "https://twitter.com/NYCASP"
        sess = requests.Session()
        html = sess.get(url)
        response = html.content.decode('utf-8')
        soup = BeautifulSoup(response, 'html.parser')
        tweets = [tweet.get_text(strip=True) for tweet in soup.find_all(class_='tweet') if
                  'tomorrow' in tweet.get_text(strip=True)]

        first_tomorrow_tweet = tweets[0]

        if 'will be in effect tomorrow' in first_tomorrow_tweet:
            return False
        else:
            holiday = re.match(r".+? will be suspended tomorrow.+?for ([^\.]+).", first_tomorrow_tweet)
            return holiday.group(1) or False

    @staticmethod
    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()

    @staticmethod
    def html_parse_call(url):
        sess = requests.Session()
        html = sess.get(url)
        response = html.content.decode('utf-8')
        return BeautifulSoup(response, 'html.parser')

    @staticmethod
    def get_minute_string(now):
        ret = (int(now.strftime('%M')) // 15) * 15
        return '00' if ret == 0 else str(ret)


@app.route('/')
def homepage():
    # only for testing
    alexa = AlexaMaster()
    return 'Visit this on your Alexa device'

    ret = alexa.get_lirr_time()

    return ret.get('message')


@ask.launch
def start_skill():
    alexa = AlexaMaster()

    if alexa.verify_user():
        session.attributes['authenticated'] = False

        return question('Nobis Ready').reprompt('Can you repeat the command again?')

    return statement('You do not have access to this application. Please contact technical support.')


@ask.intent("SubwayIntent")
def subway_intent():
    alexa = AlexaMaster()

    ret_message = alexa.subway_intent_action()

    return question(ret_message + '. Do you want to know something else').reprompt('Can you repeat that?')


@ask.intent("MoveCarIntent")
def move_car_intent():
    alexa = AlexaMaster()

    ret_message = alexa.move_car_intent_action()

    return question(ret_message + '. Do you want to know something else').reprompt('Can you repeat that?')


@ask.intent("CryptoIntent", default={'crypto': 'all'})
def crypto_intent(crypto):
    alexa = AlexaMaster()

    ret_message = alexa.crypto_intent_action(crypto)

    if ret_message['success']:
        return question(ret_message['message'] + ". Do you want to know something else").reprompt(
            'Can you repeat that?')
    else:
        return question(ret_message['message']).reprompt('Can you repeat that?')


@ask.intent("RoommateIntent")
def roommate_intent():
    alexa = AlexaMaster()

    selected_roommate = alexa.get_which_roommate_status()

    ret_message = 'It is {}s turn.'.format(selected_roommate['short_name'])

    return question(ret_message + '. Does he have to do something?').reprompt('Can you repeat that?')


@ask.intent("SlickdealsIntent", mapping={'keyword': 'Keyword'}, convert={'keyword': str})
def slickdeals_intent(keyword):
    if 'keyword' in convert_errors:
        return question('Sorry, I didn\'t catch that.').reprompt('Can you repeat that?')

    alexa = AlexaMaster()

    ret_message = alexa.get_slickdeals_status(keyword)

    return question(ret_message['message'] + '. Do you want to know something else').reprompt('Can you repeat that?')


@ask.intent("StocksIntent", default={'stock': 'all'})
def stocks_intent(stock):
    # if 'keyword' in convert_errors:
    #     return question('Sorry, I didn\'t catch that.').reprompt('Can you repeat that?')

    alexa = AlexaMaster()

    ret_message = alexa.get_stocks_status(stock)

    return question(ret_message['message'] + '. Do you want to know something else').reprompt('Can you repeat that?')


@ask.intent("YesIntent")
def yes_intent():
    if session.attributes['get_which_roommate_status_called']:
        alexa = AlexaMaster()

        ret_message = alexa.update_roommate_status()

        return question(ret_message + '. Do you want to know something else?').reprompt('Can you repeat that?')
    else:
        return question('What are you talking about? Do you want to know something else?').reprompt(
            'Can you repeat that?')


@ask.intent("AMAZON.CancelIntent")
def cancel_intent():
    return statement('Let me know if you need anything else.')


@ask.intent("AMAZON.FallbackIntent")
def fallback_intent():
    return statement('Sorry, I didn\'t catch that.')


@ask.intent("FullStatusIntent")
def full_status_intent():
    alexa = AlexaMaster()

    ret_message = alexa.get_phillip_report()

    return statement(ret_message)


@ask.intent("ProvidePasswordIntent", mapping={'password': 'Password'}, convert={'keyword': str})
def provide_password_intent(password):
    if 'keyword' in convert_errors:
        return question('Sorry, I didn\'t catch that.').reprompt('Can you repeat that?')

    alexa = AlexaMaster()

    if session.attributes['password_check']:
        session.attributes['password_check'] = False
        if alexa.compare_provided_password(password):
            func = getattr(alexa, session.attributes['intended_action'])

            ret_message = func()

            if ret_message['success']:
                return question(ret_message['message'] + '. Do you want to know something else').reprompt(
                    'Can you repeat that?')
            else:
                return question(ret_message['message']).reprompt('Can you repeat that?')

        else:
            return question('Sorry, your password was incorrect. Do you wan to know something else?').reprompt(
                'Can you repeat that?')

    else:
        return question('What are you talking about? Do you want to know something else?').reprompt(
            'Can you repeat that?')


@ask.intent("CityEventsIntent")
def city_events_intent():
    alexa = AlexaMaster()

    ret_message = alexa.get_city_events()

    return question(ret_message['message'] + '. Do you want to know something else').reprompt('Can you repeat that?')


@ask.intent("LirrIntent")
def lirr_intent():
    alexa = AlexaMaster()

    ret_message = alexa.get_lirr_time()

    return question(ret_message['message'] + '. Do you want to know something else')


if __name__ == '__main__':
    app.run(debug=True)
