from flask import Flask

'''
This follows the Application Factory pattern outlined here

http://flask.pocoo.org/docs/1.0/patterns/appfactories/
'''
def create_app(config):
    import nobisalexaservices.stockservice
    from nobisalexaservices import alexamaster

    app = Flask(__name__)
    app.register_blueprint(alexamaster.blueprint)
    app.register_blueprint(stockservice.blueprint)
    return app



