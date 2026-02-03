import os
from ttxread import read_ttx
from ttxfont import Simulator
from font_analyzer_ui import create_svg_from_shaped_result, get_glyph_height, group_glyphs_into_logical_units

# Load font
font = read_ttx("eot.ttx")
sim = Simulator(font)

sequences = {
    "seq_a1_b1x3": ["A1", "B1", "B1", "B1"],
    "seq_b1x3_a1": ["B1", "B1", "B1", "A1"],
    "seq_a1_vj_b1_hj_b1": ["A1", "vj", "B1", "hj", "B1"],
    "seq_a1_a1_b1x3": ["A1", "A1", "B1", "B1", "B1"],
}

out_dir = "."

for name, tokens in sequences.items():
    sim.set_tokens(tokens)
    # Normalize places to plain dicts
    places = []
    for p in getattr(sim, 'places', []):
        if hasattr(p, 'items') and callable(p.items):
            places.append(dict(p.items()))
        elif isinstance(p, dict):
            places.append(p)
        else:
            places.append({'XCoordinate':0,'YCoordinate':0})
    svg = create_svg_from_shaped_result(font, sim.tokens, places)
    out_path = os.path.join(out_dir, f"{name}.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    # Print a brief diagnostic: heights and columns computed
    columns = group_glyphs_into_logical_units(font, sim.tokens, places)
    print(f"{name} -> columns={len(columns)}")
    for ci, col in enumerate(columns):
        col_h = sum(get_glyph_height(font, g['token']) for g in col if get_glyph_height(font, g['token'])>0)
        print(f"  col {ci}: signs={[g['token'] for g in col]} height={col_h}")

print("Wrote multi-sequence SVGs.")
