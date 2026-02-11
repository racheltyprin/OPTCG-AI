import json
import sys
import os
import torch

# Add root to path to resolve src and root-level modules
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from src.parseCards import CardEffectParser
from src.cardDataClass import Card

def run_tests():
    parser = CardEffectParser()
    
    # Updated to look for combined.json in the data directory relative to project root
    data_path = os.path.join(root_path, 'data', 'combined.json')
    
    if not os.path.exists(data_path):
        # Fallback for sandbox environment
        alt_path = os.path.join(root_path, 'upload', 'pasted_file_B8BTQi_combined.json')
        if os.path.exists(alt_path):
            data_path = alt_path
        else:
            print(f"Error: Data file not found at {data_path}")
            return

    with open(data_path, 'r') as f:
        raw_data = json.load(f)
    
    # Test IDs
    test_ids = [
        "EB01-046_r1", # Brook: Sequential (Debuff then KO)
        "OP04-001",    # Nefeltari Vivi (Leader): Passive + Active
        "OP08-118",    # Silvers Rayleigh: Multi-target, multi-magnitude
        "OP02-085_p2", # Magellan: Self cost vs Opponent effect
        "OP05-098_p2"  # Enel (Leader): Life replacement
    ]
    
    output_dir = os.path.join(root_path, 'output')
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "parsed_cards_output.txt")
    
    with open(report_path, "w") as f:
        f.write("="*100 + "\n")
        f.write(f"{'OPTCG MULTI-STEP EFFECT TENSOR REPORT':^100}\n")
        f.write("="*100 + "\n\n")
        
        for data in raw_data:
            if data.get('id') not in test_ids: continue
            
            effect_text = data.get('effect', '')
            steps = parser.parse_card_effects(effect_text)
            keywords = parser.parse_keywords(effect_text)
            
            card = Card(
                card_id=data.get('id', ''),
                name=data.get('name', ''),
                category=data.get('category', ''),
                set=data.get('pack_id', ''),
                cost=data.get('cost', 0) or 0,
                power=data.get('power', 0) or 0,
                counter=data.get('counter', 0) or 0,
                life=data.get('life', 0) or 0,
                colors=data.get('colors', []),
                types=data.get('types', []),
                attributes=data.get('attributes', []),
                trigger=bool(data.get('trigger')),
                keyword_flags=keywords,
                effects=steps
            )
            
            f.write(f"CARD: {card.name} ({card.card_id})\n")
            f.write(f"ORIGINAL EFFECT:\n{effect_text}\n\n")
            
            f.write(f"GLOBAL KEYWORDS: { {k:v for k,v in card.keyword_flags.items() if v != 0} }\n")
            
            for i, step in enumerate(card.effects):
                f.write(f"  STEP {i}:\n")
                f.write(f"    timing:     { {k:v for k,v in step.timing_flags.items() if v != 0} }\n")
                f.write(f"    target:     { {k:v for k,v in step.target_flags.items() if v != 0} }\n")
                f.write(f"    scope:      { {k:v for k,v in step.scope_flags.items() if v != 0} }\n")
                f.write(f"    action:     { {k:v for k,v in step.action_flags.items() if v != 0} }\n")
                
                # Filter conditions for cost_req/power_req
                cond_filtered = {}
                for k, v in step.condition_flags.items():
                    if k in ["cost_req", "power_req"]:
                        if v != -999: cond_filtered[k] = v
                    elif v != 0: cond_filtered[k] = v
                if cond_filtered:
                    f.write(f"    condition:  {cond_filtered}\n")
                
                cost_filtered = {k:v for k,v in step.cost_flags.items() if v != 0}
                if cost_filtered:
                    f.write(f"    cost:       {cost_filtered}\n")
            
            tensor = card.to_tensor()
            f.write(f"\nGENERATED TENSOR (Shape: {tensor.shape}):\n")
            f.write(f"{tensor}\n")
            f.write("\n" + "-"*100 + "\n\n")
            
    print(f"Test complete. Report generated at: {report_path}")

if __name__ == "__main__":
    run_tests()