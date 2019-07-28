""" Stock Intent.

Intents to ask for the current price
"""

import logging

from flask import Blueprint
from flask_ask import Ask, question

from nobisalexaservices.stockservice import stocks

blueprint = Blueprint('stocks', __name__, url_prefix="/ask")
ask = Ask(blueprint=blueprint)

logging.getLogger('flask_ask').setLevel(logging.DEBUG)


@ask.intent("StocksIntent", default={'stock': 'all'})
def stocks_intent(stock):
    """Gets the price of a stock."""
    stock_name = stocks.suggest_stock_symbol(stock)
    price = stocks.get_stock_price(stock_name)
    message = f'The price of {stock_name} is {price}'
    return question(message + '. Do you want to know something else').reprompt('Can you repeat that?')


