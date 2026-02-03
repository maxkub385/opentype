#!/usr/bin/env python3
"""
Demo script to test the visual rendering functionality
"""

from ttxread import read_ttx
from ttxfont import Simulator
from font_analyzer_ui import create_svg_from_shaped_result

def demo_visual_rendering():
    """Demonstrate the visual rendering with a simple example"""
    print("Demo: Visual Rendering of OpenType Font Analysis")
    print("=" * 50)
    
    # Try to load a small demo font
    try:
        font_path = "small/demo#1.ttx"
        print(f"Loading font: {font_path}")
        font = read_ttx(font_path)
        
        # Simple token sequence
        tokens = ["A", "B", "C"]
        print(f"Input tokens: {tokens}")
        
        # Create simulator and run
        simulator = Simulator(font)
        simulator.set_tokens(tokens)
        
        print(f"Final tokens: {simulator.tokens}")
        print(f"Final positions: {simulator.places}")
        
        # Convert places to the format expected by SVG renderer
        if hasattr(simulator, 'places'):
            places_list = []
            for place in simulator.places:
                if hasattr(place, 'items') and callable(place.items):
                    # It's a dictionary-like object
                    places_list.append(dict(place.items()))
                elif isinstance(place, dict):
                    places_list.append(place)
                else:
                    # It's a tuple or other format, create a dict
                    places_list.append({'XCoordinate': 0, 'YCoordinate': 0})
        else:
            places_list = [{'XCoordinate': 0, 'YCoordinate': 0} for _ in simulator.tokens]
        
        # Generate SVG
        svg_content = create_svg_from_shaped_result(font, simulator.tokens, places_list)
        
        # Save SVG to file
        with open("demo_output.svg", "w") as f:
            f.write(svg_content)
        
        print("\nSVG saved to demo_output.svg")
        print("You can open this file in a web browser to see the visual rendering.")
        
        # Also create an HTML file
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Visual Rendering Demo</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
        .svg-container {{ border: 1px solid #ccc; padding: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>OpenType Font Analysis - Visual Rendering Demo</h1>
        <p>Font: {font_path}</p>
        <p>Tokens: {' '.join(tokens)}</p>
    </div>
    <div class="svg-container">
        {svg_content}
    </div>
</body>
</html>
"""
        
        with open("demo_output.html", "w") as f:
            f.write(html_content)
        
        print("HTML file saved to demo_output.html")
        print("Open demo_output.html in your web browser to see the rendered glyphs!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_visual_rendering()