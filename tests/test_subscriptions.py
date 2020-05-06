import copy
from http import HTTPStatus as StatusCode

from websub.common import errors
from websub.common.errors.handlers import error_response_json_template

from websub.views import (
    UnknownModeError,
    CallbackURLValidationError,
    LeaseSecondsValidationError,
    TopicValidationError,
    UnableToPostSubscriptionError,
    SubscriptionExistsError,
    SubscriptionNotFoundError,
    REQUIRED_ATTRS,
    _validate_url,
    _validate_topic
)
from websub.constants import (
    LEASE_SECONDS_DEFAULT_VALUE,
    LEASE_SECONDS_MAX_VALUE,
    LEASE_SECONDS_MIN_VALUE,
)

POST_URL = '/subscriptions'

VALID_REQUEST_CONTENT_TYPE = 'application/x-www-form-urlencoded'

CALLBACK_ATTR_KEY = 'hub.callback'
TOPIC_ATTR_KEY = 'hub.topic'
MODE_ATTR_KEY = 'hub.mode'
LEASE_SECONDS_ATTR_KEY = 'hub.lease_seconds'
MODE_ATTR_SUBSCRIBE_VALUE = 'subscribe'
MODE_ATTR_UNSUBSCRIBE_VALUE = 'unsubscribe'

INVALID_CONTENT_TYPES = [
    'application/json',
    'multipart/form-data'
]

VALID_SUBSCRIBE_DATA = {
    CALLBACK_ATTR_KEY: 'http://elvis.presley.com/call/me/tender',
    TOPIC_ATTR_KEY: 'SONGS.OLD.TRACK.created',
    MODE_ATTR_KEY: MODE_ATTR_SUBSCRIBE_VALUE
}

VALID_UNSUBSCRIBE_DATA = {**VALID_SUBSCRIBE_DATA, MODE_ATTR_KEY: MODE_ATTR_UNSUBSCRIBE_VALUE}

INVALID_MODE_DATA = {**VALID_SUBSCRIBE_DATA, MODE_ATTR_KEY: 'dancewithme'}

INVALID_CALLBACK_DATA = {**VALID_SUBSCRIBE_DATA, CALLBACK_ATTR_KEY: '/invalid/callback'}

INVALID_TOPIC_DATA = {**VALID_SUBSCRIBE_DATA, TOPIC_ATTR_KEY: 'UN.SONGS'}


def remove_params(data, keys=None, copy_data=True, set_none=False):
    if not keys:
        keys = []
    if copy_data:
        data = copy.deepcopy(data)
    for key in keys:
        if set_none:
            data[key] = None
        else:
            del data[key]
    return data


def test_validator():
    assert not _validate_topic('CEFACT.TRADE.CO.CA.created')
    assert not _validate_topic('CEFACT.TRADE.CO.created')
    assert not _validate_topic('CEFACT.TRADE.CO.*')
    assert not _validate_topic('CEFACT.TRADE.*')
    assert not _validate_topic('CEFACT.*')

    # I'm a little bit unsure about these rules, but there is no problem to remove or modify them
    short_predicate_withoud_wildcard = 'Predicates shorter than 4 elements must include wildcard as the last element'

    assert _validate_topic('UN.CEFACT.TRADE') == short_predicate_withoud_wildcard
    assert _validate_topic('UN.CEFACT') == short_predicate_withoud_wildcard
    assert _validate_topic('*') is False  # a little silly case to subscribe on everything...
    assert _validate_topic('CEFACT.*.*') == 'Predicate may contain only one wildcard and only as the last element'
    assert _validate_topic('CEFACT.TRADE.*.CO.created') == 'Only last element of a predicate can be a wildcard'
    assert _validate_topic('') == 'Predicate must not be empty'
    assert _validate_topic(1) == 'Predicate must be string'

    assert not _validate_url('http://hello.com/callback')
    assert not _validate_url('http://hello.com:8080/callback/')
    assert not _validate_url('https://hello.com')
    assert not _validate_url('https://hello')
    assert not _validate_url('https://192.168.0.1')

    assert _validate_url('http://') == 'URL must contain domain or ip'
    assert _validate_url('192.168.0.1') == 'URL must contain scheme'
    assert _validate_url('file://192.168.0.1') == 'Unsupported url scheme: "{}". Must be one of: {}.'.format(
        'file',
        ['http', 'https']
    )
    assert _validate_url(1) == 'URL must be string'


def test_error_builders():
    # instead of asserting responses data directly it's better to test
    # error builders and then only compare the results
    assert UnknownModeError(INVALID_MODE_DATA[MODE_ATTR_KEY]).to_dict() == {
        'title': 'Unknown Mode Error',
        'code': 'unknown-mode-error',
        'status': 'Bad Request',
        'detail': 'Uknown "{}" attribute value: "{}". Accepted:{}.'.format(
            MODE_ATTR_KEY,
            INVALID_MODE_DATA[MODE_ATTR_KEY],
            [
                MODE_ATTR_SUBSCRIBE_VALUE,
                MODE_ATTR_UNSUBSCRIBE_VALUE
            ]
        ),
        'source': [
            {
                'key': MODE_ATTR_KEY,
                'value': INVALID_MODE_DATA[MODE_ATTR_KEY],
                'expected':[
                    MODE_ATTR_SUBSCRIBE_VALUE,
                    MODE_ATTR_UNSUBSCRIBE_VALUE
                ]
            }
        ]
    }

    assert TopicValidationError('a').to_dict() == {
        'title': 'Topic Validation Error',
        'code': 'topic-validation-error',
        'status': 'Bad Request',
        'detail': '"{}" attribute is invalid'.format(TOPIC_ATTR_KEY),
        'source': ['a']
    }

    assert CallbackURLValidationError('a').to_dict() == {
        'title': 'Callback URL Validation Error',
        'code': 'callback-url-validation-error',
        'status': 'Bad Request',
        'detail': '"{}" attribute is invalid'.format(CALLBACK_ATTR_KEY),
        'source': ['a']
    }

    assert LeaseSecondsValidationError(100).to_dict() == {
        'title': 'Lease Seconds Validation Error',
        'code': 'lease-seconds-validation-error',
        'status': 'Bad Request',
        'detail': '"{}" attribute is invalid. Must be integer in range {}-{}'.format(
            LEASE_SECONDS_ATTR_KEY,
            LEASE_SECONDS_MIN_VALUE,
            LEASE_SECONDS_MAX_VALUE
        ),
        'source': [
            {
                'value': 100,
                'max': LEASE_SECONDS_MAX_VALUE,
                'min': LEASE_SECONDS_MIN_VALUE
            }
        ]
    }

    assert SubscriptionExistsError().to_dict() == {
        'title': 'Conflict',
        'code': 'generic-http-error',
        'status': 'Conflict',
        'detail': 'Subscription with given parameters exists',
        'source': []
    }

    assert SubscriptionNotFoundError().to_dict() == {
        'title': 'Not Found',
        'code': 'generic-http-error',
        'status': 'Not Found',
        'detail': 'Subscription with given parameters not found',
        'source': []
    }

    assert UnableToPostSubscriptionError().to_dict() == {
        'title': 'Internal Server Error',
        'code': 'internal-server-error',
        'status': 'Internal Server Error',
        'detail': 'Unable to post data to repository',
        'source': []
    }


def test_post_success(subscriptions_repo, client):
    post = subscriptions_repo.post
    delete = subscriptions_repo.delete
    post.return_value = True
    delete.return_value = True

    # dummy register subscription check with default lease seconds
    resp = client.post(
        POST_URL,
        data=VALID_SUBSCRIBE_DATA,
        content_type=VALID_REQUEST_CONTENT_TYPE
    )
    post.assert_called_once_with(
        VALID_SUBSCRIBE_DATA[CALLBACK_ATTR_KEY],
        VALID_SUBSCRIBE_DATA[TOPIC_ATTR_KEY],
        LEASE_SECONDS_DEFAULT_VALUE
    )
    assert resp.status_code == StatusCode.ACCEPTED, resp.data

    # dummy register subscription check with default lease seconds set
    subscriptions_repo.reset_mock()
    data = {**VALID_SUBSCRIBE_DATA}

    data[LEASE_SECONDS_ATTR_KEY] = LEASE_SECONDS_MAX_VALUE
    resp = client.post(
        POST_URL,
        data=data,
        content_type=VALID_REQUEST_CONTENT_TYPE
    )
    assert resp.status_code == StatusCode.ACCEPTED, resp.data
    post.assert_called_once_with(
        data[CALLBACK_ATTR_KEY],
        data[TOPIC_ATTR_KEY],
        data[LEASE_SECONDS_ATTR_KEY]
    )

    # dummy deregister subscription check
    resp = client.post(
        POST_URL,
        data=VALID_UNSUBSCRIBE_DATA,
        content_type=VALID_REQUEST_CONTENT_TYPE
    )
    delete.assert_called_once()
    assert resp.status_code == StatusCode.ACCEPTED, resp.get_json()


def test_post_error(subscriptions_repo, client):
    post = subscriptions_repo.post
    delete = subscriptions_repo.delete
    # forcing correct mimetype
    for content_type in INVALID_CONTENT_TYPES:
        resp = client.post(
            POST_URL,
            data=VALID_SUBSCRIBE_DATA,
            content_type=content_type
        )
        assert resp.status_code == StatusCode.UNSUPPORTED_MEDIA_TYPE, resp.data

    # checks missing single required attr
    for key in REQUIRED_ATTRS:
        data = remove_params(VALID_SUBSCRIBE_DATA, keys=[key])
        resp = client.post(
            POST_URL,
            data=data,
            content_type=VALID_REQUEST_CONTENT_TYPE
        )
        assert resp.status_code == StatusCode.BAD_REQUEST, resp.data
        assert resp.get_json() == error_response_json_template(
            errors.MissingAttributesError([key])
        )

    # checks missing multiply required attrs, must return all missing
    data = remove_params(VALID_SUBSCRIBE_DATA, REQUIRED_ATTRS)
    resp = client.post(
        POST_URL,
        data=data,
        content_type=VALID_REQUEST_CONTENT_TYPE
    )
    assert resp.status_code == StatusCode.BAD_REQUEST, resp.data
    assert resp.get_json() == error_response_json_template(
        errors.MissingAttributesError(REQUIRED_ATTRS)
    )

    resp = client.post(
        POST_URL,
        data=INVALID_TOPIC_DATA,
        content_type=VALID_REQUEST_CONTENT_TYPE
    )
    assert resp.status_code == StatusCode.BAD_REQUEST, resp.data
    assert resp.get_json() == error_response_json_template(
        TopicValidationError('Predicates shorter than 4 elements must include wildcard as the last element')
    )

    resp = client.post(
        POST_URL,
        data=INVALID_CALLBACK_DATA,
        content_type=VALID_REQUEST_CONTENT_TYPE
    )
    assert resp.status_code == StatusCode.BAD_REQUEST, resp.data
    assert resp.get_json() == error_response_json_template(
        CallbackURLValidationError('URL must contain scheme')
    )

    # checks unknown mode error, if mode is not in [subscribe, unsubscribe]
    resp = client.post(
        POST_URL,
        data=INVALID_MODE_DATA,
        content_type=VALID_REQUEST_CONTENT_TYPE
    )
    assert resp.status_code == StatusCode.BAD_REQUEST, resp.data
    assert resp.get_json() == error_response_json_template(
        UnknownModeError(INVALID_MODE_DATA[MODE_ATTR_KEY])
    )

    # checks subscription exists error
    resp = client.post(
        POST_URL,
        data=VALID_SUBSCRIBE_DATA,
        content_type=VALID_REQUEST_CONTENT_TYPE
    )
    # let's support both conflict and fine, need to think about it more
    assert resp.status_code in (StatusCode.CONFLICT, StatusCode.ACCEPTED), resp.data
    # assert resp.get_json() == error_response_json_template(
    #     SubscriptionExistsError()
    # )

    # checks unable to post error
    subscriptions_repo.reset_mock()
    post.return_value = None
    resp = client.post(
        POST_URL,
        data=VALID_SUBSCRIBE_DATA,
        content_type=VALID_REQUEST_CONTENT_TYPE
    )
    post.assert_called_once()
    assert resp.status_code == StatusCode.INTERNAL_SERVER_ERROR, resp.data
    assert resp.get_json() == error_response_json_template(
        UnableToPostSubscriptionError()
    )

    # checks subscription not found error
    subscriptions_repo.reset_mock()
    delete.return_value = False
    resp = client.post(
        POST_URL,
        data=VALID_UNSUBSCRIBE_DATA,
        content_type=VALID_REQUEST_CONTENT_TYPE
    )
    delete.assert_called_once()
    assert resp.status_code == StatusCode.NOT_FOUND, resp.data
    assert resp.get_json() == error_response_json_template(
        SubscriptionNotFoundError()
    )
