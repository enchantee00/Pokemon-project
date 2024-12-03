ALTER TABLE Pokemon ALTER COLUMN hp DROP NOT NULL;

\copy Pokemon(pokemon_id, name, level, experience, trainer_id) FROM '../rawData/gymLeaders_eliteFour_pokemon.csv' DELIMITER ',' CSV HEADER;


UPDATE Pokemon
SET hp = FLOOR(((2 * pd.hp_stat + 100) * Pokemon.level) / 100) + 10
FROM PokeDex pd
WHERE Pokemon.pokemon_id = pd.id;

ALTER TABLE Pokemon ALTER COLUMN hp SET NOT NULL;

