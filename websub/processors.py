import logging

logger = logging.getLogger(__name__)


class Processor(object):
    """
    Iterate over the use case.
    """
    def __init__(self, use_case):
        self.use_case = use_case

    def __iter__(self):
        logger.info("Starting the outbound callbacks processor")
        return self

    def __next__(self):
        try:
            result = self.use_case.execute()
        except Exception as e:
            logger.exception(e)
            result = None
        return result
