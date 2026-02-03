import ttxread, ttxfont
from ttxfont import Simulator

# Load the font
print("Loading font...")
font = ttxread.read_ttx('eot.ttx')
print('Font loaded successfully')

# Test sequence A1 B1
tokens = ['A1', 'B1']
print(f'Input tokens: {tokens}')

# Apply shaping
print("Applying shaping...")
simulator = Simulator(font)
simulator.suppressed = ['ss01', 'rtlm']
simulator.set_tokens(tokens)
print('Shaping completed')

# Show basic stats
print(f'\nInput tokens: {len(tokens)}')
print(f'Output glyphs: {len(simulator.tokens)}')
print(f'Applications: {len(simulator.applications)}')

# Show output glyphs with their positions
print('\nFinal shaped result:')
for i, (token, place) in enumerate(zip(simulator.tokens, simulator.places)):
    if isinstance(place, dict):
        x = place.get('XCoordinate', 0)
        y = place.get('YCoordinate', 0)
        print(f'{token}({x}, {y})')
    else:
        print(f'{token}(?, ?)')

# Show positioning patterns
print('\nPositioning analysis:')
print('Base glyphs (no positioning):')
for i, (token, place) in enumerate(zip(simulator.tokens, simulator.places)):
    if isinstance(place, dict):
        x = place.get('XCoordinate', 0)
        y = place.get('YCoordinate', 0)
        if x == 0 and y == 0:
            print(f'  {token} - likely base glyph')

print('\nMark glyphs (with positioning):')
for i, (token, place) in enumerate(zip(simulator.tokens, simulator.places)):
    if isinstance(place, dict):
        x = place.get('XCoordinate', 0)
        y = place.get('YCoordinate', 0)
        if x != 0 or y != 0:
            print(f'  {token} at ({x}, {y}) - positioned mark')