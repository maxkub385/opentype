from ttxread import read_ttx
from ttxfont import Simulator
from font_analyzer_ui import create_svg_from_shaped_result

if __name__ == "__main__":
    font = read_ttx('eot.ttx')
    sim = Simulator(font)
    sim.suppressed = ['ss01','rtlm']
    tokens = ['A1','A1','A1']
    sim.set_tokens(tokens)
    places = []
    for p in getattr(sim, 'places', []):
        if hasattr(p, 'items') and callable(p.items):
            places.append(dict(p.items()))
        elif isinstance(p, dict):
            places.append(p)
        else:
            places.append({'XCoordinate':0,'YCoordinate':0})
    svg = create_svg_from_shaped_result(font, sim.tokens, places)
    with open('render_test.svg','w') as f:
        f.write(svg)
    print('Wrote render_test.svg')
