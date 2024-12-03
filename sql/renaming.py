import pandas as pd

# Define the file path
file_path = "../rawData/gymLeaders_eliteFour_pokemon_moveset.csv"

# Load the CSV file into a DataFrame
df = pd.read_csv(file_path)

# Convert the 'Move' column to lowercase
if 'Move' in df.columns:
    df['Move'] = df['Move'].str.lower()
else:
    print("Error: 'Move' column not found in the CSV file.")

# Save the updated DataFrame back to the CSV
df.to_csv(file_path, index=False)

print(f"All values in the 'Move' column have been converted to lowercase and saved to {file_path}.")
