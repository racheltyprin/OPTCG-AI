import json
import glob
import sys
import os

def consolidate():
    # create empty json array
    json_files = glob.glob(os.path.join(PACKS_DIR, '*.json'))
    combined_data = []

    #read ea. json file associate w ea. card
    for file in json_files:
        if os.path.basename(file) == "packs.json":
            continue  # skip pack metadata file
        with open(file, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                combined_data.extend(data)
            else:
                combined_data.append(data)

    #write to combined.json file array
    with open(CARD_LIST_FILE, 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print("Consolidation complete")

def reset():
    #resets combined_data file for testing
    combined_data=[]
    with open(CARD_LIST_FILE, 'w') as f:
        json.dump(combined_data, f, indent=2)

def extra_consolidate():
    EXTRA_CONSOLIDATED_CARD_LIST = os.path.join(DATA_DIR, 'consolidated.json')
    counter = 0
    combined_data=[]
    with open(CARD_LIST_FILE, 'r') as f:
        cardList = json.load(f)
    for card in (cardList):
        counter += 1
        if (len(card.get("id"))<=8):
            combined_data.append(card)

    with open(EXTRA_CONSOLIDATED_CARD_LIST, 'w') as f:
        json.dump(combined_data, f, indent=2)

    print("Consolidation complete")

if __name__ == "__main__":
    #directories
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    PACKS_DIR = os.path.join(DATA_DIR, 'packs/json')
    CARD_LIST_FILE = os.path.join(DATA_DIR, 'combined.json')
    if len(sys.argv) > 1:
        if sys.argv[1] == "consolidate":
            consolidate()
        elif sys.argv[1] == "reset":
            reset()
        elif sys.argv[1]== "extra_consolidate":
            extra_consolidate()
        else:
            print("Unknown command. Use 'consolidate' or 'reset'")
    else:
        print("Usage: python script.py [consolidate|reset]")