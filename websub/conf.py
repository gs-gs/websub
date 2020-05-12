from flask_env import MetaFlaskEnv
from libtrustbridge.utils.conf import env_s3_config, env_queue_config


class BaseConfig(metaclass=MetaFlaskEnv):
    DEBUG = False
    TESTING = False
    SUBSCRIPTIONS_REPO_CONF = env_s3_config('SUBSCRIPTIONS_REPO')
    SUBSCRIPTIONS_REPO_CLASS = 'websub.repos.SubscriptionsRepo'
    DELIVERY_OUTBOX_REPO_CLASS = 'websub.repos.DeliveryOutboxRepo'
    DELIVERY_OUTBOX_REPO_CONF = env_queue_config('PROC_DELIVERY_OUTBOX_REPO')
    NOTIFICATIONS_REPO_CLASS = 'websub.repos.NotificationsRepo'
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
    SUBSCRIPTIONS_REPO_CLASS = 'unittest.mock.Mock'
    SUBSCRIPTIONS_REPO_CONF = {}
    DELIVERY_OUTBOX_REPO_CLASS = 'unittest.mock.Mock'
    DELIVERY_OUTBOX_REPO_CONF = {}
    NOTIFICATIONS_REPO_CLASS = 'unittest.mock.Mock'
    NOTIFICATIONS_REPO_CONF = {}
