CREATE TEMP TABLE TempPokeDex (
    id INTEGER,
    name VARCHAR(255),
    form VARCHAR(255),
    type1 VARCHAR(50),
    type2 VARCHAR(50),
    total INTEGER,
    hp INTEGER,
    attack INTEGER,
    defense INTEGER,
    sp_atk INTEGER,
    sp_def INTEGER,
    speed INTEGER,
    generation INTEGER
);

\copy TempPokeDex (id, name, form, type1, type2, total, hp, attack, defense, sp_atk, sp_def, speed, generation) FROM '/home/ec2-user/rawData/gen01.csv' DELIMITER ',' CSV HEADER;

INSERT INTO PokeDex (id, name, type1, type2, hp_stat, att, def, spd)
SELECT id, name, type1, type2, hp, attack, defense, speed
FROM TempPokeDex;

SELECT * FROM PokeDex;



