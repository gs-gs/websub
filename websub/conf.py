from flask_env import MetaFlaskEnv

from websub.common.conf_helpers import env_s3_config, env_queue_config


class BaseConfig(metaclass=MetaFlaskEnv):
    DEBUG = False
    TESTING = False
    SUBSCRIPTIONS_REPO_CONF = env_s3_config('SUBSCRIPTIONS_REPO')
    SUBSCRIPTIONS_REPO_CLASS = 'intergov.repos.subscriptions.SubscriptionsRepo'
    DELIVERY_OUTBOX_REPO_CLASS = 'intergov.repos.delivery_outbox.DeliveryOutboxRepo'
    DELIVERY_OUTBOX_REPO_CONF = env_queue_config('PROC_DELIVERY_OUTBOX_REPO')
    NOTIFICATIONS_REPO_CLASS = env_queue_config('intergov.repos.notifications.NotificationsRepo')
    NOTIFICATIONS_REPO_CONF = env_queue_config('NOTIFICATIONS_REPO_CONF')


class ProductionConfig(BaseConfig):
    ENV = 'production'


class DevelopmentConfig(BaseConfig):
    ENV = 'development'
    DEBUG = True
    TESTING = False


class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True
