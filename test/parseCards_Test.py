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
    
    # Test a wider variety of cards to verify the new patterns
    test_ids = [
        "EB01-046_r1", # Brook: Cost reduction + K.O.
        "EB01-048_r1", # Laboon: Activate: Main + Rest self cost
        "EB01-012_r1", # Cavendish: On Play/When Attacking + Leader condition + Set DON active
        "EB01-038_p1", # Oh Come My Way: Counter + DON -1 cost + Target change
        "OP03-008_p2", # Buggy: Passive protection + On Play search
    ]
    
    output_dir = os.path.join(root_path, 'output')
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "parsed_cards_output.txt")
    
    with open(report_path, "w") as f:
        f.write("="*100 + "\n")
        f.write(f"{'OPTCG COMPREHENSIVE PARSER TENSOR REPORT':^100}\n")
        f.write("="*100 + "\n\n")
        
        for data in raw_data:
            if data.get('id') not in test_ids: continue
            
            effect_text = data.get('effect', '')
            flags = parser.parse_to_flags(effect_text)
            
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
                timing_flags=flags["timing"],
                keyword_flags=flags["keywords"],
                effect_action_flags=flags["actions"],
                conditions=flags["conditions"],
                cost_flags=flags["costs"]
            )
            
            f.write(f"CARD: {card.name} ({card.card_id})\n")
            f.write(f"ORIGINAL EFFECT:\n{effect_text}\n\n")
            
            f.write("FLAG DICTIONARIES:\n")
            
            # Helper to filter dictionaries for reporting
            def filter_dict(d):
                filtered = {}
                for k, v in d.items():
                    if k == "cost_req":
                        if v != -999: # Show if explicitly set, even if 0
                            filtered[k] = v
                    elif v != 0:
                        filtered[k] = v
                return filtered

            f.write(f"  timing:     {filter_dict(card.timing_flags)}\n")
            f.write(f"  keywords:   {filter_dict(card.keyword_flags)}\n")
            f.write(f"  costs:      {filter_dict(card.cost_flags)}\n")
            f.write(f"  actions:    {filter_dict(card.effect_action_flags)}\n")
            f.write(f"  conditions: {filter_dict(card.conditions)}\n")
            
            tensor = card.to_tensor()
            # Replace sentinel with 0 for the tensor output
            clean_tensor = tensor.clone()
            # We know cost_req is the last element of conditions, which is the last part of the tensor
            # 3 (numeric) + 16 (timing) + 5 (keywords) + 26 (actions) + 10 (conditions) + 8 (costs) = 68
            # Wait, the order in to_tensor is numeric + flags (timing + keywords + actions + conds + costs)
            # Let's just replace all -999 with 0 for the display tensor
            clean_tensor[clean_tensor == -999] = 0
            
            f.write(f"\nGENERATED TENSOR (Shape: {tensor.shape}):\n")
            f.write(f"{clean_tensor}\n")
            f.write("\n" + "-"*100 + "\n\n")
            
    print(f"Test complete. Report generated at: {report_path}")

if __name__ == "__main__":
    run_tests()