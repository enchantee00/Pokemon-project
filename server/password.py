

from flask import Flask, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from flask_bcrypt import Bcrypt
from database_config import init_app, db
from models import Trainer, Pokemon, PokeDex, Move, PokemonMove,WildBattleRecord, GymBattleRecord, TypeEffectiveness
import random
import traceback
from collections import defaultdict
from sqlalchemy import text


app = Flask(__name__)
init_app(app)
bcrypt = Bcrypt(app)


with app.app_context():
    
    # 2. Fetch all trainers
    trainers = db.session.execute(text("SELECT id, role FROM trainers")).fetchall()

    # 3. Generate hashed password from role and update the password column
    for trainer in trainers:
        trainer_id = trainer.id
        role = trainer.role

        # Hash the role as the password
        hashed_password = bcrypt.generate_password_hash(role).decode('utf-8')

        # Update the password column for this trainer
        db.session.execute(
            text("UPDATE trainers SET password = :hashed_password WHERE id = :trainer_id"),
            {"hashed_password": hashed_password, "trainer_id": trainer_id}
        )

    db.session.commit()

    # 4. Set the 'password' column to NOT NULL
    db.session.execute(text("ALTER TABLE trainers ALTER COLUMN password SET NOT NULL"))
    db.session.commit()

print("Password column added and updated successfully.")
