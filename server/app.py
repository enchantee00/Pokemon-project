from flask import Flask, request, jsonify, session
from sqlalchemy.exc import SQLAlchemyError
from flask_bcrypt import Bcrypt
from flask_session import Session
from database_config import init_app, db
from models import Trainer, Pokemon, PokeDex, Move, PokemonMove,WildBattleRecord, GymBattleRecord, TypeEffectiveness
import random
import traceback
from collections import defaultdict
from sqlalchemy.sql import func
from flask_cors import CORS
from functools import wraps
from dotenv import load_dotenv
import os


app = Flask(__name__)
init_app(app)
bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True)  # 모든 도메인에서의 요청 허용


# app.config['SESSION_TYPE'] = 'filesystem'  # 세션 저장소를 서버 파일로 설정
# Session(app)


# load_dotenv()  # .env 파일 로드
# app.secret_key = os.getenv('FLASK_SECRET_KEY')


# app.config.update({
#     'SESSION_COOKIE_SECURE': False,      # HTTPS에서만 세션 쿠키 허용
#     'SESSION_COOKIE_SAMESITE': None
# })


# Badges 값에 따른 레벨 범위
BADGE_LEVEL_RANGES = {
    0: (1, 12),
    1: (13, 18),
    2: (19, 24),
    3: (19, 24),
    4: (25, 37),
    5: (25, 37),
    6: (25, 37),
    7: (38, 40),
    8: (41, 53)
}

current_role = None

# 권한 검증 데코레이터
def role_required(required_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # trainer_id = session.get('trainer_id')
            # if not trainer_id:
            #     return jsonify({'error': 'Authentication required'}), 402
            
            # # Fetch user and their role from the database
            # trainer = Trainer.query.get(trainer_id)
            print(current_role)
            if not current_role or current_role not in required_roles:
                return jsonify({'error': 'Permission denied'}), 403
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


@app.errorhandler(404)
def not_found_error(e):
    """404 Not Found 처리"""
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_server_error(e):
    """500 Internal Server Error 처리"""
    return jsonify({"error": "An unexpected error occurred"}), 500

# @app.before_request
# def debug_session():
#     print("Session before request:", dict(session))
#     print("Request Cookies:", request.cookies)
    

# @app.after_request
# def after_request(response):
#     print("Session after request:", dict(session))
#     return response


@app.route('/')
def home():
    return "Hello! World!"

# --- Admin API ---
@app.route('/trainers', methods=['GET'])
@role_required(['Admin'])
def get_trainers():
    """모든 트레이너 조회"""
    try:
        trainers = Trainer.query.all()
        return jsonify([{
            'id': trainer.id,
            'name': trainer.name,
            'badges': trainer.badges,
            'role': trainer.role,
            'created_at': trainer.created_at
        } for trainer in trainers])
    except Exception as e:
        db.session.rollback()
        error_trace = traceback.format_exc()
        return jsonify({"error": str(e), "trace": error_trace}), 500
    
    
@app.route('/trainers/<int:id>', methods=['PUT'])
@role_required(["Admin"])
def update_trainer(id):
    """특정 트레이너 정보 업데이트"""
    data = request.json
    trainer = Trainer.query.get(id)
    if not trainer:
        return jsonify({'error': 'Trainer not found'}), 404

    trainer.name = data.get('name', trainer.name)
    trainer.badges = data.get('badges', trainer.badges)
    trainer.role = data.get('role', trainer.role)
    db.session.commit()
    return jsonify({'message': 'Trainer updated successfully'})


@app.route('/trainers/<int:id>', methods=['DELETE'])
@role_required(["Admin"])
def delete_trainer(id):
    """특정 트레이너 삭제"""
    trainer = Trainer.query.get(id)
    if not trainer:
        return jsonify({'error': 'Trainer not found'}), 404

    db.session.delete(trainer)
    db.session.commit()
    return jsonify({'message': 'Trainer deleted successfully'})


# --- Pokemon Manager API ---
@app.route('/pokemons', methods=['GET'])
@role_required(['Pokemon Manager'])
def get_pokemons():
    """모든 포켓몬 조회"""
    pokemons = Pokemon.query.all()
    
    id = db.Column(db.Integer, primary_key=True)
    pokedex_id = db.Column(db.Integer, db.ForeignKey('pokedex.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    hp = db.Column(db.Integer, nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    return jsonify([{
        'id': pokemon.id,
        'pokedex_id': pokemon.pokedex_id,
        'name': pokemon.name,
        'level': pokemon.level,
        'experience': pokemon.experience,
        'hp': pokemon.hp,
        'trainer_id': pokemon.trainer_id,
        'created_at': pokemon.created_at
    } for pokemon in pokemons])
    
    
@app.route('/pokedex', methods=['GET'])
@role_required(['Pokemon Manager'])
def get_pokedex():
    """포케덱스에 있는 모든 포켓몬 조회"""
    pokemons = PokeDex.query.all()
    
    return jsonify([{
        'id': pokemon.id,
        'name': pokemon.name,
        'type1': pokemon.type1,
        'type2': pokemon.type2,
        'hp_stat': pokemon.hp_stat,
        'att': pokemon.att,
        'def_stat': pokemon.def_stat,
        'spd': pokemon.spd,
        'front_img': pokemon.front_img,
        'back_img': pokemon.back_img,
        'created_at': pokemon.created_at
    } for pokemon in pokemons])


@app.route('/pokedex/<int:pokemon_id>', methods=['PUT'])
@role_required(['Pokemon Manager'])
def update_pokemon_stats(pokemon_id):
    """포케덱스에 있는 포켓몬 스탯 수정"""
    
    # 요청 데이터 받기
    data = request.get_json()
    
    # 수정할 값들 (기본값 설정)
    new_hp_stat = data.get('hp_stat', None)
    new_att = data.get('att', None)
    new_def_stat = data.get('def_stat', None)
    new_spd = data.get('spd', None)
    
    # 해당 포켓몬을 찾기
    pokemon = PokeDex.query.get(pokemon_id)
    
    if not pokemon:
        return jsonify({"error": "Pokemon not found"}), 404
    
    # 수정할 값이 제공되었으면 해당 포켓몬의 스탯을 업데이트
    if new_hp_stat is not None:
        pokemon.hp_stat = new_hp_stat
    if new_att is not None:
        pokemon.att = new_att
    if new_def_stat is not None:
        pokemon.def_stat = new_def_stat
    if new_spd is not None:
        pokemon.spd = new_spd
    
    try:
        # 데이터베이스 세션 커밋
        db.session.commit()
        return jsonify({
            'id': pokemon.id,
            'name': pokemon.name,
            'type1': pokemon.type1,
            'type2': pokemon.type2,
            'hp_stat': pokemon.hp_stat,
            'att': pokemon.att,
            'def_stat': pokemon.def_stat,
            'spd': pokemon.spd,
            'front_img': pokemon.front_img,
            'back_img': pokemon.back_img,
            'created_at': pokemon.created_at
        })
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update Pokemon stats"}), 500


# --- 기술 관리자 API ---
@app.route('/moves', methods=['GET'])
@role_required(['Skill Manager'])
def get_moves():
    """모든 기술 조회"""
    moves = Move.query.all()
    
    return jsonify([{
        'id': move.id,
        'name': move.name,
        'type': move.type,
        'power': move.power,
        'pp': move.pp,
        'accuracy': move.accuracy
    } for move in moves])

@app.route('/moves/<int:move_id>', methods=['PUT'])
@role_required(['Skill Manager'])
def update_move(move_id):
    """기술의 스탯 수정"""
    
    # 요청 데이터 받기
    data = request.get_json()
    
    # 수정할 값들 (기본값 설정)
    new_power = data.get('power', None)
    new_pp = data.get('pp', None)
    new_accuracy = data.get('accuracy', None)
    
    # 해당 기술을 찾기
    move = Move.query.get(move_id)
    
    if not move:
        return jsonify({"error": "Move not found"}), 404
    
    # 수정할 값이 제공되었으면 해당 기술의 스탯을 업데이트
    if new_power is not None:
        move.power = new_power
    if new_pp is not None:
        move.pp = new_pp
    if new_accuracy is not None:
        move.accuracy = new_accuracy
    
    try:
        # 데이터베이스 세션 커밋
        db.session.commit()
        return jsonify({
            'id': move.id,
            'name': move.name,
            'type': move.type,
            'power': move.power,
            'pp': move.pp,
            'accuracy': move.accuracy
        })
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update move"}), 500


@app.route('/typeeffectiveness', methods=['GET'])
@role_required(['Skill Manager'])
def get_type_effectiveness():
    """모든 타입 효과 조회"""
    effectiveness = TypeEffectiveness.query.all()
    
    return jsonify([{
        'attack': item.attack,
        'defend': item.defend,
        'effectiveness': item.effectiveness
    } for item in effectiveness])



@app.route('/typeeffectiveness/<attack_type>/<defend_type>', methods=['PUT'])
@role_required(['Skill Manager'])
def update_type_effectiveness(attack_type, defend_type):
    """타입 효과 수정"""
    
    # 요청 데이터 받기
    data = request.get_json()
    new_effectiveness = data.get('effectiveness', None)
    
    # 해당 타입 효과를 찾기
    effectiveness = TypeEffectiveness.query.filter_by(attack=attack_type, defend=defend_type).first()
    
    if not effectiveness:
        return jsonify({"error": "Type effectiveness not found"}), 404
    
    # 수정할 값이 제공되었으면 해당 타입 효과를 업데이트
    if new_effectiveness is not None:
        effectiveness.effectiveness = new_effectiveness
    
    try:
        # 데이터베이스 세션 커밋
        db.session.commit()
        return jsonify({
            'attack': effectiveness.attack,
            'defend': effectiveness.defend,
            'effectiveness': effectiveness.effectiveness
        })
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update type effectiveness"}), 500



# --- Trainer API ---
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    name = data.get('name')
    password = data.get('password')

    if not name or not password:
        return jsonify({"error": "Name and password are required"}), 400

    # Check if name already exists
    existing_trainer = Trainer.query.filter_by(name=name).first()
    if existing_trainer:
        return jsonify({"error": "Trainer with this name already exists"}), 400

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create new Trainer
    new_trainer = Trainer(name=name, badges=0, role="Trainer", password=hashed_password)
    db.session.add(new_trainer)
    db.session.commit()


    # Randomly select a Pokemon from PokeDex
    pokedex_entry = db.session.query(PokeDex).order_by(func.random()).first()
    if not pokedex_entry:
        return jsonify({"error": "No Pokemon available in the PokeDex"}), 400

    # Calculate max_hp
    max_hp = ((2 * pokedex_entry.hp_stat + 100) * 5) / 100 + 10  # Level 5

    # Add Pokemon to the new trainer
    new_pokemon = Pokemon(
        pokedex_id=pokedex_entry.id,
        name=pokedex_entry.name,
        level=5,
        hp=max_hp,
        experience=0,
        trainer_id=new_trainer.id
    )
    db.session.add(new_pokemon)
    db.session.commit()  # Commit to get the new pokemon's ID

    # Assign Moves to the new Pokemon
    moves = []
    if pokedex_entry.type1:
        type1_moves = db.session.query(Move).filter_by(type=pokedex_entry.type1.lower()).all()
        if type1_moves:
            moves.append(random.choice(type1_moves))  # Random move for type1

    if pokedex_entry.type2:  # If type2 exists
        type2_moves = db.session.query(Move).filter_by(type=pokedex_entry.type2.lower()).all()
        if type2_moves:
            moves.append(random.choice(type2_moves))  # Random move for type2

    # Add the moves to PokemonMoves
    for move in moves:
        new_pokemon_move = PokemonMove(
            pokemon_id=new_pokemon.id,
            move_id=move.id,
            remaining_uses=move.pp  # Set to the move's max PP
        )
        db.session.add(new_pokemon_move)

    # Final Commit
    db.session.commit()

    return jsonify({
        "message": "Trainer registered successfully",
        "trainer": {
            "id": new_trainer.id,
            "name": new_trainer.name,
            "role": new_trainer.role
        },
        "pokemon": {
            "id": new_pokemon.id,
            "name": new_pokemon.name,
            "level": new_pokemon.level,
            "hp": new_pokemon.hp,
            "experience": new_pokemon.experience,
            "moves": [{"id": move.id, "name": move.name, "type": move.type} for move in moves]
        }
    }), 201


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        name = data.get('name')
        password = data.get('password')

        if not name or not password:
            return jsonify({"error": "Name and password are required"}), 400

        # Check if trainer exists
        trainer = Trainer.query.filter_by(name=name).first()
        if not trainer:
            return jsonify({"error": "Invalid name or password"}), 401

        # Verify the password
        if not bcrypt.check_password_hash(trainer.password, password):
            return jsonify({"error": "Invalid name or password"}), 401
        
        global current_role
        current_role = trainer.role

        return jsonify({"message": "Login successful", "trainer_id": trainer.id}), 200
    
    except Exception as e:
        db.session.rollback()
        error_trace = traceback.format_exc()
        return jsonify({"error": str(e), "trace": error_trace}), 500



@app.route('/trainers/<int:id>', methods=['GET'])
def get_trainer(id):
    """특정 트레이너 조회"""
    trainer = Trainer.query.get(id)
    if not trainer:
        return jsonify({'error': 'Trainer not found'}), 404
    return jsonify({
        'id': trainer.id,
        'name': trainer.name,
        'badges': trainer.badges,
        'role': trainer.role,
        'created_at': trainer.created_at
    })






# --- Pokemon API ---
@app.route('/trainers/<int:trainer_id>/pokemon', methods=['GET'])
def get_pokemon_by_trainer(trainer_id):
    """특정 트레이너의 포켓몬 조회 + PokeDex 정보 포함"""
    try:
        pokemon = db.session.query(
            Pokemon.id,
            Pokemon.pokedex_id, 
            Pokemon.name, 
            Pokemon.level, 
            Pokemon.experience, 
            Pokemon.hp, 
            Pokemon.trainer_id, 
            Pokemon.created_at,
            PokeDex.name.label("pokedex_name"), 
            PokeDex.type1, 
            PokeDex.type2, 
            PokeDex.hp_stat, 
            PokeDex.att, 
            PokeDex.def_stat, 
            PokeDex.spd,
            PokeDex.front_img,
            PokeDex.back_img
        ).join(PokeDex, Pokemon.pokedex_id == PokeDex.id).filter(Pokemon.trainer_id == trainer_id).all()

        if not pokemon:
            return jsonify({"error": "No Pokemon found for the given trainer"}), 404

        return jsonify([{
            'id': p.id,
            'pokedex_id': p.pokedex_id,
            'name': p.name, #이름 바꿀 수 있는지, 없는 게 나을 듯
            'level': p.level,
            'experience': p.experience,
            'hp': p.hp,
            'type1': p.type1,
            'type2': p.type2,
            'hp_stat': p.hp_stat,
            'att': p.att,
            'def': p.def_stat,
            'spd': p.spd,
            'trainer_id': p.trainer_id,
            'front_img_url':p.front_img,
            'back_img_url':p.back_img,
            'created_at': p.created_at,
        } for p in pokemon])
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/pokemon', methods=['POST'])
def add_pokemon():
    """새 포켓몬 추가"""
    data = request.json
    pokemon = Pokemon(
        pokemon_id=data['pokemon_id'],
        name=data['name'],
        level=data.get('level', 1),
        experience=data.get('experience', 0),
        hp=data['hp'],
        trainer_id=data['trainer_id']
    )
    db.session.add(pokemon)
    db.session.commit()
    return jsonify({'message': 'Pokemon added successfully', 'id': pokemon.id}), 201

@app.route('/pokemon/<int:pokemon_id>', methods=['DELETE'])
def delete_pokemon(pokemon_id):
    try:
        # 해당 Pokemon ID로 포켓몬 검색
        pokemon = Pokemon.query.filter_by(id=pokemon_id).first()

        # 포켓몬이 없을 경우
        if not pokemon:
            return jsonify({"error": "Pokemon not found"}), 404

        # 포켓몬 삭제
        db.session.delete(pokemon)
        db.session.commit()

        return jsonify({"message": f"Pokemon with ID {pokemon_id} has been deleted successfully."}), 200

    except Exception as e:
        db.session.rollback()
        error_trace = traceback.format_exc()
        return jsonify({"error": str(e), "trace": error_trace}), 500


@app.route('/pokemon/<int:id>', methods=['GET'])
def get_pokemon_by_id(id):
    """특정 포켓몬 조회"""
    pokemon = Pokemon.query.get(id)
    if not pokemon:
        return jsonify({'error': 'Pokemon not found'}), 404
    return jsonify({
        'id': pokemon.id,
        'pokemon_id': pokemon.pokemon_id,
        'name': pokemon.name,
        'level': pokemon.level,
        'experience': pokemon.experience,
        'hp': pokemon.hp,
        'trainer_id': pokemon.trainer_id,
        'created_at': pokemon.created_at
    })

# @app.route('/pokemon/<int:id>', methods=['PUT'])
# def update_pokemon(id):
#     """특정 포켓몬 정보 업데이트"""
#     data = request.json
#     pokemon = Pokemon.query.get(id)
#     if not pokemon:
#         return jsonify({'error': 'Pokemon not found'}), 404

#     pokemon.name = data.get('name', pokemon.name)
#     pokemon.level = data.get('level', pokemon.level)
#     pokemon.experience = data.get('experience', pokemon.experience)
#     pokemon.hp = data.get('hp', pokemon.hp)
#     pokemon.trainer_id = data.get('trainer_id', pokemon.trainer_id)
#     db.session.commit()
#     return jsonify({'message': 'Pokemon updated successfully'})

# @app.route('/pokemon/<int:id>', methods=['DELETE'])
# def delete_pokemon(id):
#     """특정 포켓몬 삭제"""
#     pokemon = Pokemon.query.get(id)
#     if not pokemon:
#         return jsonify({'error': 'Pokemon not found'}), 404

#     db.session.delete(pokemon)
#     db.session.commit()
#     return jsonify({'message': 'Pokemon deleted successfully'})

@app.route('/wild-battle-record/trainers/<int:id>', methods=['GET'])
def get_wild_battle_record(id):
    """특정 트레이너의 야생 배틀 기록 조회"""
    records = WildBattleRecord.query.filter_by(trainer_id=id)
    if not records:
        return jsonify({'message': "You don't have any records"}), 404
    return jsonify([
        {
            "name": record.pokemon_name,
            "level": record.pokemon_level,
            "result": record.result,
            "created_at": record.created_at
        }
        for record in records
    ])

@app.route('/gym-battle-record/trainers/<int:id>', methods=['GET'])
def get_gym_battle_record(id):
    """특정 트레이너의 관장 배틀 기록 조회"""
    records = GymBattleRecord.query.filter_by(trainer_id=id)
    if not records:
        return jsonify({'message': "You don't have any records"}), 404
    return jsonify([
        {
            "name": record.gym_leader_name,
            "badges": record.gym_leader_badges,
            "result": record.result,
            "created_at": record.created_at
        }
        for record in records
    ])


@app.route('/trainers/<int:trainer_id>/pokemon/<int:pokemon_id>/moves', methods=['GET'])
def get_pokemon_moves(trainer_id, pokemon_id):
    """트레이너의 포켓몬 기술 조회"""
    try:
        pokemon = Pokemon.query.filter_by(id=pokemon_id, trainer_id=trainer_id).first()
        if not pokemon:
            return jsonify({"error": "Pokemon not found or not owned by this trainer"}), 404

        moves = db.session.query(
            PokemonMove.remaining_uses,
            Move.id.label("move_id"),
            Move.name,
            Move.type,
            Move.power,
            Move.pp,
            Move.accuracy
        ).join(Move, PokemonMove.move_id == Move.id).filter(PokemonMove.pokemon_id == pokemon_id).all()

        return jsonify([{
            "move_id": m.move_id,
            "name": m.name,
            "type": m.type,
            "power": m.power,
            "remaining_uses": m.remaining_uses,
            "accuracy": m.accuracy
        } for m in moves])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
# 야생 포켓몬 Level 트레이너 뱃지 개수 따라서 다르게
@app.route('/wild-pokemon/trainer/<int:trainer_id>', methods=['GET'])
def get_wild_pokemon(trainer_id):
    """랜덤 야생 포켓몬 등장 + PokeDex 정보 포함"""
    try:
        # trainer_id가 0인 야생 포켓몬 조회
        wild_pokemons = db.session.query(
            Pokemon.id.label("pokemon_id"),
            Pokemon.name,
            Pokemon.level,
            Pokemon.experience,
            Pokemon.hp,
            Pokemon.trainer_id,
            Pokemon.created_at,
            PokeDex.id.label("pokedex_id"),
            PokeDex.name.label("pokedex_name"),
            PokeDex.type1,
            PokeDex.type2,
            PokeDex.hp_stat,
            PokeDex.att,
            PokeDex.def_stat,
            PokeDex.spd,
            PokeDex.front_img,
            PokeDex.back_img,
        ).join(PokeDex, Pokemon.pokedex_id == PokeDex.id).filter(Pokemon.trainer_id == 0).all()

        if not wild_pokemons:
            return jsonify({"error": "No wild Pokemon available"}), 404

        # 랜덤으로 한 포켓몬 선택
        selected_pokemon = random.choice(wild_pokemons)
        
        trainer = Trainer.query.get(trainer_id)
        badges = trainer.badges
        
        if badges not in BADGE_LEVEL_RANGES:
            raise ValueError(f"Invalid badges value: {badges}")
        level_min, level_max = BADGE_LEVEL_RANGES[badges]
        
        random_level = random.randint(level_min, level_max)
        max_hp = ((2 * selected_pokemon.hp_stat + 100) * random_level) / 100 + 10  # Level 5
        
        return jsonify({
            'id': selected_pokemon.pokemon_id,
            'pokedex_id': selected_pokemon.pokedex_id,
            'name': selected_pokemon.name, 
            'level': random_level,
            'hp': max_hp,
            'front_img_url':selected_pokemon.front_img,
            'back_img_url':selected_pokemon.back_img,
            'created_at': selected_pokemon.created_at,
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        return jsonify({"error": str(e), "trace": error_trace}), 500      
    
      
    
# 레벨에 따라 hp 달라질 것 같음 -> pokemon 테이블에 hp_stat 둬야 할 것 같음
@app.route('/catch', methods=['POST'])
def catch_pokemon():
    """포획: hp 수준에 따라 포획 확률 계산"""
    try:
        data = request.json
        trainer_id = data['trainer_id']
        attacker = data['attacker']
        defender = data['defender']

        wild_pokemon_id = defender['id']
        wild_pokemon = Pokemon.query.get(wild_pokemon_id)
        if not wild_pokemon or wild_pokemon.trainer_id != 0:
            return jsonify({"error": "Wild Pokemon not found"}), 404
        

        wild_pokedex = PokeDex.query.get(wild_pokemon.pokedex_id)
        level = defender['level']
        remaining_hp = defender['hp']
        max_hp = ((2 * wild_pokedex.hp_stat + 100) * level) / 100 + 10

        # 포획 확률 계산
        capture_rate = max(1, (1 - (remaining_hp / max_hp)) * 100)
        success = random.randint(1, 100) <= capture_rate

        opponent_move = ""
        if success:
            # 포켓몬 소유권 업데이트
            
            owned_pokemon_count = Pokemon.query.filter_by(trainer_id=trainer_id).count()

            if owned_pokemon_count >= 6:
                return jsonify({"caught": -1, "message": "You already have 6 Pokemon. You can't catch more!"})
    
            new_pokemon = Pokemon(
                pokedex_id=wild_pokemon.pokedex_id,
                name=wild_pokemon.name,
                level=level,
                experience=0,
                hp=remaining_hp,
                trainer_id=trainer_id 
            )
            db.session.add(new_pokemon)
            db.session.commit()
            return jsonify({"caught":1, "message": "Pokemon caught successfully!"})
        
        else:
            moves = db.session.query(
                PokemonMove.remaining_uses,
                Move.id.label("move_id"),
                Move.name,
                Move.type,
                Move.power,
                Move.pp,
                Move.accuracy
            ).join(Move, PokemonMove.move_id == Move.id).filter(PokemonMove.pokemon_id == wild_pokemon_id, PokemonMove.remaining_uses > 0).all()

            if not moves:
                return jsonify({"error": "No available moves for this Pokemon"}), 400
            selected_move = random.choice(moves)
            opponent_move = selected_move.name
            
            attacker_pokedex = PokeDex.query.get(attacker['pokedex_id']) 
            defender_pokedex = PokeDex.query.get(defender['pokedex_id']) 
            
            # 데미지 계산
            effectiveness_type1 = db.session.query(TypeEffectiveness.effectiveness).filter_by(
                attack=selected_move.type, defend=attacker_pokedex.type1).scalar() or 1.0
            effectiveness_type2 = db.session.query(TypeEffectiveness.effectiveness).filter_by(
                attack=selected_move.type, defend=attacker_pokedex.type2).scalar() or 1.0
            
            

            damage = calculate_damage(defender_pokedex, attacker_pokedex, level, selected_move, effectiveness_type1, effectiveness_type2)
            print("opponent attack :", damage)
            
            # HP 업데이트
            attacker['hp'] = max(0, attacker['hp'] - damage)
            
            db.session.query(PokemonMove).filter_by(pokemon_id=defender['id'], move_id=selected_move.move_id).update({"remaining_uses": selected_move.remaining_uses-1})
            
            return jsonify({
                # 한 턴이 끝날때마다 남은
                "caught": 0,
                "attacker": {
                    "id": attacker['id'],
                    "remaining_hp": attacker['hp']
                },
                "defender_move": {
                    "move_name": opponent_move
                }
            })

    except Exception as e:
        error_trace = traceback.format_exc()
        return jsonify({"error": str(e), "trace": error_trace}), 500    


def calculate_damage(attacker, defender, level, move, effectiveness_type1, effectiveness_type2):
    """데미지 계산"""
    # 공식의 요소들
    Level = level
    Critical = random.choice([1, 1.5])  # 1 또는 1.5
    Power = move.power
    A = attacker.att
    D = defender.def_stat
    STAB = 1.5 if move.type in [attacker.type1, attacker.type2] else 1
    type1 = effectiveness_type1
    type2 = effectiveness_type2
    random_factor = random.uniform(0.85, 1.0)  # 0.85 ~ 1.0 사이의 랜덤 값

    # 데미지 공식
    damage = (((2 * Level * Critical / 5 + 2) * Power * (A / D)) / 50 + 2) * STAB * type1 * type2 * random_factor
    return int(damage)


@app.route('/battle/trainer/<int:trainer_id>', methods=['GET'])
def battle_start(trainer_id):
    """뱃지 개수에 따라 관장 차례대로 나옴"""
    try:
        trainer = Trainer.query.filter_by(id=trainer_id).first()
        my_badges = trainer.badges
        
        if my_badges <= 7:
            opponent = Trainer.query.filter_by(role="Gym Leader", badges=my_badges+1).first()
        else: # elite_four
            opponents = (
                Trainer.query
                .filter_by(role="Elite Four")
                .order_by(Trainer.id)  # trainer_id 순서로 정렬
                .all()
            )
            # 마지막까지 해치우면 마지막 엘리트 4만 마주침
            if my_badges - 8 >= 4:
                my_badges = 11
            opponent = opponents[my_badges-8]  # 리스트의 첫 번째 트레이너 선택
            
        opponent_pokemons = db.session.query(
            Pokemon.id.label("pokemon_id"),
            Pokemon.name,
            Pokemon.level,
            Pokemon.experience,
            Pokemon.hp,
            Pokemon.trainer_id,
            Pokemon.created_at,
            PokeDex.id.label("pokedex_id"),
            PokeDex.name.label("pokedex_name"),
            PokeDex.type1,
            PokeDex.type2,
            PokeDex.hp_stat,
            PokeDex.att,
            PokeDex.def_stat,
            PokeDex.spd,
            PokeDex.front_img,
            PokeDex.back_img,
        ).join(PokeDex, Pokemon.pokedex_id == PokeDex.id).filter(Pokemon.trainer_id == opponent.id).all()
        
        # 포켓몬 데이터 변환
        result = []
        for pokemon in opponent_pokemons:
            result.append({
                'id': pokemon.pokemon_id,
                'pokedex_id': pokemon.pokedex_id,
                'name': pokemon.name,
                'level': pokemon.level,
                'hp': pokemon.hp,
                'front_img_url': pokemon.front_img,
                'back_img_url': pokemon.back_img,
                'created_at': pokemon.created_at
            })
        # 응답 데이터 생성
        opponent = {
            "id": opponent.id,
            "name": opponent.name,
            "badges": opponent.badges,
            "total_pokemon": len(result),
        }
        response = {
            "opponent": opponent,
            "pokemons": result
        }

        # 결과 반환
        return jsonify(response), 200
        
    except Exception as e:
        db.session.rollback()
        error_trace = traceback.format_exc()
        return jsonify({"error": str(e), "trace": error_trace}), 500      


@app.route('/battle/skill-use', methods=['POST'])
def use_skill():
    """스킬 사용"""
    try:
        data = request.json # 가변적인 값들은 따로 받는다.
        attacker = data['attacker'] # id, pokedex_id, level, hp
        pokemon_move = data['pokemon_move'] # move_id, pokemon_id, r_u -> 스킬 사용한 포켓몬의 스킬 정보
        defender = data['defender'] # id, pokedex_id, level, hp
        
        move = Move.query.get(pokemon_move['move_id'])
        attacker_pokedex = PokeDex.query.get(attacker['pokedex_id']) 
        defender_pokedex = PokeDex.query.get(defender['pokedex_id']) 
        
        
        if not attacker_pokedex or not attacker_pokedex:
            return jsonify({"error": "Pokemon not found"}), 404
        if not move:
            return jsonify({"error": "Move not found"}), 404
        
        
        # 데미지 계산
        effectiveness_type1 = db.session.query(TypeEffectiveness.effectiveness).filter_by(
            attack=move.type, defend=defender_pokedex.type1).scalar() or 1.0
        effectiveness_type2 = db.session.query(TypeEffectiveness.effectiveness).filter_by(
            attack=move.type, defend=defender_pokedex.type2).scalar() or 1.0

        damage = calculate_damage(attacker_pokedex, defender_pokedex, attacker['level'], move, effectiveness_type1, effectiveness_type2)
        print("attack: ", damage)

        # HP 업데이트
        defender['hp'] = max(0, defender['hp'] - damage)
        pokemon_move['remaining_uses'] -= 1
        
        
        opponent_move = ""
        # 상대방의 hp가 0이 아니면 나도 해당 포켓몬의 랜덤 스킬로 공격받는다
        if defender['hp'] != 0:
            
            moves = db.session.query(
                PokemonMove.remaining_uses,
                Move.id.label("move_id"),
                Move.name,
                Move.type,
                Move.power,
                Move.pp,
                Move.accuracy
            ).join(Move, PokemonMove.move_id == Move.id).filter(PokemonMove.pokemon_id == defender['id'], PokemonMove.remaining_uses > 0).all()

            if not moves:
                return jsonify({"error": "No available moves for this Pokemon"}), 400
            selected_move = random.choice(moves)
            opponent_move = selected_move.name
            
            
            # 데미지 계산
            effectiveness_type1 = db.session.query(TypeEffectiveness.effectiveness).filter_by(
                attack=selected_move.type, defend=attacker_pokedex.type1).scalar() or 1.0
            effectiveness_type2 = db.session.query(TypeEffectiveness.effectiveness).filter_by(
                attack=selected_move.type, defend=attacker_pokedex.type2).scalar() or 1.0

            damage = calculate_damage(defender_pokedex, attacker_pokedex, defender['level'], selected_move, effectiveness_type1, effectiveness_type2)
            print("opponent attack :", damage)
            
            # HP 업데이트
            attacker['hp'] = max(0, attacker['hp'] - damage)
            
            db.session.query(PokemonMove).filter_by(pokemon_id=defender['id'], move_id=selected_move.move_id).update({"remaining_uses": selected_move.remaining_uses-1})
            # 변경사항 커밋
            db.session.commit()
                    
        
        return jsonify({
            # 한 턴이 끝날때마다 남은
            "attacker": {
                "id": attacker['id'],
                "remaining_hp": attacker['hp']
            },
            "defender": {
                "id": defender['id'],
                "remaining_hp": defender['hp'],
            },
            "attacker_move": {
                "move_id": pokemon_move['move_id'],
                "pokemon_id": pokemon_move['pokemon_id'],
                "remaining_uses": pokemon_move['remaining_uses']
            },
            "defender_move": {
                "move_name": opponent_move
            }
        })
    except Exception as e:
        db.session.rollback()
        error_trace = traceback.format_exc()
        return jsonify({"error": str(e), "trace": error_trace}), 500        


@app.route('/battle/update', methods=['POST'])
def update_battle_results():
    """관장 배틀 종료 후 포켓몬 HP, exp, level, 스킬 remaining_uses 업데이트"""
    try:
        # 클라이언트로부터 받은 데이터
        data = request.json

        # 1. 포켓몬 업데이트
        pokemon_updates = data.get('pokemons')  # 포켓몬 HP 업데이트 정보
        if pokemon_updates:
            for pokemon in pokemon_updates:
                pokemon_entry = Pokemon.query.get(pokemon['id'])
                pokedex_entry = PokeDex.query.get(pokemon_entry.pokedex_id)
                
                new_exp = pokemon_entry.experience + 20
                new_level = pokemon_entry.level
                level_up_exp = pokemon_entry.level * (pokedex_entry.att + pokedex_entry.def_stat + pokedex_entry.spd + pokedex_entry.hp_stat)
                if level_up_exp < pokemon_entry.experience + 20: 
                    new_level += 1
                    new_exp = (pokemon_entry.experience + 20) - level_up_exp
                
                db.session.query(Pokemon).filter_by(id=pokemon['id']).update({
                    "hp": pokemon['remaining_hp'],
                    "experience": new_exp,
                    "level": new_level
                })
                

        # 2. 스킬 remaining_uses 업데이트
        skill_updates = data.get('skills')  # 스킬 remaining_uses 업데이트 정보
        if skill_updates:
            for skill in skill_updates:
                db.session.query(PokemonMove).filter_by(
                    pokemon_id=skill['pokemon_id'],
                    move_id=skill['move_id']
                ).update({
                    "remaining_uses": skill['remaining_uses']
                })
        
        # 상대 트레이너 포켓몬들 기술 횟수 풀로 채우기
        trainer_id = data.get('trainer_id')
        opponent_id = data.get('opponent_id')
        won = data.get('won')
        
        pokemons = Pokemon.query.filter_by(trainer_id = opponent_id).all()
        pokemon_moves = db.session.query(
            PokemonMove.pokemon_id,
            PokemonMove.move_id,
            PokemonMove.remaining_uses,
            Move.pp.label("max_pp")
        ).join(
            Move, PokemonMove.move_id == Move.id
        ).filter(
            PokemonMove.pokemon_id.in_([pokemon.id for pokemon in pokemons])
        ).all()
        
        moves_by_pokemon = defaultdict(list)
        for move in pokemon_moves:
            moves_by_pokemon[move.pokemon_id].append(move)

        for pokemon in pokemons:
            # 스킬 remaining_uses 갱신
            for move in moves_by_pokemon[pokemon.id]:
                db.session.query(PokemonMove).filter_by(
                    pokemon_id=move.pokemon_id,
                    move_id=move.move_id
                ).update({"remaining_uses": move.max_pp})
        
        if won:
            badges = Trainer.query.get(trainer_id).badges
            db.session.query(Trainer).filter_by(id=trainer_id).update({
                "badges": badges + 1,
            })
        
        
        # record 기록
        opponent = Trainer.query.get(opponent_id)
        new_record = GymBattleRecord(
            trainer_id=trainer_id,
            gym_leader_id=opponent_id,
            gym_leader_name=opponent.name,
            gym_leader_badges=opponent.gym_leader_badges,
            result= "WIN" if won else "LOSE"
        )
        db.session.add(new_record)
        
       
        # 변경 사항 커밋
        db.session.commit()
        return jsonify({"message": "Battle results updated successfully"}), 200

    except Exception as e:
        error_trace = traceback.format_exc()
        return jsonify({"error": str(e), "trace": error_trace}), 500


@app.route('/wild-battle/update', methods=['POST'])
def update_wild_battle_results():
    """배틀 종료 후 포켓몬 HP, exp, level, 스킬 remaining_uses 업데이트"""
    try:
        # 클라이언트로부터 받은 데이터
        data = request.json

        # 1. 포켓몬 업데이트
        pokemon_updates = data.get('pokemons')  # 포켓몬 HP 업데이트 정보
        if pokemon_updates:
            for pokemon in pokemon_updates:
                pokemon_entry = Pokemon.query.get(pokemon['id'])
                pokedex_entry = PokeDex.query.get(pokemon_entry.pokedex_id)
                
                new_exp = pokemon_entry.experience + 20
                new_level = pokemon_entry.level
                level_up_exp = pokemon_entry.level * (pokedex_entry.att + pokedex_entry.def_stat + pokedex_entry.spd + pokedex_entry.hp_stat)
                if level_up_exp < pokemon_entry.experience + 20: 
                    new_level += 1
                    new_exp = (pokemon_entry.experience + 20) - level_up_exp
                
                db.session.query(Pokemon).filter_by(id=pokemon['id']).update({
                    "hp": pokemon['remaining_hp'],
                    "experience": new_exp,
                    "level": new_level
                })
                

        # 2. 스킬 remaining_uses 업데이트
        skill_updates = data.get('skills')  # 스킬 remaining_uses 업데이트 정보
        if skill_updates:
            for skill in skill_updates:
                db.session.query(PokemonMove).filter_by(
                    pokemon_id=skill['pokemon_id'],
                    move_id=skill['move_id']
                ).update({
                    "remaining_uses": skill['remaining_uses']
                })
        
        # 상대 트레이너 포켓몬들 기술 횟수 풀로 채우기
        trainer_id = data.get('trainer_id')
        pokemon = data.get('pokemon')
        result = data.get('result')
        
        new_record = WildBattleRecord(
            trainer_id=trainer_id,
            pokemon_name=pokemon['name'],
            pokemon_level=pokemon['level'],
            result=result
        )
        db.session.add(new_record)
            
        # 변경 사항 커밋
        db.session.commit()
        return jsonify({"message": "Battle results updated successfully"}), 200

    except Exception as e:
        error_trace = traceback.format_exc()
        return jsonify({"error": str(e), "trace": error_trace}), 500     
     


@app.route('/trainers/<int:trainer_id>/heal', methods=['GET'])
def heal_pokemon(trainer_id):
    """모든 포켓몬의 HP 회복"""
    try:
        # 1. Pokemon과 PokeDex를 조인하여 모든 포켓몬의 현재 레벨과 스탯 가져오기
        pokemons = db.session.query(
            Pokemon.id,
            Pokemon.level,
            Pokemon.hp,
            PokeDex.hp_stat
        ).join(
            PokeDex, Pokemon.pokedex_id == PokeDex.id
        ).filter(Pokemon.trainer_id == trainer_id).all()

        # 2. PokemonMove와 Move를 조인하여 모든 스킬 데이터 가져오기
        pokemon_moves = db.session.query(
            PokemonMove.pokemon_id,
            PokemonMove.move_id,
            PokemonMove.remaining_uses,
            Move.pp.label("max_pp")
        ).join(
            Move, PokemonMove.move_id == Move.id
        ).filter(
            PokemonMove.pokemon_id.in_([pokemon.id for pokemon in pokemons])
        ).all()

        # 3. HP 및 remaining_uses 업데이트
        # 포켓몬 별로 그룹화
        moves_by_pokemon = defaultdict(list)
        for move in pokemon_moves:
            moves_by_pokemon[move.pokemon_id].append(move)

        # 업데이트 수행
        for pokemon in pokemons:
            # HP 계산
            max_hp = ((2 * pokemon.hp_stat + 100) * pokemon.level) / 100 + 10
            db.session.query(Pokemon).filter_by(id=pokemon.id).update({"hp": max_hp})

            # 스킬 remaining_uses 갱신
            for move in moves_by_pokemon[pokemon.id]:
                db.session.query(PokemonMove).filter_by(
                    pokemon_id=move.pokemon_id,
                    move_id=move.move_id
                ).update({"remaining_uses": move.max_pp})

        
        # 변경 사항 커밋
        db.session.commit()

        return jsonify({"message": "All Pokemon HP and skills healed successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
        
        
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
