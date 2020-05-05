import uuid
from unittest import mock

from websub.use_cases import DeliverCallbackUseCase


def test_deliver_callback_ok(delivery_outbox_repo):
    dummy_url = 'http://dummy_url.com/404'
    job = {
        's': dummy_url,
        'message': mock.Mock()
    }
    delivery_outbox_repo.get_job.return_value = (uuid.uuid4(), job)

    use_case = DeliverCallbackUseCase()
    use_case._deliver_notification = mock.Mock()  # this should be delegating to a repo

    assert use_case.execute() is not None
    assert use_case.execute() is not False


@mock.patch('websub.use_cases.requests')
def test_deliver_notification(requests):
    dummy_url = 'http://dummy_url.com/404'
    use_case = DeliverCallbackUseCase()

    response = mock.Mock()
    response.status_code = 200
    requests.post.return_value = response

    assert use_case._deliver_notification(dummy_url, {'payload': 'payload'})
    response.status_code = 400
    assert not use_case._deliver_notification(dummy_url, {'payload': 'payload'})


def test_not_deleted(delivery_outbox_repo):
    dummy_url = 'http://dummy_url.com/404'
    job = {
        's': dummy_url,
        'message': mock.Mock()
    }
    delivery_outbox_repo.get_job.return_value = (uuid.uuid4(), job)
    delivery_outbox_repo.delete.return_value = False
    use_case = DeliverCallbackUseCase()
    assert not use_case.execute()


def test_deliver_callback_none_if_no_jobs(delivery_outbox_repo):
    delivery_outbox_repo.get_job.return_value = None

    use_case = DeliverCallbackUseCase()

    assert use_case.execute() is None


def test_deliver_callback_false_if_max_retries_exceeded(delivery_outbox_repo):
    dummy_url = 'http://dummy_url.com/404'
    job = {
        's': dummy_url,
        'message': mock.Mock(),
        'retry': 5
    }
    delivery_outbox_repo.get_job.return_value = (uuid.uuid4(), job)
    delivery_outbox_repo.delete.return_value = True
    use_case = DeliverCallbackUseCase()
    use_case._deliver_notification = mock.Mock()

    use_case.MAX_RETRIES = 4
    assert use_case.execute() is False
    assert delivery_outbox_repo.delete.was_called()
    use_case.MAX_RETRIES = 6
    assert use_case.execute() is True
    assert delivery_outbox_repo.delete.was_called()
    use_case.MAX_RETRIES = 5
    use_case._deliver_notification = mock.Mock()
    use_case._deliver_notification.return_value = False
    assert use_case.execute() is False
    delivery_outbox_repo.post_job.assert_not_called()


def test_deliver_callback_false_if_delivery_fails(delivery_outbox_repo):
    dummy_url = 'http://dummy_url.com/404'
    job = {
        's': dummy_url,
        'message': mock.Mock()
    }
    delivery_outbox_repo.get_job.return_value = (uuid.uuid4(), job)

    use_case = DeliverCallbackUseCase()
    failing_delivery = mock.Mock()
    failing_delivery.side_effect = Exception()
    use_case._deliver_notification = failing_delivery

    assert use_case.execute() is False
    assert delivery_outbox_repo.delete.was_called()


def test_deliver_callback_resubmits_on_fail(delivery_outbox_repo):
    dummy_url = 'http://dummy_url.com/404'
    job = {
        's': dummy_url,
        'message': mock.Mock()
    }
    delivery_outbox_repo.get_job.return_value = (uuid.uuid4(), job)

    use_case = DeliverCallbackUseCase()
    failing_delivery = mock.Mock()
    failing_delivery.side_effect = Exception()
    use_case._deliver_notification = failing_delivery
    use_case.execute()

    assert delivery_outbox_repo.post_job.was_called()


def test_deliver_callback_does_not_resubmit_on_success():
    dummy_url = 'http://dummy_url.com/404'
    delivery_outbox_repo = mock.Mock()
    job = {
        's': dummy_url,
        'message': mock.Mock()
    }
    delivery_outbox_repo.get_job.return_value = (uuid.uuid4(), job)

    use_case = DeliverCallbackUseCase()
    passing_delivery = mock.Mock()
    passing_delivery.return_value = True
    use_case._deliver_notification = passing_delivery
    use_case.execute()

    assert delivery_outbox_repo.post_job.not_called()
