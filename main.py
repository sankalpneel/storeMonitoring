import psycopg2
from flask import Flask
from app.routes import api
import app.database as databse # Import your database connection configuration


# Create a Flask application
app = Flask(__name__)
# Register the API Blueprint
app.register_blueprint(api, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True)
