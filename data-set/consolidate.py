import json
import glob
import sys

def consolidate():
    # create empty json array
    json_files = glob.glob('packs/*.json')
    combined_data = []

    #read ea. json file associate w ea. card
    for file in json_files:
        with open(file, 'r') as f:
            data = json.load(f)
            combined_data.append(data)

    #write to combined.json file array
    with open('combined.json', 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print("Consolidation complete")

def reset():
    #resets combined_data file for testing
    combined_data=[]
    with open('combined.json', 'w') as f:
        json.dump(combined_data, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "consolidate":
            consolidate()
        elif sys.argv[1] == "reset":
            reset()
        else:
            print("Unknown command. Use 'consolidate' or 'reset'")
    else:
        print("Usage: python script.py [consolidate|reset]")