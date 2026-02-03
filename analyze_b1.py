import ttxread, ttxfont, ttxtables
from ttxfont import Simulator

# Load the font
print("Loading font...")
font = ttxread.read_ttx('eot.ttx')
print('Font loaded successfully')

# Create a simple test sequence with just B1
tokens = ['B1']
print('Input tokens:', tokens)

# Apply shaping
print("Applying shaping...")
simulator = Simulator(font)
simulator.suppressed = ['ss01', 'rtlm']  # Suppress some features as in the original test
simulator.set_tokens(tokens)
print('Shaping completed')

# Show basic stats
print(f'\nInput tokens: {len(tokens)}')
print(f'Output glyphs: {len(simulator.tokens)}')
print(f'Rules applied: {len(simulator.applications)}')

# Show output glyphs
print('\nOutput glyphs:')
for glyph in simulator.tokens:
    print(f'  {glyph}')

# Show first few rules to understand the progression
print('\nFirst 10 rules applied:')
for i, rule in enumerate(simulator.applications[:10]):
    print(f'{i+1}. {rule}')

print('\nRules 30-40:')
for i, rule in enumerate(simulator.applications[29:40], 30):
    print(f'{i}. {rule}')

print('\nLast 10 rules applied:')
for i, rule in enumerate(simulator.applications[-10:], len(simulator.applications)-9):
    print(f'{i}. {rule}')