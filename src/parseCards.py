import json
import os
from pathlib import Path
import re
import sys

#combined.json filepaths:
PARENT_DIRECTORY= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNCONSOLIDATED_CARD_LIST_FILE = os.path.join(PARENT_DIRECTORY, "data/combined.json")
CONSOLIDATED_CARD_LIST_FILE = os.path.join(PARENT_DIRECTORY, "data/consolidated.json")

#trackers
timing = []


#goes through each card in combined.json and consolidated.json, counts amounts, finds difference
def card_counter():
    #load unconsolidated cardlist
    with open(UNCONSOLIDATED_CARD_LIST_FILE, 'r') as f:
        cardList = json.load(f)
    unconsolidatedCounter = 0
    for card in cardList:
        unconsolidatedCounter +=1
    
    #load consolidated cardlist
    with open(CONSOLIDATED_CARD_LIST_FILE, 'r') as f:
        cardList = json.load(f)
    consolidatedCounter = 0
    for card in cardList:
        consolidatedCounter +=1

    print("unconsolidated amount =",unconsolidatedCounter,"; consolidated amount =",consolidatedCounter)
    print(unconsolidatedCounter-consolidatedCounter)

#go through each card
def parse_cards(listType):
    cardList = []
    if listType == "unconsolidated":
        with open(UNCONSOLIDATED_CARD_LIST_FILE, 'r') as f:
            cardList = json.load(f)
    else:
        with open(CONSOLIDATED_CARD_LIST_FILE, 'r') as f:
            cardList = json.load(f)
    
    for card in cardList:
        (parse_timing(card.get("effect")))
    timing_counter()


def timing_counter():
    timingDict = {}
    newTimingDict = {}
    for item in timing:
        if item not in timingDict:
            timingDict[item]=1
        else:
            timingDict.update({item: (1+timingDict.get(item))}) 
    for key in timingDict:
        if timingDict.get(key) >= 2:
            newTimingDict[key]=timingDict.get(key)
    print(newTimingDict)
            

 
    


#goes through each card and figures out when the effect occurs
def parse_timing(effectText):
    if not effectText or effectText.strip() == "-":
        return ["none"], ""
    timings = re.findall(r'\[(.*?)\]', effectText)
    if not timings:
        return ["immediate"], effectText
    # Remove timing brackets from text
    cleaned_text = re.sub(r'\[.*?\]', '', effectText).strip()
    for t in timings:
        
        if (t.lower().replace(" ", "_")) not in timing:
            timing.append(t)
    return [t.lower().replace(" ", "_") for t in timings], cleaned_text

    


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "parse_cards":
            if len(sys.argv)>2:
                parse_cards(sys.argv[2])
            else:
                parse_cards("consolidated")
        elif sys.argv[1] == "parse_timing":
            parse_timing()
        elif sys.argv[1] == "card_counter":
            card_counter()
        else:
            print("Unknown command. Use 'consolidate' or 'reset'")
    else:
        print("Usage: python script.py [consolidate|reset]")