import logging

from websub.use_cases import DeliverCallbackUseCase, DispatchMessageToSubscribersUseCase

logger = logging.getLogger(__name__)


class CallbacksDeliveryProcessor(object):
    """
    Iterate over the DeliverCallbackUseCase.
    """
    def __init__(self):
        self.uc = DeliverCallbackUseCase()

    def __iter__(self):
        logger.info("Starting the outbound callbacks processor")
        return self

    def __next__(self):
        try:
            result = self.uc.execute()
        except Exception as e:
            logger.exception(e)
            result = None
        return result


class CallbacksSpreaderProcessor(object):
    """
    Convert each incoming message to set of messages containing (websub_url, message)
    so they may be sent and fail separately
    """

    def __init__(self,):
        self.uc = DispatchMessageToSubscribersUseCase()

    def __iter__(self):
        logger.info("Starting the outbound callbacks processor")
        return self

    def __next__(self):
        try:
            result = self.uc.execute()
        except Exception as e:
            logger.exception(e)
            result = None
        return result
