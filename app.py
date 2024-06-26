import os
import logging
from flask import Flask
from extensions import db
from sqlalchemy import text
from seed import seed_challenges
from flask_cors import CORS

# Initialize logging
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

# Determine if the app is running on Heroku
IS_HEROKU = 'DYNO' in os.environ

# Load environment variables only if not on Heroku
if not IS_HEROKU:
    from dotenv import load_dotenv

    load_dotenv()

# Import the create_app function from your views package
from views import create_app

# Call create_app to initialize your Flask application and register routes
app = create_app()

CORS(app, resources={r"/*": {"origins": "*"}})

# Configure the SQLAlchemy database URI
if IS_HEROKU:
    stackhero_url = os.environ['STACKHERO_MYSQL_DATABASE_URL']
    stackhero_url = stackhero_url.replace('mysql://', 'mysql+pymysql://')
    stackhero_url = stackhero_url.split('?')[0]  # Remove the query parameters
    ssl_cert = os.environ['SSL_KEY']

    # Check if the server.crt file exists and has contents
    if not os.path.exists('server.crt') or os.path.getsize('server.crt') == 0:
        with open('server.crt', 'w') as f:
            f.write(ssl_cert)

    app.config['SQLALCHEMY_DATABASE_URI'] = stackhero_url + '?ssl_ca=server.crt'
else:
    # When running locally, take the database URI from the .env file
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')

# Prevent SQLAlchemy from tracking modifications
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the SQLAlchemy app
db.init_app(app)


# Function to test database connection
def test_db_connection():
    try:
        with app.app_context():
            with db.engine.connect() as connection:
                # Using the text() construct to execute a simple query
                result = connection.execute(text("SELECT 1"))
                for row in result:
                    logging.info("Database connection test was successful. Result: {}".format(row))
    except Exception as e:
        logging.error(f"Database connection test failed: {e}")


# Function to create tables and seed data
def create_tables_and_seed_data():
    with app.app_context():
        db.create_all()
        seed_challenges(app)
        logging.info("Database tables created successfully.")
        test_db_connection()  # Test database connection


# Create tables and seed data
create_tables_and_seed_data()

if __name__ == '__main__':
    # Run the Flask app
    # The host must be set to '0.0.0.0' to be accessible within the Heroku dyno
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
