from werkzeug.security import generate_password_hash
from app import app, db
from models import Trainer
from datetime import datetime
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

# 비밀번호 해시화
hashed_password_poke = bcrypt.generate_password_hash("Pokemon Manager").decode('utf-8')
hashed_password_skill = bcrypt.generate_password_hash("Skill Manager").decode('utf-8')

# 애플리케이션 컨텍스트 내에서 작업을 수행
with app.app_context():  # 애플리케이션 컨텍스트를 열고
    # Pokemon Manager 역할의 사용자 추가
    pokemon_manager = Trainer(
        name="Pokemon Professor",  # 사용자의 이름을 변경
        role="Pokemon Manager",
        password=hashed_password_poke,  # 해시화된 비밀번호
        created_at=datetime.now()  # 생성 시간
    )

    # Skill Manager 역할의 사용자 추가
    skill_manager = Trainer(
        name="Skill Professor",  # 사용자의 이름을 변경
        role="Skill Manager",
        password=hashed_password_skill,  # 해시화된 비밀번호
        created_at=datetime.now()  # 생성 시간
    )

    # 트랜잭션 처리
    try:
        db.session.add(pokemon_manager)
        db.session.add(skill_manager)
        db.session.commit()  # 데이터베이스에 커밋
        print("Users added successfully")
    except Exception as e:
        db.session.rollback()  # 오류 발생 시 롤백
        print(f"Error occurred: {e}")
