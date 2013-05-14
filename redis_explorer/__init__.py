from flask import Flask
app = Flask(__name__)

import redis_explorer.views
