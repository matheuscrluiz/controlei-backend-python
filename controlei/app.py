# coding: utf-8
from flask import Flask
from flask_cors import CORS
from controlei.view.bp.root_blueprint import init_app
import warnings
warnings.filterwarnings(
    "ignore",
    message="pandas only supports SQLAlchemy connectable"
)


def create_app():

    app = Flask(__name__)
    app.config['PROPAGATE_EXCEPTIONS'] = True
    init_app(app)
    CORS(app)

    return app
