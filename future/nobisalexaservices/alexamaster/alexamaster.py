from flask_ask import Ask, question, statement
from flask import Blueprint, render_template


@ask.launch
def start_skill():
    alexa = AlexaMaster()

    if alexa.verify_user():
        session.attributes['authenticated'] = False

        return question('Nobis Ready').reprompt('Can you repeat the command again?')

    return statement('You do not have access to this application. Please contact technical support.')
