from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Trainer(db.Model):
    __tablename__ = 'trainers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    badges = db.Column(db.Integer, default=0)
    role = db.Column(db.String(50))  # e.g., Trainer or Gym Leader
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    pokemon = db.relationship('Pokemon', backref='trainer', lazy=True)

class Pokemon(db.Model):
    __tablename__ = 'pokemon'
    id = db.Column(db.Integer, primary_key=True)
    pokedex_id = db.Column(db.Integer, db.ForeignKey('pokedex.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    hp = db.Column(db.Integer, nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    moves = db.relationship('PokemonMove', backref='pokemon', lazy=True)

class PokeDex(db.Model):
    __tablename__ = 'pokedex'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type1 = db.Column(db.String(50))
    type2 = db.Column(db.String(50))
    hp_stat = db.Column(db.Integer, nullable=False)
    att = db.Column(db.Integer, nullable=False)
    def_stat = db.Column(db.Integer, nullable=False)
    spd = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Move(db.Model):
    __tablename__ = 'moves'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50))
    power = db.Column(db.Integer, nullable=False)  # Changed from "damage"
    pp = db.Column(db.Integer, nullable=False)  # Number of times move can be used
    accuracy = db.Column(db.Integer, nullable=False)

class PokemonMove(db.Model):
    __tablename__ = 'pokemonmoves'
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemon.id'), primary_key=True)
    move_id = db.Column(db.Integer, db.ForeignKey('moves.id'), primary_key=True)
    remaining_uses = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class WildBattleRecord(db.Model):
    __tablename__ = 'wildbattlerecords'
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainers.id'), nullable=False)
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemon.id'), nullable=False)
    result = db.Column(db.String(50), nullable=False)  # WIN, LOSE, or Capture
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class GymBattleRecord(db.Model):
    __tablename__ = 'gymbattlerecords'
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainers.id'), nullable=False)
    gym_leader_id = db.Column(db.Integer, db.ForeignKey('trainers.id'), nullable=False)
    result = db.Column(db.String(50), nullable=False)  # WIN or LOSE
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class TypeEffectiveness(db.Model):
    __tablename__ = 'typeeffectiveness'
    attack = db.Column(db.String(50), primary_key=True)
    defend = db.Column(db.String(50), primary_key=True)
    effectiveness = db.Column(db.Float, nullable=False)
