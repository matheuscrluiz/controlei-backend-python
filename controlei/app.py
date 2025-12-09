# coding: utf-8
from flask import Flask
from controlei.view.bp.root_blueprint import init_app


def create_app():

    app = Flask(__name__)
    app.config['PROPAGATE_EXCEPTIONS'] = True
    init_app(app)

    return app
