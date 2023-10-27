import os
from flask import Flask
from flask_restful import Api
from app.resources.apicheck_resource import APIcheck_Resource
from app.resources.traduzir_resource import TraduzirResource

def create_app():
    app = Flask(__name__)
    api = Api(app)

    #app.config['ENV'] = 'development'
    #app.config['DEBUG'] = True

    if 'FLASK_CONFIG' in os.environ.keys():
        app.config.from_object('app.settings.' + os.environ['FLASK_CONFIG'])
    else:
        app.config.from_object('app.settings.Development')

    api.add_resource(APIcheck_Resource, '/api_check')
    api.add_resource(TraduzirResource, '/translate')

    return app