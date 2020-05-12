from datetime import datetime
from io import BytesIO
from unittest import TestCase, mock

import pytest
from freezegun import freeze_time

from websub.repos import Pattern, Subscription, SubscriptionsRepo, Id


class MinioPatternTest(TestCase):
    def test_to_key__when_empty__should_return_error(self):
        with pytest.raises(ValueError):
            Pattern(predicate='').to_key()

    def test_to_key__when_contains_slashes__should_return_error(self):
        with pytest.raises(ValueError):
            Pattern(predicate='aa/bb').to_key()

    def test_to_key__when_wildcard_without_dot__should_return_error(self):
        with pytest.raises(ValueError):
            Pattern(predicate='aa.bb*').to_key()

    def test_to_key__when_predicate_valid__should_return_key(self):
        assert Pattern('aaaa.bbbb.cccc').to_key() == "AAAA/BBBB/CCCC/"

    def test_to_key__with_wildcard_in_predicate__should_be_handled(self):
        assert Pattern('aaaa.bbbb.cccc.*').to_key() == "AAAA/BBBB/CCCC/"
        assert Pattern('aaaa.bbbb.cccc.').to_key() == "AAAA/BBBB/CCCC/"

    def test_to_layers__should_return_list_of_layers(self):
        assert Pattern('aaaa.bbbb.cccc.*').to_layers() == [
            'AAAA/',
            'AAAA/BBBB/',
            'AAAA/BBBB/CCCC/'
        ]


@freeze_time("2020-05-12 12:00:01")
class SubscriptionTest(TestCase):
    def setUp(self):
        body = mock.MagicMock()
        body.read.return_value = b'{"e": "2020-05-12 14:00:01", "c": "http://callback.com/1"}'

        self.obj = {'Body': body}

    def test_subscription_for_valid_object__should_have_callback_url(self):
        subscription = Subscription(self.obj, 'some_name', now=datetime.utcnow())
        assert subscription.is_valid
        assert not subscription.is_expired
        assert subscription.callback_url == 'http://callback.com/1'

    @freeze_time("2020-05-12 15:00:01")
    def test_subscription_for_expired_object__should_be_not_valid(self):
        subscription = Subscription(self.obj, 'some_name', now=datetime.utcnow())
        assert not subscription.is_valid
        assert subscription.is_expired

    def test_subscription__when_missing_callback__should_be_not_valid(self):
        self.obj['Body'].read.return_value = b'{}'
        subscription = Subscription(self.obj, 'some_name', now=datetime.utcnow())
        assert not subscription.is_valid
        assert subscription.error == "data missing required key:'c'"

    def test_subscription__when_missing_expiration__should_be_valid(self):
        self.obj['Body'].read.return_value = b'{"c": "http://callback.com/1"}'
        subscription = Subscription(self.obj, 'some_name', now=datetime.utcnow())
        assert subscription.is_valid


class SubscriptionsRepoTest(TestCase):
    def setUp(self):
        boto3_patch = mock.patch('libtrustbridge.repos.miniorepo.boto3')
        self.boto3 = boto3_patch.start()
        self.client = self.boto3.client.return_value
        self.addCleanup(boto3_patch.stop)
        self.connection_data = {
            'access_key': 'awsAccessKeyId',
            'secret_key': 'awsSecretAccessKey',
            'host': 'some_host',
            'port': '1111',
            'use_ssl': False,
        }

    def test_subscribe_by_id__should_put_object_into_repo(self):
        repo = SubscriptionsRepo(connection_data=self.connection_data)
        id = Id('some_ref')

        repo.subscribe_by_id(id, 'http://callback.url/1')
        self.client.put_object.assert_called_once()
        args, kwargs = self.client.put_object.call_args

        assert kwargs['Bucket'] == 'subscriptions'
        assert kwargs['ContentLength'] == 41
        assert kwargs['Key'] == 'some_ref'
        assert kwargs['Body'].read() == b'{"c": "http://callback.url/1", "e": null}'

    def test_subscribe_by_pattern__should_put_object_into_repo(self):
        repo = SubscriptionsRepo(connection_data=self.connection_data)
        pattern = Pattern('aaa.bbb.ccc')

        repo.subscribe_by_pattern(pattern, 'http://callback.url/1')
        self.client.put_object.assert_called_once()
        args, kwargs = self.client.put_object.call_args

        assert kwargs['Bucket'] == 'subscriptions'
        assert kwargs['ContentLength'] == 41
        assert kwargs['Key'] == 'AAA/BBB/CCC/ff0d1111f6636c354cf92c7137f1b5e6'
        assert kwargs['Body'].read() == b'{"c": "http://callback.url/1", "e": null}'

    def test_get_subscription_by_id__should_return_subscriptions(self):
        repo = SubscriptionsRepo(connection_data=self.connection_data)
        self.client.list_objects.return_value = {
            'Contents': [{'Key': 'some_ref'}]
        }
        self.client.get_object.return_value = {
            'Body': BytesIO(b'{"c": "http://callback.url/1", "e": null}'),
            'Bucket': 'subscriptions',
            'ContentLength': 39,
            'Key': 'some_ref',
        }

        subscriptions = repo.get_subscriptions_by_id(Id('some_ref'))

        assert list(subscriptions)[0].callback_url == 'http://callback.url/1'
        self.client.list_objects.assert_called_once_with(Bucket='subscriptions', Prefix='some_ref')
        self.client.get_object.assert_called_once_with(Bucket='subscriptions', Key='some_ref')

    def test_get_subscription_by_pattern__should_return_subscriptions(self):
        repo = SubscriptionsRepo(connection_data=self.connection_data)
        self.client.list_objects.side_effect = [
            {'Contents': []},
            {'Contents': [{'Key': 'AA/BB/ff0d1111f6636c354cf92c7137f1b5e6'}]}
        ]
        self.client.get_object.return_value = {
            'Body': BytesIO(b'{"c": "http://callback.url/1", "e": null}'),
            'Bucket': 'subscriptions',
            'ContentLength': 39,
            'Key': 'AA',
        }

        subscriptions = repo.get_subscriptions_by_pattern(Pattern('aa.bb'))

        assert list(subscriptions)[0].callback_url == 'http://callback.url/1'
        assert self.client.list_objects.mock_calls == [
            mock.call(Bucket='subscriptions', Prefix='AA/'),
            mock.call(Bucket='subscriptions', Prefix='AA/BB/')
        ]
        self.client.get_object.assert_called_once_with(Bucket='subscriptions', Key='AA/BB/ff0d1111f6636c354cf92c7137f1b5e6')
