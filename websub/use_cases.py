import json
import logging
import random

import inject
import requests

from websub.serializers import MessageJSONEncoder

logger = logging.getLogger(__name__)


class SubscriptionRegisterUseCase:
    """
    Used by the subscription API

    Initialised with the subscription repo,
    saves url, predicate(pattern), expiration to the storage.
    """

    subscriptions = inject.attr('SubscriptionRepo')

    def execute(self, url, pattern, expiration):
        # this operation deletes all previous subscription for given url and pattern
        # and replaces them with new one. Techically it's create or update operation
        posted = self.subscriptions.post(url, pattern, expiration)
        if not posted:
            return None
        return True


class SubscriptionDeregisterUseCase:
    """
    Used by the subscription API

    on user's request removes the subscription to given url for given pattern
    """

    subscriptions = inject.attr('SubscriptionRepo')

    def execute(self, url, pattern):
        return self.subscriptions.delete(url, pattern) > 0


class DispatchMessageToSubscribersUseCase:
    """
    Used by the callbacks spreader worker.

    This is the "fan-out" part of the WebSub,
    where each event dispatched
    to all the relevant subscribers.
    For each event (notification),
    it looks-up the relevant subscribers
    and dispatches a callback task
    so that they will be notified.

    There is a downstream delivery processor
    that actually makes the callback,
    it is insulated from this process
    by the delivery outbox message queue.

    Note: In this application
    the subscription signature
    is based on the message predicate.
    """
    subscriptions = inject.attr('SubscriptionRepo')
    delivery_outbox = inject.attr('DeliveryOutboxRepo')
    notifications = inject.attr('NotificationRepo')

    def execute(self):
        fetched_publish = self.notifications.get_job()
        if not fetched_publish:
            return None
        (publish_msg_id, message_job) = fetched_publish
        return self.process(publish_msg_id, message_job)

    def process(self, publish_msg_id, message_job):
        # message_job is either a Message class
        # or a dict with 'message' field which is Message
        # which may be empty
        # or just a dict which must be sent as a callback directly
        message = message_job.get('message')
        predicate = message_job.get('predicate') or message.predicate
        assert predicate

        # find the subscribers for this predicate
        subscribers = self._get_subscribers(predicate)

        # what is worse, multiple delivery or lost messages?
        # here we assume lost messages are worse
        # given the delivery outbox is just a queue there aren't many reasons
        # for it to fail, real fails will be on the next step - when it's trivial
        # to re-process the single message when other ones will be fine.
        # (see DeliverCallbackUseCase)
        all_OK = True

        if message:
            payload = json.dumps(message, cls=MessageJSONEncoder)
        else:
            payload = message_job

        for s in subscribers:
            job = {
                's': s,  # subscribed callback url
                'payload': payload  # the payload to be sent to the callback
            }
            logger.info("Scheduling notification of \n[%s] with payload \n%s", s, payload)
            status = self.delivery_outbox.post_job(job)
            if not status:
                all_OK = False

        if all_OK:
            self.notifications.delete(publish_msg_id)
            return True
        else:
            return False

    def _get_subscribers(self, predicate):
        subscribers = self.subscriptions.search(predicate, layered=True)
        if not subscribers:
            logger.info("Nobody to notify about the message %s", predicate)
        return subscribers


class DeliverCallbackUseCase:
    """
    Is used by a callback deliverer worker

    Reads queue delivery_outbox_repo consisting of tasks in format:
        (url, message)

    Then such message should be either sent to this URL and the task is deleted
    or, in case of any error, not to be deleted and to be tried again
    (up to MAX_RETRIES times)

    TODO: rate limits, no more than 100 messages to a single url per 10 seconds?
    """

    MAX_RETRIES = 2
    delivery_outbox = inject.attr('DeliveryOutboxRepo')

    def execute(self):
        deliverable = self.delivery_outbox.get_job()
        if not deliverable:
            return None
        else:
            (queue_msg_id, job) = deliverable
        return self.process(queue_msg_id, job)

    def process(self, queue_msg_id, job):
        # TODO: test to ensure this message has a callback_url
        subscribe_url = job['s']
        payload = job.get('payload')

        retry_number = int(job.get('retry', 0))
        # second line of defence. Just in case

        if retry_number > self.MAX_RETRIES:
            logger.error(
                "Dropping notification %s about %s due to max retries reached",
                subscribe_url,
                payload
            )
            self.delivery_outbox.delete(queue_msg_id)
            return False

        try:
            is_delivered = self._deliver_notification(
                subscribe_url, payload
            )
        except Exception as e:
            logger.exception(e)
            is_delivered = False

        # we always delete a message, because we want to re-send it with
        # retries count increased
        deleted = self.delivery_outbox.delete(queue_msg_id)
        if not deleted:
            # quite strange, may be the same message is being processed twice
            # or it's already exhausted it's retry count on the
            # queue broker side
            logger.error(
                "Unable to delete message %s from the delivery_outbox",
                queue_msg_id
            )
            return False

        if not is_delivered:
            # @Neketek: I think it's better to not post the job at all instead of filtering it
            if retry_number + 1 > self.MAX_RETRIES:
                logger.error(
                    "Dropping notification %s about %s due to max retries reached",
                    subscribe_url,
                    payload
                )
                return False
            logger.info("Delivery failed, re-schedule it")
            self.delivery_outbox.post_job(
                {
                    's': subscribe_url,
                    'payload': payload,
                    'retry': retry_number + 1
                },
                # put it to the end of queue and with some nice delay
                # TODO: delay = retry_number * 30 + random.randint(0, 100)
                # for real cases (it's too slow for development)
                delay_seconds=random.randint(1, 10)
            )
            return False

        return True

    def _deliver_notification(self, url, payload):
        # https://indieweb.org/How_to_publish_and_consume_WebSub
        # https://www.w3.org/TR/websub/#x7-content-distribution
        # TODO: respect Retry-After header from the receiver
        # TODO: move to env variable, is unlikely to be used anyway
        hub_url = "127.0.0.1:5102"

        logger.info(
            "Sending WebSub payload \n    %s to callback URL \n    %s",
            payload, url
        )
        resp = requests.post(
            url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'Link': '<https://{}/>; rel="hub"'.format(
                    hub_url,
                ),
            }
        )

        if str(resp.status_code).startswith('2'):
            return True
        else:
            logger.error(
                "Subscription url %s seems to be invalid, returns %s",
                url,
                resp.status_code
            )
            return False
