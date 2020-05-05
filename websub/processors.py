import logging

from websub.use_cases import DeliverCallbackUseCase


logger = logging.getLogger('callback_deliver')


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
