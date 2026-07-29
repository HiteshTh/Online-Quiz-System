from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_socketio import SocketIO

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()
# Initialize socketio without parameters, will run init_app in factory
socketio = SocketIO(cors_allowed_origins="*")

# Login manager configuration
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'
