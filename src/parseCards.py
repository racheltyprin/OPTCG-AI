import copy
import json
import os
from pathlib import Path
import re
import sys

#combined.json filepaths:
PARENT_DIRECTORY= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNCONSOLIDATED_CARD_LIST_FILE = os.path.join(PARENT_DIRECTORY, "data/combined.json")
CONSOLIDATED_CARD_LIST_FILE = os.path.join(PARENT_DIRECTORY, "data/consolidated.json")
TIMING_FLAGS = {
  "on_play": 0,
  "activate_main": 0,
  "main": 0,
  "counter": 0,
  "when_attacking": 0,
  "on_ko": 0,
  "on_block": 0,
  "end_turn": 0,
  "opponent_turn": 0,
  "end_opponent_turn": 0
}
KEYWORD_FLAGS = {
  "rush": 0,
  "blocker": 0,
  "double_attack": 0,
  "banish": 0,
  "trigger": 0,
  "rush_character": 0,
  "unblockable": 0
}
EFFECT_ACTION_FLAGS = {
  "power_change": 0,
  "cost_change": 0,
  "ko": 0,
  "draw": 0,
  "search": 0,
  "rest": 0,
  "unrest": 0,
  "bounce": 0,
  "bottom_deck": 0,
  "trash": 0,
  "don_attach": 0,
  "don_remove": 0,
  "life_add": 0,
  "life_remove": 0,
  "don_add": 0,
  "don_remove": 0
}
CONDITIONS = {
  "don_times": 0, # of don required>,
  "don_minus": 0, # of don required>,
  "don_rest": 0, # of don required>,
  "once_per_turn": 0,
  "your_turn": 0,
  "opponent_turn": 0,
  "may": 0
}
EFFECT_AMOUNT_FLAGS = {
    "power_change_amount": 0,
    "cost_change_amount": 0,
    "draw_amount": 0,
    "search_amount": 0,
    "don_change_amount": 0,
}
OUTPUT_FILE = os.path.join(PARENT_DIRECTORY, "output/parsed_cards_output.txt")


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
def parse_cards():
    with open(OUTPUT_FILE, 'w') as output:
        with open(UNCONSOLIDATED_CARD_LIST_FILE, 'r') as f:
            cardList = json.load(f)
        for card in cardList:
            timing_flags = copy.deepcopy(TIMING_FLAGS)
            keyword_flags = copy.deepcopy(KEYWORD_FLAGS)
            effect_action_flags = copy.deepcopy(EFFECT_ACTION_FLAGS)
            effect_amount_flags = copy.deepcopy(EFFECT_AMOUNT_FLAGS)
            condition_flags = copy.deepcopy(CONDITIONS)
            
            timing_flags = parse_timing(card.get("effect"), timing_flags)
            keyword_flags = parse_keywords(card.get("effect"), keyword_flags)
            effect_action_flags, effect_amount_flags = parse_effect_action(card.get("effect"), effect_action_flags, effect_amount_flags)


            output.write(f"Card ID: {card.get('id')}\n")
            output.write(f"Name: {card.get('name')}\n")
            output.write(f"Effect: {card.get('effect')}\n\n")

            output.write("Timing Flags:\n")
            for k, v in timing_flags.items():
                output.write(f"  {k}: {v}\n")

            output.write("\nKeyword Flags:\n")
            for k, v in keyword_flags.items():
                output.write(f"  {k}: {v}\n")

            output.write("\nEffect Action Flags:\n")
            for k, v in effect_action_flags.items():
                output.write(f"  {k}: {v}\n")

            output.write("\nEffect Amount Flags:\n")
            for k, v in effect_amount_flags.items():
                output.write(f"  {k}: {v}\n")
            
            output.write("\nCondition Flags:\n")
            for k, v in condition_flags.items():
                output.write(f"  {k}: {v}\n")

            output.write("\n" + "-"*60 + "\n\n")

        print(f"Parsing complete! Output written to {output}")

 
    


#goes through effect text and figures fills in timing flags dict for a card
def parse_timing(effectText: str, timingFlags: dict):
    if not effectText or effectText== "-":
        timingFlags
    
    text=effectText.lower()
    if "[on play]" in text:
        timingFlags["on_play"] = 1
    if "[activate: main]" in text:
        timingFlags["activate_main"] = 1
    if "[main]" in text:
        timingFlags["main"] = 1
    if "[counter]" in text:
        timingFlags["counter"] = 1
    if "[when attacking]" in text:
        timingFlags["when_attacking"] = 1
    if "[on k.o.]" in text or "when this character is k.o.'d" in text:
        timingFlags["on_ko"] = 1
    if "[on block]" in text:
        timingFlags["on_block"] = 1
    if "[end of your turn]" in text:
        timingFlags["end_turn"] = 1
    if "[opponent's turn]" in text:
        timingFlags["opponent_turn"] = 1
    if "end of your opponent's next turn" in text:
        timingFlags["end_opponents_turn"] = 1
    
    return timingFlags

#goes through effect text and fills in keyword flags dict for a card
def parse_keywords(effectText: str, keywordFlags: dict):
    if not effectText or effectText== "-":
        return keywordFlags
    
    text = effectText.lower()

    if "[rush]" in text:
        keywordFlags["rush"] = 1
    if "[blocker]" in text:
        keywordFlags["blocker"] = 1
    if "[double attack]" in text:
        keywordFlags["double_attack"] = 1
    if "[banish]" in text:
        keywordFlags["banish"] = 1
    if "[trigger]" in text: 
        keywordFlags["trigger"] = 1
    if "[rush: character]" in text or "can attack Characters on the turn in which it is played" in text:
        keywordFlags["rush_character"] = 1
    if "[unblockable]" in text or "cannot activate a [blocker]" in text:
        keywordFlags["unblockable"] = 1
    
    return keywordFlags

#goes through effect text and fills in effect action flags dict for a card
def parse_effect_action(effectText: str, effectActionFlags: dict, effectAmountFlags):
    if not effectText or effectText== "-":
        return effectActionFlags, effectAmountFlags

    text = effectText.lower()
    text = text.replace('\u2212', '-')
    text = re.sub(r'\[on k\.o\.\]', '', text)
    text = text.replace("when this character is k.o.'d", '') 
    text = re.sub(r'\s+', ' ', text)
    #remove timing
    text = re.sub(r'\[[^\]]+\]', '', text)
    text = text.strip() 

    #power change + amount
    powerMatch = re.search(r'([+-])(\d+)0{3}', text)
    if powerMatch:
        if powerMatch.group(1) == '+':
            sign = 1
        else:
            sign = -1
        magnitude = sign * int(powerMatch.group(2)) * 1000
        effectActionFlags["power_change"] = 1
        effectAmountFlags["power_change_amount"] = magnitude


    #cost change + amount
    costMatch = re.search(r'([+-]\d+)\s*cost', text)
    if costMatch:
        if costMatch.group(1) == '+':
            sign = 1
        else:
            sign = -1
        magnitude = sign * int(costMatch.group(1)) * sign
        effectActionFlags["cost_change"] = 1
        effectAmountFlags["cost_change_amount"] = magnitude

    #ko effect (not timing)
    if "k.o." in text:
        effectActionFlags["ko"] = 1

    #draw effect
    drawMatch = re.search(r'draw (\d+) card[s]?', text)
    if drawMatch:
        drawAmount = int(drawMatch.group(1))
        effectActionFlags["draw"] = 1
        effectAmountFlags["draw_amount"] = drawAmount

    #search effect
    searchMatch = re.search(r'look at (\d+) card[s]? from the top of your deck', text)
    if searchMatch:
        searchAmount = int(searchMatch.group(1))
        effectActionFlags["search"] = 1
        effectAmountFlags["search_amount"] = searchAmount

    #rest
    restMatch = re.search(r"rest up to\s+(\d+)\s+of your opponent's characters", text)
    if restMatch:
        effectActionFlags["rest"] = 1
    
    #restand character
    unrestMatch = re.search(r"set up to\s+(\d+)\s+of your character[s]?.*?as active", text)
    if unrestMatch:
        effectActionFlags["unrest"] = 1
    
    #return character to hand 
    bounceMatch = re.search(r"return\s+up to\s+\d+\s+.*?character[s]?.*?to the owner's hand", text)
    if bounceMatch:
        effectActionFlags["bounce"] = 1

    #send character to bottom of deck
    bottomDeck = re.search(r"place\s+(?:up to\s+)?(\d+)\s+.*?character[s]?.*?at the bottom of the owner's deck", text)
    if bottomDeck:
        effectActionFlags["bottom_deck"] = 1

    #trash
    if "trash" in text:    
        effectActionFlags["trash"] = 1
    
    #give rested don
    donAttachMatch = re.search(r"give\s+(?:up to\s+)?(\d+)\s+rested\s+don!!\s+card[s]?.*?(?:leader|character)", text)
    if donAttachMatch:
        effectActionFlags["don_attach"] = 1
    
    #special case: don reattachment
    reassignMatch = re.search(r"give\s+(?:up to\s+|)(\d+)\s+currently given don!!\s+card[s]?.*?character", text)
    if reassignMatch:
        effectActionFlags["don_attach"] = 1
        effectActionFlags["don_remove"] = 1
    
    #don removal
    donRemoveMatch = re.search(r"return\s+(?:up to\s+|)(\d+)\s+currently given don!!\s+card[s]?.*?cost area", text)
    if donRemoveMatch:
        effectActionFlags["don_remove"] = 1

    #life removal
    lifeRemoveMatch = re.search(r'(?:add|trash|remove)\s+(?:up to\s+)?(\d+)\s+card[s]?\s+from the (?:top|bottom) of your(?: opponent\'s)? life cards',text)
    if lifeRemoveMatch:
        effectActionFlags["life_remove"] = 1
    
    #life addition
    lifeAdditionMatch = re.search( r'add\s+(?:up to\s+)?(\d+)\s+card[s]?.*?to the top of your life cards', text)
    if lifeAdditionMatch:
        amount = int(lifeAdditionMatch.group(1))
        effectActionFlags["life_add"] = 1
        effectAmountFlags["life_add_amount"] = amount

    
    #special case: life swapping
    lifeSwapMatch = re.search(r"add\s+(\d+)\s+card[s]?\s+from the (?:top|bottom) of your life cards to your hand", text)
    if lifeSwapMatch:
        effectActionFlags["life_remove"] = 1
        effectActionFlags["life_add"] = 1
    
    #don add from don deck
    donAddMatch = re.search(r'add\s+(?:up to\s+)?(\d+)\s+don!!\s+card[s]?.*?from your don!! deck', text)
    if donAddMatch:
        amount = int(donAddMatch.group(1))
        effectActionFlags["don_add"] = 1
        effectAmountFlags["don_change_amount"] = amount
    
    #don remove to don deck
    donRemoveMatch = re.search(r'(?:return|returns|may return).*?(\d+)?\s*don!!\s+card[s]?.*?field.*?don!! deck',text)
    if donRemoveMatch:
        if donRemoveMatch.group(1):
            amount = int(donRemoveMatch.group(1))
        else:
            amount = 1
        effectActionFlags["don_change"] = 1
        effectAmountFlags["don_change_amount"] = -amount

    # DON restand effect
    donRestandMatch = re.search(r"set up to\s+(\d+)\s+of your don!!\s+cards\s+as active", text)
    if donRestandMatch:
        amount = int(donRestandMatch.group(1))
        effectActionFlags["don_restand"] = 1
        effectAmountFlags["don_restand_amount"] = amount

    
    return effectActionFlags, effectAmountFlags



def parse_conditions(effectText: str, conditionsFlags: dict):
    if not effectText or effectText == "-":
        return conditionsFlags
    
    text = effectText.lower()
    text = text.replace('\u2212', '-')  # normalize minus signs
    text = re.sub(r'\s+', ' ', text)    # collapse whitespace

    # don!! x __ (attached don)
    donxMatch = re.search(r"\[don!! x(\d+)\]", text)
    if donxMatch:
        conditionsFlags["don_times"] = int(donxMatch.group(1))

    # don!! -__ (don sent back to don deck)
    donMinusMatch = re.search(r"(?:don!! )?-(\d+)", text)
    if donMinusMatch:
        conditionsFlags["don_minus"] = int(donMinusMatch.group(1))

    # don __ (don rested)
    donRestMatch = re.search(r"\u2461", text)
    if donRestMatch:
        conditionsFlags["don_rest"] = int(donRestMatch.group(1))

    # once_per_turn: phrases like "once per turn"
    if "[once per turn]" in text:
        conditionsFlags["once_per_turn"] = 1

    # your_turn: phrases like "during your turn"
    if "[your turn]" in text:
        conditionsFlags["your_turn"] = 1

    # opponent_turn: phrases like "during your opponent's turn"
    if "[opponent's turn]" in text:
        conditionsFlags["opponent_turn"] = 1

    # may: catchall for "you may"
    if "you may" in text:
        conditionsFlags["may"] = 1

    return conditionsFlags



    


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "parse_cards":
            if len(sys.argv)>2:
                parse_cards(sys.argv[2])
            else:
                parse_cards()
        elif sys.argv[1] == "parse_timing":
            parse_timing()
        elif sys.argv[1] == "card_counter":
            card_counter()
        else:
            print("Unknown command.")
    else:
        print("Usage: python script.py [consolidate|reset]")