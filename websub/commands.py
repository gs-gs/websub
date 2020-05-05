import time

from flask_script import Command

from websub.processors import CallbacksDeliveryProcessor


class RunCallbacksDeliveryProcessor(Command):
    def run(self):
        for result in CallbacksDeliveryProcessor():
            # no message was processed, might not have been any, sleep
            # or the exception has been raised, sleep as well
            if result is None:
                time.sleep(1)
