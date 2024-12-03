CREATE TEMP TABLE TempPokemonData (
    GymLeaderName TEXT,
    Pokemon TEXT,
    Move TEXT,
    Pokemon_id INTEGER
);

\copy TempPokemonData(GymLeaderName, Pokemon, Move, Pokemon_id) FROM '../rawData/gymLeaders_eliteFour_pokemon_moveset.csv' DELIMITER ',' CSV HEADER;

INSERT INTO PokemonMoves (pokemon_id, move_id, remaining_uses, created_at)
SELECT 
    TempPokemonData.Pokemon_id, 
    Moves.id AS move_id, 
    Moves.pp AS remaining_uses, -- Use the pp column as remaining_uses
    NOW() AS created_at
FROM 
    TempPokemonData
JOIN 
    Moves ON Moves.name = TempPokemonData.Move; -- Match move name in TempPokemonData with name in Moves

DROP TABLE TempPokemonData;
