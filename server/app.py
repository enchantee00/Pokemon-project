from flask import Flask, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from flask_bcrypt import Bcrypt
from database_config import init_app, db
from models import Trainer, Pokemon, PokeDex, Move, PokemonMove,WildBattleRecord, GymBattleRecord, TypeEffectiveness
import random
import traceback
from collections import defaultdict
from sqlalchemy.sql import func



app = Flask(__name__)
init_app(app)
bcrypt = Bcrypt(app)


@app.errorhandler(404)
def not_found_error(e):
    """404 Not Found 처리"""
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_server_error(e):
    """500 Internal Server Error 처리"""
    return jsonify({"error": "An unexpected error occurred"}), 500


@app.route('/')
def home():
    return "Hello, World!"

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

    return jsonify({"message": "Login successful", "trainer_id": trainer.id}), 200



# --- Trainers API ---
@app.route('/trainers', methods=['GET'])
def get_trainers():
    """모든 트레이너 조회"""
    trainers = Trainer.query.all()
    return jsonify([{
        'id': trainer.id,
        'name': trainer.name,
        'badges': trainer.badges,
        'role': trainer.role,
        'created_at': trainer.created_at
    } for trainer in trainers])

# @app.route('/trainers', methods=['POST'])
# def add_trainer():
#     """새 트레이너 추가"""
#     data = request.json
#     trainer = Trainer(
#         name=data['name'],
#         badges=data.get('badges', 0),
#         role=data.get('role')
#     )
#     db.session.add(trainer)
#     db.session.commit()
#     return jsonify({'message': 'Trainer added successfully', 'id': trainer.id}), 201

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

# @app.route('/trainers/<int:id>', methods=['PUT'])
# def update_trainer(id):
#     """특정 트레이너 정보 업데이트"""
#     data = request.json
#     trainer = Trainer.query.get(id)
#     if not trainer:
#         return jsonify({'error': 'Trainer not found'}), 404

#     trainer.name = data.get('name', trainer.name)
#     trainer.badges = data.get('badges', trainer.badges)
#     trainer.role = data.get('role', trainer.role)
#     db.session.commit()
#     return jsonify({'message': 'Trainer updated successfully'})

# @app.route('/trainers/<int:id>', methods=['DELETE'])
# def delete_trainer(id):
#     """특정 트레이너 삭제"""
#     trainer = Trainer.query.get(id)
#     if not trainer:
#         return jsonify({'error': 'Trainer not found'}), 404

#     db.session.delete(trainer)
#     db.session.commit()
#     return jsonify({'message': 'Trainer deleted successfully'})

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
            PokeDex.spd
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
            'created_at': p.created_at,
        } for p in pokemon])
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# @app.route('/pokemon', methods=['POST'])
# def add_pokemon():
#     """새 포켓몬 추가"""
#     data = request.json
#     pokemon = Pokemon(
#         pokemon_id=data['pokemon_id'],
#         name=data['name'],
#         level=data.get('level', 1),
#         experience=data.get('experience', 0),
#         hp=data['hp'],
#         trainer_id=data['trainer_id']
#     )
#     db.session.add(pokemon)
#     db.session.commit()
#     return jsonify({'message': 'Pokemon added successfully', 'id': pokemon.id}), 201

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


# Pokedex에서 랜덤으로 뽑기, Level 뱃지따라서 다르게
@app.route('/wild-pokemon', methods=['GET'])
def get_wild_pokemon():
    """랜덤 야생 포켓몬 등장 + PokeDex 정보 포함"""
    try:
        # trainer_id가 0인 야생 포켓몬 조회
        wild_pokemon = db.session.query(
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
            PokeDex.spd
        ).join(PokeDex, Pokemon.pokedex_id == PokeDex.id).filter(Pokemon.trainer_id == 0).all()

        if not wild_pokemon:
            return jsonify({"error": "No wild Pokemon available"}), 404

        # 랜덤으로 한 포켓몬 선택
        selected_pokemon = random.choice(wild_pokemon)

        return jsonify({
            "pokemon": {
                "id": selected_pokemon.pokemon_id,
                "name": selected_pokemon.name,
                "level": selected_pokemon.level,
                "experience": selected_pokemon.experience,
                "hp": selected_pokemon.hp,
                "trainer_id": selected_pokemon.trainer_id,
                "created_at": selected_pokemon.created_at
            },
            "pokedex": {
                "id": selected_pokemon.pokedex_id,
                "name": selected_pokemon.pokedex_name,
                "type1": selected_pokemon.type1,
                "type2": selected_pokemon.type2,
                "hp_stat": selected_pokemon.hp_stat,
                "att": selected_pokemon.att,
                "def_stat": selected_pokemon.def_stat,
                "spd": selected_pokemon.spd
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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

        # HP 업데이트
        defender['hp'] = max(0, defender['hp'] - damage)
        pokemon_move['remaining_uses'] -= 1
        
        
        exp = None
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
            
            
            # 데미지 계산
            effectiveness_type1 = db.session.query(TypeEffectiveness.effectiveness).filter_by(
                attack=selected_move.type, defend=attacker_pokedex.type1).scalar() or 1.0
            effectiveness_type2 = db.session.query(TypeEffectiveness.effectiveness).filter_by(
                attack=selected_move.type, defend=attacker_pokedex.type2).scalar() or 1.0

            damage = calculate_damage(defender_pokedex, attacker_pokedex, defender['level'], selected_move, effectiveness_type1, effectiveness_type2)

            # HP 업데이트
            attacker['hp'] = max(0, attacker['hp'] - damage)
            # DB에서 해당 포켓몬의 hp 업데이트
            db.session.query(PokemonMove).filter_by(pokemon_id=defender['id'], move_id=selected_move.move_id).update({"remaining_uses": selected_move.remaining_uses-1})
            # 변경사항 커밋
            db.session.commit()
                        
        else: # 상대방 포켓몬 죽이면 경험치 준다
            exp = 10
        
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
                "move_name": selected_move.name
            }
        })
    except Exception as e:
        db.session.rollback()
        error_trace = traceback.format_exc()
        return jsonify({"error": str(e), "trace": error_trace}), 500        


@app.route('/battle/update', methods=['POST'])
def update_battle_results():
    """배틀 종료 후 포켓몬 HP와 스킬 remaining_uses 업데이트"""
    try:
        # 클라이언트로부터 받은 데이터
        data = request.json

        # 1. 포켓몬 업데이트
        pokemon_updates = data.get('pokemon')  # 포켓몬 HP 업데이트 정보
        if pokemon_updates:
            for pokemon in pokemon_updates:
                db.session.query(Pokemon).filter_by(id=pokemon['id']).update({
                    "hp": pokemon['remaining_hp']
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

        # 변경 사항 커밋
        db.session.commit()
        return jsonify({"message": "Battle results updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


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
        

# 레벨에 따라 hp 달라질 것 같음 -> pokemon 테이블에 hp_stat 둬야 할 것 같음
@app.route('/catch/<int:wild_pokemon_id>', methods=['POST'])
def catch_pokemon(wild_pokemon_id):
    """포획: hp 수준에 따라 포획 확률 계산"""
    try:
        wild_pokemon = Pokemon.query.get(wild_pokemon_id)
        if not wild_pokemon or wild_pokemon.trainer_id != 0:
            return jsonify({"error": "Wild Pokemon not found"}), 404

        # 포획 확률 계산
        capture_rate = max(1, (1 - (wild_pokemon.hp / 100)) * 100)
        success = random.randint(1, 100) <= capture_rate

        if success:
            # 포켓몬 소유권 업데이트
            data = request.json
            trainer_id = data['trainer_id']
            wild_pokemon.trainer_id = trainer_id
            db.session.commit()
            return jsonify({"message": "Pokemon caught successfully!"})
        else:
            return jsonify({"message": "Pokemon escaped!"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
