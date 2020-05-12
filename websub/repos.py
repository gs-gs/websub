import hashlib
import json
import logging
from datetime import timedelta, datetime
from io import BytesIO

import dateutil
from libtrustbridge.repos import elasticmqrepo
from libtrustbridge.repos.miniorepo import MinioRepo

logger = logging.getLogger(__name__)


def expiration_datetime(seconds):
    return datetime.utcnow() + timedelta(seconds=seconds)


def url_to_filename(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()


class SubscriptionExpired(Exception):
    pass


class InvalidSubscriptionFormat(Exception):
    pass


class Id:
    def __init__(self, id):
        self.id = id

    def to_key(self):
        return self.id


class Pattern:
    def __init__(self, predicate):
        self.predicate = predicate

    def to_key(self, url=''):
        self._validate()
        if self.predicate.endswith('.'):
            self.predicate = self.predicate[:-1]
        if self.predicate.endswith('*'):
            self.predicate = self.predicate[:-1]

        predicate_parts = self.predicate.upper().split('.')
        key = '/'.join([p for p in predicate_parts if p]) + '/'
        if url:
            key += url_to_filename(url)
        return key

    def _validate(self):
        if not self.predicate:
            raise ValueError("non-empty predicate is required")
        if '/' in self.predicate:
            raise ValueError("predicate should contain dots, not slashes")
        if self.predicate.endswith('*') and self.predicate[-2] != '.':
            raise ValueError("* character is supported only after a dot")

    def to_layers(self):
        layers = []
        key = self.to_key()
        split_layers = [layer for layer in key.split("/") if layer]
        for i in range(0, len(split_layers)):
            layers.append("/".join(split_layers[0:i + 1]) + "/")
        return layers


class Subscription:
    CALLBACK_KEY = 'c'
    EXPIRATION_KEY = 'e'

    def __init__(self, payload, key, now: datetime):
        self.payload = payload
        self.key = key
        self.now = now
        try:
            self.data = self._decode(payload)
            self.is_valid = True
        except (InvalidSubscriptionFormat, SubscriptionExpired) as e:
            self.is_valid = False
            self.error = str(e)

    def _decode(self, payload):
        try:
            data = json.loads(payload.decode('utf-8'))
        except UnicodeError as e:
            raise InvalidSubscriptionFormat("data is not UTF-8") from e
        except ValueError as e:
            logger.warning("Tried to decode JSON data %s but failed", json_data)
            raise InvalidSubscriptionFormat("data is not a valid JSON") from e

        try:
            callback = data[self.CALLBACK_KEY]
            expiration = data.get(self.EXPIRATION_KEY)
            if expiration:
                data[self.EXPIRATION_KEY] = dateutil.parser.parse(expiration)
                self.is_expired = data[self.EXPIRATION_KEY] < self.now
                if self.is_expired:
                    raise SubscriptionExpired()
        except KeyError as e:
            raise InvalidSubscriptionFormat(f"data missing required key:{str(e)}") from e
        except (TypeError, ValueError) as e:
            raise InvalidSubscriptionFormat(f"expiration invalid format:{str(data[self.EXPIRATION_KEY])}") from e

        return data

    @property
    def callback_url(self):
        return self.data[self.CALLBACK_KEY]

    @classmethod
    def encode_obj(cls, callback, expiration_seconds):
        expiration = expiration_datetime(expiration_seconds).isoformat() if expiration_seconds else None
        data = {
            cls.CALLBACK_KEY: callback,
            cls.EXPIRATION_KEY: expiration
        }
        return json.dumps(data).encode('utf-8')


class SubscriptionsRepo(MinioRepo):
    DEFAULT_BUCKET = 'subscriptions'

    def subscribe_by_id(self, id: Id, url, expiration_seconds=None):
        key = id.to_key()
        self._subscribe_by_key(key, url, expiration_seconds)

    def subscribe_by_pattern(self, pattern: Pattern, url, expiration_seconds=None):
        key = pattern.to_key(url=url)
        self._subscribe_by_key(key, url, expiration_seconds)

    def get_subscriptions_by_id(self, id: Id):
        return self._get_subscriptions_by_key(id.to_key(), datetime.utcnow())

    def get_subscriptions_by_pattern(self, pattern: Pattern):
        """
        predicate pattern parameter is the primary search filter
        technically aaaa.bbbb.cccc.* == aaaa.bbbb.cccc
        This can be used for verbosity

        search predicate: a.b.c.d
        1. a = files in A/
        2. a.b = files in A/B/
        3. a.b.c = files in A/B/C/
        4. a.b.c.d files in A/B/C/D/

        Important: subscription AA.BB.CCCC is not equal to AA.BB.CC but includes
        AA.BB.CCCC.EE, and doesn't include AA.BB.CC.GG
        """
        subscriptions = set()
        now = datetime.utcnow()
        layers = pattern.to_layers()
        for storage_key in layers:
            subscriptions |= self._get_subscriptions_by_key(storage_key, now)

        return subscriptions

    def bulk_delete(self, keys):
        if not keys:
            return

        self.client.delete_objects(
            Bucket=self.bucket,
            Delete={
                'Objects': [
                    {'Key': key} for key in keys
                ],
                'Quiet': True,
            },
        )

    def _subscribe_by_key(self, key, url, expiration):
        subscription = Subscription.encode_obj(url, expiration)
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=BytesIO(subscription),
            ContentLength=len(subscription)
        )

    def _search_objects(self, storage_key):
        found_objects = set()

        listed_objects = self.client.list_objects(
            Bucket=self.bucket,
            Prefix=storage_key,
        )
        # Warning: this is very dumb way to iterate S3-like objects
        # works only on small datasets
        for obj in listed_objects.get('Contents', []):
            full_url = obj['Key']
            rel_url = full_url[len(storage_key):]
            if '/' in rel_url:
                # returned a file in subdirectory, ignore
                continue
            found_objects.add(obj['Key'])

        return found_objects

    def _get_subscriptions_by_key(self, key, now):
        subscriptions = set()

        found_objects = self._search_objects(key)
        for obj_key in found_objects:
            obj = self.client.get_object(
                Bucket=self.bucket,
                Key=obj_key,
            )
            payload = obj['Body'].read()
            subscription = Subscription(payload, obj_key, now)
            subscriptions.add(subscription)

        return subscriptions


class DeliveryOutboxRepo(elasticmqrepo.ElasticMQRepo):
    def _get_queue_name(self):
        return 'delivery-outbox'


class NotificationOutboxRepo(elasticmqrepo.ElasticMQRepo):
    def _get_queue_name(self):
        return 'notifications'

