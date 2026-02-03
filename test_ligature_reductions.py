import ttxread, ttxfont
from ttxfont import Simulator

# Load the font
font = ttxread.read_ttx('eot.ttx')

# Test component sequences that we saw in the B1 breakdown
# These might trigger actual ligature reductions
test_sequences = [
    # From B1 analysis - components that got ligated together
    "sh4 sv6",  # Rule 59 showed these being ligated to o46
    "cv0 cv6",  # Rule 39 showed these being ligated
    "eh4 im0 ev6",  # These were involved in ligature formation
    "r0bA c0bA",  # Base components
    "c0eA r0eA",  # End components
    # Direct test of the ligatures we found in TTX
    "cleanup Qi",
    "rm1 dv0",
    "rm2 dv0", 
    "rm3 dv0",
    "rm4 dv0",
    "rm5 dv0",
    "rm6 dv0",
]

print("Testing for actual ligature reductions...")

for sequence in test_sequences:
    tokens = sequence.split()
    
    simulator = Simulator(font)
    simulator.suppressed = ['ss01', 'rtlm']
    simulator.set_tokens(tokens)
    
    # Look for actual ligature rules that were applied
    ligature_rules = []
    for app in simulator.applications:
        if 'LigSubstitution' in str(type(app['rule'])):
            ligature_rules.append(app)
    
    if ligature_rules or len(simulator.tokens) < len(tokens):
        print(f"\n=== '{sequence}' ===")
        print(f"Input:  {tokens} (count: {len(tokens)})")
        print(f"Output: {simulator.tokens} (count: {len(simulator.tokens)})")
        
        if len(simulator.tokens) < len(tokens):
            print(f"*** REDUCTION: {len(tokens)} -> {len(simulator.tokens)} ***")
        
        for rule in ligature_rules:
            print(f"Ligature: pos {rule['posses']} -> {rule}")