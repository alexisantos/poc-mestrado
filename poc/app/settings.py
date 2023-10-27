class Config(object):
    DEBUG = True
    TESTING = True

class Production(Config):
    DEBUG = False

class Development(Config):
    DEBUG = True

class TESTING(Config):
    TESTING = True