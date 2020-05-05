import inject
from flask import Flask

from werkzeug.utils import import_string

from .conf import BaseConfig
from . import views


def create_app(config_object=None):
    if config_object is None:
        config_object = BaseConfig

    app = Flask(__name__)
    app.config.from_object(config_object)
    app.register_blueprint(views.blueprint)

    def inject_config(binder):
        SubscriptionRepo = import_string(app.config['SUBSCRIPTION_REPO_CLASS'])
        binder.bind('SubscriptionRepo', SubscriptionRepo(app.config['SUBSCRIPTION_REPO_CONF']))

        DeliveryOutboxRepo = import_string(app.config['DELIVERY_OUTBOX_REPO_CLASS'])
        binder.bind('DeliveryOutboxRepo', DeliveryOutboxRepo(app.config['DELIVERY_OUTBOX_REPO_CONF']))

    inject.configure(inject_config)

    return app
