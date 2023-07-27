from flask import Flask
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.jinja_env.filters['zip'] = zip
bootstrap = Bootstrap(app)


from app import views
