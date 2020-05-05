from unittest import mock
from websub.processors import CallbacksDeliveryProcessor


@mock.patch('websub.processors.DeliverCallbackUseCase', autospec=True)
def test(DeliverCallbackUseCase, delivery_outbox_repo):
    processor = CallbacksDeliveryProcessor()
    # checking proper initialization
    DeliverCallbackUseCase.assert_called_once_with()

    assert iter(processor) == processor

    use_case = DeliverCallbackUseCase.return_value
    use_case.execute.return_value = False
    assert next(processor) is False
    use_case.execute.return_value = True
    assert next(processor) is True
    use_case.execute.return_value = None
    assert next(processor) is None
    use_case.execute.return_value = True
    use_case.execute.side_effect = Exception('Test')
    assert next(processor) is None
