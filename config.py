import os


class Config:
    """Configuracion base compartida por todos los entornos."""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-temporal-desarrollo')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', Config.SQLALCHEMY_DATABASE_URI)


class ProductionConfig(Config):
    DEBUG = False


config_por_nombre = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
