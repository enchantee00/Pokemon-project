-- 1. Trainers 테이블
DROP TABLE IF EXISTS Trainers CASCADE;
CREATE TABLE Trainers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    badges INTEGER DEFAULT 0,
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. PokeDex 테이블
DROP TABLE IF EXISTS PokeDex CASCADE;
CREATE TABLE PokeDex (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type1 VARCHAR(50),
    type2 VARCHAR(50),
    hp_stat INTEGER NOT NULL,
    att INTEGER NOT NULL,
    def INTEGER NOT NULL,
    spd INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Moves 테이블
DROP TABLE IF EXISTS Moves CASCADE;
CREATE TABLE Moves (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50),
    damage INTEGER NOT NULL
);

-- 4. Pokemon 테이블
DROP TABLE IF EXISTS Pokemon CASCADE;
CREATE TABLE Pokemon (
    id SERIAL PRIMARY KEY,
    pokemon_id INTEGER NOT NULL REFERENCES PokeDex(id),
    name VARCHAR(255) NOT NULL,
    level INTEGER DEFAULT 1,
    experience INTEGER DEFAULT 0,
    hp INTEGER NOT NULL,
    trainer_id INTEGER REFERENCES Trainers(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. PokemonMoves 테이블
DROP TABLE IF EXISTS PokemonMoves CASCADE;
CREATE TABLE PokemonMoves (
    pokemon_id INTEGER NOT NULL REFERENCES Pokemon(id),
    move_id INTEGER NOT NULL REFERENCES Moves(id),
    remaining_uses INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (pokemon_id, move_id)
);

-- 6. WildBattleRecords 테이블
DROP TABLE IF EXISTS WildBattleRecords CASCADE;
CREATE TABLE WildBattleRecords (
    id SERIAL PRIMARY KEY,
    trainer_id INTEGER NOT NULL REFERENCES Trainers(id),
    pokemon_id INTEGER NOT NULL REFERENCES Pokemon(id),
    result VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. GymBattleRecords 테이블
DROP TABLE IF EXISTS GymBattleRecords CASCADE;
CREATE TABLE GymBattleRecords (
    id SERIAL PRIMARY KEY,
    trainer_id INTEGER NOT NULL REFERENCES Trainers(id),
    gym_leader_id INTEGER NOT NULL REFERENCES Trainers(id),
    result VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
