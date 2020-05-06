import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SubscriptionExpired(Exception):
    pass


class InvalidSubscriptionFormat(Exception):
    pass


class SubscriptionsBaseRepo(ABC):
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
