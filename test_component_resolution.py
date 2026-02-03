#!/usr/bin/env python3
"""
Test script to verify component glyph resolution is working correctly.
"""

import ttxread
from font_analyzer_ui import resolve_glyph_outline, contours_to_svg_path

def test_component_resolution():
    """Test component glyph resolution with eot.ttx font"""
    try:
        # Load the Egyptian hieroglyph font
        font = ttxread.read_ttx("eot.ttx")
        print(f"Loaded font with {len(font.glyphs)} glyphs")
        
        # Test with vj glyph which we know uses components
        glyph_name = "vj"
        print(f"\nTesting component resolution for glyph: {glyph_name}")
        
        # Check if glyph has contours directly
        has_contours = hasattr(font, 'contours') and glyph_name in font.contours
        print(f"Has direct contours: {has_contours}")
        
        # Check if glyph has components
        has_components = hasattr(font, 'components') and glyph_name in font.components
        print(f"Has components: {has_components}")
        
        if has_components:
            components = font.components[glyph_name]
            print(f"Components: {components}")
        
        # Try to resolve the outline
        outline = resolve_glyph_outline(glyph_name, font)
        if outline:
            print(f"Successfully resolved outline with {len(outline)} contours")
            
            # Try to convert to SVG path
            svg_path = contours_to_svg_path(outline)
            if svg_path:
                print(f"Successfully generated SVG path (length: {len(svg_path)})")
                print(f"SVG path preview: {svg_path[:100]}...")
            else:
                print("Failed to generate SVG path")
        else:
            print("Failed to resolve outline")
        
        # Test with the composite glyph QB5 that results from shaping
        print(f"\nTesting with shaped result glyph: QB5")
        qb5_outline = resolve_glyph_outline("QB5", font)
        if qb5_outline:
            print(f"Successfully resolved QB5 outline with {len(qb5_outline)} contours")
        else:
            print("Failed to resolve QB5 outline")
        
        # Test with A1_22R which has components
        print(f"\nTesting with component glyph: A1_22R")
        a1_outline = resolve_glyph_outline("A1_22R", font)
        if a1_outline:
            print(f"Successfully resolved A1_22R outline with {len(a1_outline)} contours")
            
            # Try to convert to SVG path
            svg_path = contours_to_svg_path(a1_outline)
            if svg_path:
                print(f"Successfully generated SVG path (length: {len(svg_path)})")
            else:
                print("Failed to generate SVG path")
        else:
            print("Failed to resolve A1_22R outline")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_component_resolution()