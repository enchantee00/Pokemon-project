from flask_sqlalchemy import SQLAlchemy
from models import db

def init_app(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://ec2-user:password@localhost/pokemon_database'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

# DB_CONFIG = {
#     'host': 'localhost',
#     'database': 'pokemon_database',
#     'user': 'ec2-user',
#     'password': 'password',
#     'port': '5432'  # 기본 포트
# }