"""Test Utils."""
import functools


def mocked_requests_get_success(url_and_responses):
    """A successful requests.get with a 200 status code."""
    return functools.partial(mocked_requests_get, url_and_responses, 200)


def mocked_requests_get_failed(url_and_responses):
    """ A successful requests_get with a 404 status code"""
    return functools.partial(mocked_requests_get, url_and_responses, 404)


def mocked_requests_get(url_and_responses, status_code, *args, **kwargs):
    """Mocks the result of a requests.get.

    :param url_and_responses: a dictionary from url string to its response, per status code
                            {
                                'http://anything.com': {
                                    200:
                                        '{hello: world}',
                                    404:
                                        'Error'
                                },
                            }
    :param status_code: Whether or not this response succeeds.
    :param args: This is meant to match the requests.get interface. The first argument is the URL we're querying
    :param kwargs:
    """

    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.text = json_data

        def json(self):
            return self.json_data

        def raise_for_status(self):
            pass
    return MockResponse(url_and_responses[args[0]][status_code], status_code)

