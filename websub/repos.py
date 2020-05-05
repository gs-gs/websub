import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SubscriptionExpired(Exception):
    pass


class InvalidSubscriptionFormat(Exception):
    pass


class SubscriptionBaseRepo(ABC):
    def __init__(self, connection_data):
        self.connection_data = connection_data

    @abstractmethod
    def search(self, predicate_pattern, url=None, recursive=False, layered=False):
        pass

    @abstractmethod
    def post(self, url, predicate_pattern):
        pass

    @abstractmethod
    def delete(self, url, predicate_pattern, recursive=False):
        pass


class DeliveryOutboxBaseRepo(ABC):
    def __init__(self, connection_data):
        self.connection_data = connection_data

    @abstractmethod
    def get_job(self):
        pass

    @abstractmethod
    def post_job(self, payload, delay_seconds=0):
        pass

    @abstractmethod
    def delete(self, message_id):
        pass


class SubscriptionSampleRepo(SubscriptionBaseRepo):
    def search(self, predicate_pattern, url=None, recursive=False, layered=False):
        print(predicate_pattern)

    def post(self, url, predicate_pattern):
        print(predicate_pattern)

    def delete(self, url, predicate_pattern, recursive=False):
        print(predicate_pattern)


class DeliveryOutboxSampleRepo(DeliveryOutboxBaseRepo):
    def get_job(self):
        pass

    def post_job(self, payload, delay_seconds=0):
        pass

    def delete(self, message_id):
        pass
