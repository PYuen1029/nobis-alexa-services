""" LIRR Intent

Intents to ask for LIRR times
"""
import datetime

from flask import Blueprint, logging
from flask_ask import Ask, question
from nobisalexaservices.lirrservice import lirr

blueprint = Blueprint('lirr', __name__, url_prefix="/ask")
ask = Ask(blueprint=blueprint)

logging.getLogger('flask_ask').setLevel(logging.DEBUG)


@ask.intent("LirrIntent", default={'from_station': 'Penn Station', 'to_station': 'Flushing', 'num_itineraries': 4})
def lirr_intent(from_station, to_station, num_itineraries):
    """Finds the next departure"""
    itineraries = lirr.get_next_itineraries(from_station, to_station, datetime.datetime.now(), num_itineraries)

    message = f'Here are the next {len(itineraries)} departures' if num_itineraries > 1 else f'Here is the next departure'
    message += f' from {from_station} to {to_station} '
    message += ", ".join(itinerary.departure_time for itinerary in itineraries)
    message += ", ".join(str(itinerary) for itinerary in itineraries)

    return question(message + '. Do you want to know something else').reprompt('Can you repeat that?')
