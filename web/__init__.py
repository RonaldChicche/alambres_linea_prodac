import os

from flask import Flask
from importlib import import_module
from flask import request, jsonify, render_template_string
from flask_socketio import SocketIO, emit

from .ptz_app import *
from .esmeril_app import *
from .stream_namespaces import *
import base64

# Rutna para intentar conectar camaras

ptz_application = CameraWelding("192.168.90.108", "admin", "Bertek@206036")
ptz_app_tail = CameraTail("192.168.90.109", "admin", "Bertek@206036")
esmeril_application = EsmerilWebApp()


def register_blueprints(app):
    # for module_name in ('home'):
    module = import_module('web.home.routes')
    app.register_blueprint(module.blueprint)

def register_extensions(app, PlcParser):
    ptz_application.start(app)
    ptz_application.start_plc_thread(PlcParser)
    ptz_app_tail.start(app)
    ptz_app_tail.start_plc_thread(PlcParser)
    esmeril_application.start_plc_thread(PlcParser)

def create_app(config, PlcParser):
    app = Flask(__name__)
    app.config.from_object(config)
    register_blueprints(app)
    register_extensions(app, PlcParser)
    return app