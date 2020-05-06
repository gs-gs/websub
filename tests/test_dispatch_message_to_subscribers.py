import random
import uuid
from functools import partial
from unittest import TestCase, mock

import inject

from websub.use_cases import DispatchMessageToSubscribersUseCase


def bind_repos(binder, repos):
    for repo_name, repo in repos.items():
        binder.bind(repo_name, repo)


def random_urls(*kwargs, **args):
    return [
        "https://{}.{}/{}".format(
            uuid.uuid4(),
            random.choice(['com', 'net', 'org', 'com.au', 'gov.au']),
            uuid.uuid4()
        ) for x in range(6)]


class TestDispatchMessageToSubscribersUseCase(TestCase):
    def setUp(self):
        self.message_dict = {'message': 'some_message', 'predicate': 'some_predicate'}
        self.subscriptions_repo = mock.Mock()
        self.delivery_outbox_repo = mock.Mock()
        self.notifications_repo = mock.Mock()
        repos = {
            'SubscriptionsRepo': self.subscriptions_repo,
            'DeliveryOutboxRepo': self.delivery_outbox_repo,
            'NotificationsRepo': self.notifications_repo
        }

        inject.clear_and_configure(partial(bind_repos, repos=repos))
        self.addCleanup(inject.clear)

    def test_delivery_enqueued(self):
        self.notifications_repo.get_job.return_value = (1234, self.message_dict)
        self.delivery_outbox_repo.post_job.return_value = True
        self.subscriptions_repo.search.return_value = ['https://foo.com/bar', ]
        use_case = DispatchMessageToSubscribersUseCase()
        use_case.execute()

        assert self.delivery_outbox_repo.post_job.called
        assert self.notifications_repo.delete.called

    def test_notifications_empty_no_send(self):
        self.notifications_repo.get_job.return_value = ()
        self.subscriptions_repo.search.return_value = ['https://foo.com/bar', ]
        use_case = DispatchMessageToSubscribersUseCase()
        use_case.execute()

        assert not self.delivery_outbox_repo.post_job.called

    def test_delivery_outbox_post_fail_no_delete(self):
        self.notifications_repo.get_job.return_value = (123, self.message_dict)
        self.delivery_outbox_repo.post_job.return_value = False  # post failed
        self.subscriptions_repo.search.return_value = ['https://foo.com/bar', ]
        use_case = DispatchMessageToSubscribersUseCase()
        use_case.execute()

        assert not self.notifications_repo.delete.called

    def test_multiple_descriptions(self):
        self.notifications_repo.get_job.return_value = (123, self.message_dict)
        self.delivery_outbox_repo.post_job.return_value = False  # post failed
        self.subscriptions_repo.search.side_effect = random_urls
        use_case = DispatchMessageToSubscribersUseCase()
        use_case.execute()

        assert not self.notifications_repo.delete.called
