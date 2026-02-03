import ttxread, ttxfont
from ttxfont import Simulator

# Load the font
print("Loading font...")
font = ttxread.read_ttx('eot.ttx')
print('Font loaded successfully')

# Test sequences that might trigger multi-to-one substitutions
test_sequences = [
    "A1 vj",
    "A1 vj A1", 
    "vj A1",
    "A1 B1",
    "rm1 dv0",  # From the ligature we found
    "rm2 dv0",  # Another one we found
    "cleanup Qi",  # Another ligature we found
]

for sequence in test_sequences:
    print(f"\n=== Testing: '{sequence}' ===")
    tokens = sequence.split()
    print(f"Input tokens: {tokens} (count: {len(tokens)})")
    
    simulator = Simulator(font)
    simulator.suppressed = ['ss01', 'rtlm']
    simulator.set_tokens(tokens)
    
    print(f"Output tokens: {simulator.tokens} (count: {len(simulator.tokens)})")
    
    # Check if we got reduction
    if len(simulator.tokens) < len(tokens):
        print(f"*** REDUCTION: {len(tokens)} -> {len(simulator.tokens)} ***")
        # Show the specific rules that caused ligatures
        for app in simulator.applications:
            if 'LigSubstitution' in str(type(app['rule'])):
                print(f"Ligature rule: {app}")
    elif len(simulator.tokens) > len(tokens):
        print(f"Expansion: {len(tokens)} -> {len(simulator.tokens)}")
    else:
        print("No change in token count")