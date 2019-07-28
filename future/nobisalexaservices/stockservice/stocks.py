"""
Stock client that performs a fuzzy search for a stock symbol, then looks for its price
"""
import json
import requests

YAHOO_STOCK_SUGGEST_URL = 'http://d.yimg.com/aq/autoc?query={}&region=US&lang=en-US'
IEX_STOCK_PRICE_URL = 'https://api.iextrading.com/1.0/stock/{}/quote'


def suggest_stock_symbol(stock):
    """ Perform a fuzzy search for a NASDAQ stock using Yahoo's api

    :param stock: String specifying a company name ("Coca Cola") or its stock symbol ("COKE")
    :return: the company's NASDAQ symbol, if it could be found. None otherwise
    """
    url = YAHOO_STOCK_SUGGEST_URL.format(stock)
    resp = requests.get(url)
    resp.raise_for_status()

    try:
        json_data = json.loads(resp.text)
        # get the first Nasdaq result
        results = json_data['ResultSet']['Result']
        nasdaq_result = [value for value in results if value['exchDisp'] == 'NASDAQ']
        if nasdaq_result:
            return nasdaq_result[0]['symbol']
    except ValueError:
        # We failed to decode the JSON
        return None
    except KeyError:
        return None


def get_stock_price(stock_symbol):
    if stock_symbol is None:
        return None

    url = IEX_STOCK_PRICE_URL.format(stock_symbol)
    resp = requests.get(url)
    resp.raise_for_status()

    try:
        json_data = json.loads(resp.text)
        return "${:.2f}".format(json_data['close'])
    except ValueError:
        # We failed to decode the JSON
        return None
    except KeyError:
        return None


