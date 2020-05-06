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
def subscriptions_repo():
    repo = mock.Mock()
    inject.clear_and_configure(lambda binder: binder.bind('SubscriptionsRepo', repo))
    yield repo
    inject.clear()


@pytest.yield_fixture(scope='module')
def notifications_repo():
    repo = mock.Mock()

    inject.clear_and_configure(lambda binder: binder.bind('NotificationsRepo', repo))
    yield repo
    inject.clear()
