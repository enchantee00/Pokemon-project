
from flask import Flask, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from models import db, Trainer, Pokemon, PokeDex, Move, PokemonMove,WildBattleRecord, GymBattleRecord, TypeEffectiveness
import random
import traceback
from collections import defaultdict
from sqlalchemy import text
from app import app



with app.app_context():
    try:
        # 1. PokeDex의 모든 포켓몬 가져오기
        pokedex_entries = PokeDex.query.all()

        for pokedex in pokedex_entries:
            # 2. Pokemon 테이블에 포켓몬 추가
            max_hp = ((2 * pokedex.hp_stat + 100) * 1) / 100 + 10  # Level 1로 기본 HP 계산
            new_pokemon = Pokemon(
                pokedex_id=pokedex.id,
                name=pokedex.name,
                level=1,
                experience=0,
                hp=1,
                trainer_id=0  # Trainer 없는 야생 포켓몬
            )
            db.session.add(new_pokemon)
            db.session.commit()  # Commit 후 Pokemon ID를 가져올 수 있음

            # Pokemon ID 가져오기
            pokemon_id = new_pokemon.id

            # 3. Moves 테이블에서 type1, type2에 맞는 스킬 가져오기
            moves = []
            
            if pokedex.type1:
                type1_moves = db.session.query(Move).filter_by(type=pokedex.type1.lower()).all()
                if type1_moves:
                    moves.append(random.choice(type1_moves))  # Random move for type1

            # type2와 매칭되는 Moves 가져오기 (type2가 있을 경우)
            if pokedex.type2:
                type2_moves = db.session.query(Move).filter_by(type=pokedex.type2.lower()).all()
                if type2_moves:
                    moves.append(random.choice(type2_moves))  # Random move for type2

            # 4. PokemonMoves 테이블에 추가
            for move in moves:
                new_pokemon_move = PokemonMove(
                    pokemon_id=pokemon_id,
                    move_id=move.id,
                    remaining_uses=move.pp  # Moves 테이블의 pp로 초기화
                )
                db.session.add(new_pokemon_move)

        # 최종 커밋
        db.session.commit()
        print("Wild Pokemon and their moves successfully populated.")

    except Exception as e:
        db.session.rollback()
        error_trace = traceback.format_exc()
        print({"error": str(e), "trace": error_trace})




