CREATE TEMP TABLE TempMoves (
    data JSONB
);

-- Load the NDJSON data into the TempMoves table
\copy TempMoves(data) FROM '../rawData/filtered_moves_ndjson.json';

-- Insert the relevant data into the Moves table
INSERT INTO Moves (name, type, power, pp, accuracy)
SELECT 
    data->>'name' AS name,
    data->>'type' AS type,
    CASE 
        WHEN data->>'power' IS NULL THEN NULL
        ELSE (data->>'power')::INTEGER
    END AS power,
    CASE 
        WHEN data->>'pp' IS NULL THEN NULL
        ELSE (data->>'pp')::INTEGER
    END AS pp,
    CASE 
        WHEN data->>'accuracy' IS NULL THEN NULL
        ELSE (data->>'accuracy')::DOUBLE PRECISION
    END AS accuracy
FROM TempMoves;




