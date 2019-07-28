import unittest
from unittest import mock
from nobisalexaservices.stockservice import stocks
from tests.utils import mocked_requests_get_success, mocked_requests_get_failed


class TestStocks(unittest.TestCase):

    SUGGEST_COKE_SUCCESSFUL_RESP = '{"ResultSet":{"Query":"COKE","Result":[{"symbol":"COKE",' \
                      '"name":"Coca-Cola Bottling Co. Consolidated","exch":"NMS",' \
                      '"type":"S","exchDisp":"NASDAQ","typeDisp":"Equity"}]}}'

    SUGGEST_MADEUP_FAILED_RESP = '{"ResultSet":{"Query":"MADEUP","Result":[]}}'

    PRICE_COKE_SUCCESSFUL_RESP = '{"symbol":"COKE","companyName":"Coca-Cola Bottling Co. Consolidated",' \
                                 '"primaryExchange":"Nasdaq Global Select","sector":"Consumer Defensive",' \
                                 '"calculationPrice":"close","open":172.54,"openTime":1534512600050,"close":174.81,' \
                                 '"closeTime":1534536000254,"high":175.94,"low":170.21,"latestPrice":174.81,' \
                                 '"latestSource":"Close","latestTime":"August 17, 2018","latestUpdate":1534536000254,' \
                                 '"latestVolume":76824,"iexRealtimePrice":null,"iexRealtimeSize":null,' \
                                 '"iexLastUpdated":null,"delayedPrice":174.81,"delayedPriceTime":1534536000254,' \
                                 '"extendedPrice":174.81,"extendedChange":0,"extendedChangePercent":0,' \
                                 '"extendedPriceTime":1534538461000,"previousClose":173.5,"change":1.31,' \
                                 '"changePercent":0.00755,"iexMarketPercent":null,"iexVolume":null,' \
                                 '"avgTotalVolume":60251,"iexBidPrice":null,"iexBidSize":null,"iexAskPrice":null,' \
                                 '"iexAskSize":null,"marketCap":1635254027,"peRatio":null,"week52High":230,' \
                                 '"week52Low":125.08,"ytdChange":-0.16130179259569186} '

    @mock.patch('requests.get', side_effect=mocked_requests_get_success({
        stocks.YAHOO_STOCK_SUGGEST_URL.format('COKE'): {
            200: SUGGEST_COKE_SUCCESSFUL_RESP
        },
    }))
    def test_suggest_stock_successful(self, mock_get):
        coke = stocks.suggest_stock_symbol('COKE')
        self.assertEqual(coke.upper(), 'COKE')

    @mock.patch('requests.get', side_effect=mocked_requests_get_success({
        stocks.YAHOO_STOCK_SUGGEST_URL.format('MADEUP'): {
            200: SUGGEST_MADEUP_FAILED_RESP
        },
    }))
    def test_suggest_stock_could_not_be_found(self, mock_get):
        madeup = stocks.suggest_stock_symbol('MADEUP')
        self.assertIsNone(madeup)

    @mock.patch('requests.get', side_effect=mocked_requests_get_failed({
        stocks.YAHOO_STOCK_SUGGEST_URL.format('MADEUP'): {
            404: '{}'
        },
    }))
    def test_suggest_stock_failed(self, mock_get):
        madeup = stocks.suggest_stock_symbol('MADEUP')
        self.assertIsNone(madeup)

    @mock.patch('requests.get', side_effect=mocked_requests_get_success({
        stocks.YAHOO_STOCK_SUGGEST_URL.format('MADEUP'): {
            200: '129102tjgwmv,f3]'
        },
    }))
    def test_suggest_stock_garbage_response(self, mock_get):
        madeup = stocks.suggest_stock_symbol('MADEUP')
        self.assertIsNone(madeup)

    @mock.patch('requests.get', side_effect=mocked_requests_get_success({
        stocks.IEX_STOCK_PRICE_URL.format('COKE'): {
            200: PRICE_COKE_SUCCESSFUL_RESP
        },
    }))
    def test_get_price_successful(self, mock_get):
        coke_price = stocks.get_stock_price('COKE')
        self.assertEquals(coke_price, '$174.81')

    @mock.patch('requests.get', side_effect=mocked_requests_get_success({
        stocks.IEX_STOCK_PRICE_URL.format('COKE'): {
            200: '{}'
        },
    }))
    def test_get_price_failed(self, mock_get):
        coke_price = stocks.get_stock_price('COKE')
        self.assertIsNone(coke_price)






