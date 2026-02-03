import ttxread, ttxfont
from ttxfont import Simulator

# Load the font
font = ttxread.read_ttx('eot.ttx')

print("=== EGYPTIAN HIEROGLYPH COMPONENT SYSTEM DEEP DIVE ===")
print()

# Analyze multiple glyphs to understand component patterns
test_glyphs = ['A1', 'B1', 'C1', 'D1']

for glyph in test_glyphs:
    if glyph in font.glyphs:
        print(f"GLYPH: {glyph}")
        print(f"  Has components: {glyph in font.components and len(font.components[glyph]) > 0}")
        print(f"  Has contours: {glyph in font.contours and len(font.contours[glyph]) > 0}")
        
        # Show what it expands to
        simulator = Simulator(font)
        simulator.suppressed = ['ss01', 'rtlm']
        simulator.set_tokens([glyph])
        
        print(f"  Expands to {len(simulator.tokens)} components:")
        for i, component in enumerate(simulator.tokens):
            if i < 6:  # Show first 6 components
                print(f"    {component}")
            elif i == 6:
                print(f"    ... and {len(simulator.tokens) - 6} more")
                break
        print()

print()
print("=== COMPONENT NAMING CONVENTIONS ===")

# Analyze component naming patterns from our B1 example
components = ['QB4', 'r0v6', 'c0h4', 'o46', 'm0', 'c0eA', 'r0eB']

patterns = {
    'Q': 'Main structure prefix (QB4 = Base variant 4)',
    'r0': 'Right positioning (r0v6 = Right vertical variant 6)',
    'c0': 'Center positioning (c0h4 = Center horizontal variant 4)',
    'o': 'Ornamental element (o46 = Ornament variant 46)',
    'm': 'Middle element (m0 = Middle basic)',
    'e': 'End element (eA/eB = End variants A/B)'
}

print("Component prefixes and their meanings:")
for prefix, meaning in patterns.items():
    print(f"  {prefix:3} → {meaning}")

print()
print("=== SUBSTITUTION CHAIN EXAMPLE ===")
print("How B1 becomes QB4 + r0v6 + c0h4 + o46 + m0 + B1 + c0eA + r0eB:")
print()

simulator = Simulator(font)
simulator.suppressed = ['ss01', 'rtlm']
simulator.set_tokens(['B1'])

# Show key transformation steps
key_steps = [
    (0, "Initial: B1"),
    (3, "Add structure elements"),
    (10, "Break down components"), 
    (20, "Add positioning marks"),
    (40, "Form ligatures"),
    (60, "Final assembly"),
    (67, "Position components")
]

for step_num, description in key_steps:
    if step_num < len(simulator.applications):
        app = simulator.applications[step_num]
        print(f"Step {step_num:2}: {description}")
        print(f"         Feature: {app['feature']}")
        print(f"         Result:  {app['tokens'][:6]}{'...' if len(app['tokens']) > 6 else ''}")
        print()

print()
print("=== COORDINATE SYSTEM ===")
print("Egyptian hieroglyphs use a vertical stacking coordinate system:")
print()
print("Y = 1860: Upper area (ornaments, diacritics)")
print("Y =  930: Middle area (structural elements)")  
print("Y =    0: Baseline (main glyph, end marks)")
print()
print("X coordinates control horizontal positioning:")
print("X =    0: Main position")
print("X = -735: Left offset for secondary elements")
print("X =-1365: Far left for upper elements")

print()
print("=== ASSEMBLY STRATEGY ===")
print("1. DECOMPOSITION: Break logical glyph into semantic parts")
print("2. EXPANSION: Add positioning and structural elements")
print("3. REFINEMENT: Apply contextual substitutions")
print("4. LIGATURE: Combine related components")
print("5. POSITIONING: Apply final coordinate placement")
print("6. RESULT: Multiple positioned glyphs forming one logical unit")