import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from flask_migrate import upgrade

app = create_app()
with app.app_context():
    upgrade()
    print('Migration applied successfully')