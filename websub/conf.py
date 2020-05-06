from flask_env import MetaFlaskEnv

from websub.common.conf_helpers import env_s3_config, env_queue_config


class BaseConfig(metaclass=MetaFlaskEnv):
    DEBUG = False
    TESTING = False
    SUBSCRIPTION_REPO_CONF = env_s3_config('SUBSCRIPTION_REPO')
    SUBSCRIPTION_REPO_CLASS = 'intergov.repos.subscriptions.SubscriptionsRepo'
    DELIVERY_OUTBOX_REPO_CLASS = 'intergov.repos.delivery_outbox.DeliveryOutboxRepo'
    DELIVERY_OUTBOX_REPO_CONF = env_queue_config('PROC_DELIVERY_OUTBOX_REPO')
    NOTIFICATION_REPO_CLASS = env_queue_config('intergov.repos.notifications.NotificationsRepo')
    NOTIFICATION_REPO_CONF = env_queue_config('NOTIFICATION_REPO_CONF')


class ProductionConfig(BaseConfig):
    ENV = 'production'


class DevelopmentConfig(BaseConfig):
    ENV = 'development'
    DEBUG = True
    TESTING = False


class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True
