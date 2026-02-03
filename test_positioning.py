import ttxread, ttxfont
from ttxfont import Simulator

# Load the font
font = ttxread.read_ttx('eot.ttx')

# Test sequences that should trigger positioning
test_sequences = [
    "A1 vj A1",  # This created a complex composite in our earlier tests
    "A1 hj A1",  # Horizontal joiner
    "B1 vj B1",  # Vertical joiner with B1
    "A1 A1",     # Two A1s might trigger positioning
    "vj A1",     # Joiner followed by glyph
    "A1 vj",     # Glyph followed by joiner
]

print("=== TESTING FOR NON-EMPTY POSITIONING ===")
print()

for sequence in test_sequences:
    print(f"Testing: '{sequence}'")
    tokens = sequence.split()
    
    simulator = Simulator(font)
    simulator.suppressed = ['ss01', 'rtlm']
    simulator.set_tokens(tokens)
    
    print(f"  Input tokens: {len(tokens)}")
    print(f"  Output tokens: {len(simulator.tokens)}")
    
    # Check if we have positioning data
    if hasattr(simulator, 'places') and simulator.places:
        print(f"  Positioning data: {len(simulator.places)} positions")
        
        # Show non-empty positions
        non_empty_positions = []
        for i, pos in enumerate(simulator.places):
            if pos:
                # Handle different position formats
                x_coord = 0
                y_coord = 0
                
                if isinstance(pos, dict):
                    x_coord = pos.get('XCoordinate', 0)
                    y_coord = pos.get('YCoordinate', 0)
                elif isinstance(pos, tuple) and len(pos) >= 2:
                    x_coord = pos[0] if pos[0] else 0
                    y_coord = pos[1] if pos[1] else 0
                
                if x_coord != 0 or y_coord != 0:
                    non_empty_positions.append((i, simulator.tokens[i], x_coord, y_coord))
        
        if non_empty_positions:
            print("  *** NON-EMPTY POSITIONS FOUND! ***")
            for i, token, x, y in non_empty_positions:
                print(f"    {token} at position {i}: ({x}, {y})")
        else:
            print("  All positions are empty")
    else:
        print("  No positioning data")
    
    print()

# Also test some component sequences that we know get positioned
print("=== TESTING COMPONENT SEQUENCES ===")

component_sequences = [
    "r0v6 c0h4",  # Positioning marks
    "QB4 r0v6",   # Base + mark
    "m0 B1",      # Middle + base
]

for sequence in component_sequences:
    print(f"Testing components: '{sequence}'")
    tokens = sequence.split()
    
    simulator = Simulator(font)
    simulator.suppressed = ['ss01', 'rtlm']
    simulator.set_tokens(tokens)
    
    if hasattr(simulator, 'places') and simulator.places:
        print(f"  Positions: {simulator.places}")
    else:
        print("  No positioning data")
    print()