from unittest import mock

import inject
import pytest


@pytest.yield_fixture(scope='module')
def delivery_outbox_repo():
    repo = mock.Mock()
    inject.clear_and_configure(lambda binder: binder.bind('DeliveryOutboxRepo', repo))
    yield repo
    inject.clear()


@pytest.yield_fixture(scope='module')
def subscription_repo():
    repo = mock.Mock()
    inject.clear_and_configure(lambda binder: binder.bind('SubscriptionRepo', repo))
    yield repo
    inject.clear()


@pytest.yield_fixture(scope='module')
def notification_repo():
    repo = mock.Mock()

    inject.clear_and_configure(lambda binder: binder.bind('NotificationRepo', repo))
    yield repo
    inject.clear()
