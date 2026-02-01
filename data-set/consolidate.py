import json
import glob

json_files = glob.glob('json/*.json')
combined_data = []

for file in json_files:
    with open(file, 'r') as f:
        data = json.load(f)
        combined_data.append(data)

with open('combined.json', 'w') as f:
    json.dump(combined_data, f, indent=2)