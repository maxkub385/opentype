import ttxread, ttxfont
from ttxfont import Simulator

# Load the font
font = ttxread.read_ttx('eot.ttx')

print("=== EGYPTIAN HIEROGLYPH COMPONENT ANALYSIS ===")
print("Example: B1 (Egyptian Hieroglyph B001 - Seated woman)")
print()

# Step 1: Show the basic B1 glyph information
print("1. BASIC GLYPH INFO:")
print(f"   B1 glyph exists in font: {'B1' in font.glyphs}")
if 'B1' in font.glyphs:
    print(f"   B1 is a recognized glyph in the font")
    if 'B1' in font.components:
        print(f"   B1 has components: {font.components['B1']}")
    else:
        print("   B1 has no direct components (it's a base glyph)")
    
    if 'B1' in font.contours:
        print(f"   B1 has contour data: {len(font.contours['B1'])} contours")
    else:
        print("   B1 has no contour data (composite glyph)")

print()

# Step 2: Show what happens when B1 is processed
print("2. SUBSTITUTION PROCESS:")
tokens = ['B1']
simulator = Simulator(font)
simulator.suppressed = ['ss01', 'rtlm']
simulator.set_tokens(tokens)

print(f"   Input: {tokens}")
print(f"   Output: {simulator.tokens}")
print(f"   Component expansion: 1 → {len(simulator.tokens)} glyphs")

print()

# Step 3: Show the first few substitution rules that create components
print("3. COMPONENT CREATION RULES:")
for i, app in enumerate(simulator.applications[:8]):
    if i == 0:
        print(f"   Rule {i+1}: Initial expansion")
        print(f"      {app['tokens']}")
        print(f"      → B1 becomes: {app['tokens']}")
    else:
        print(f"   Rule {i+1}: {app['feature']} feature")
        print(f"      Positions {app['posses']}: {app['tokens']}")
    print()

print()

# Step 4: Analyze the final components and their roles
print("4. FINAL COMPONENT ANALYSIS:")
final_glyphs = simulator.tokens
glyph_roles = {
    'QB4': 'Main hieroglyph body (base structure)',
    'r0v6': 'Right positioning mark (vertical variant 6)', 
    'c0h4': 'Center positioning mark (horizontal variant 4)',
    'o46': 'Ornamental component (variant 46)',
    'm0': 'Middle structural element',
    'B1': 'Original glyph reference (lower position)',
    'c0eA': 'Center end mark (variant A)',
    'r0eB': 'Right end mark (variant B)'
}

for glyph in final_glyphs:
    role = glyph_roles.get(glyph, 'Unknown component')
    print(f"   {glyph:8} → {role}")

print()

# Step 5: Show positioning coordinates
print("5. COMPONENT POSITIONING:")
print("   (From your earlier analysis)")
positions = [
    ('QB4', 0, 0, 'Main body at baseline'),
    ('r0v6', -1365, 1860, 'Upper right area'),
    ('c0h4', -1365, 1860, 'Upper center area'),
    ('o46', -1365, 1860, 'Upper ornamental'),
    ('m0', -735, 930, 'Middle section'),
    ('B1', -735, 0, 'Lower reference'),
    ('c0eA', -735, 0, 'Lower center'),
    ('r0eB', -735, 0, 'Lower right')
]

for glyph, x, y, desc in positions:
    print(f"   {glyph:8} at ({x:5}, {y:4}) → {desc}")

print()
print("6. COMPONENT SYSTEM PRINCIPLES:")
print("   • Modular Design: Each hieroglyph breaks into reusable parts")
print("   • Positioning Marks: r0*, c0*, etc. control spatial relationships") 
print("   • Variant System: Numbers/letters indicate different versions (v6, h4, 46)")
print("   • Hierarchical Assembly: Base → Structure → Ornaments → Marks")
print("   • Coordinate Stacking: Vertical layers at different Y coordinates")