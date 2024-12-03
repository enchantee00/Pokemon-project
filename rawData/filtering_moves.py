import json

input_file = "filtered_moves.json"
output_file = "filtered_moves_ndjson.json"

with open(input_file, "r") as infile, open(output_file, "w") as outfile:
    data = json.load(infile)  # Load the JSON array
    for obj in data:          # Write each object as a new line
        json.dump(obj, outfile)
        outfile.write("\n")

