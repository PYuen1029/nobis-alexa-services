from flask_ask import Ask, question
from flask import Blueprint
"""
The main entry point for Alexa-Ask

"""

blueprint = Blueprint('alexamaster', __name__, url_prefix="/ask")
ask = Ask(blueprint=blueprint)


@ask.launch
def start_skill():
    return question('Nobis Ready').reprompt('Can you repeat the command again?')


@ask.session_ended
def session_ended():
    return "{}", 200

