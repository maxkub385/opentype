#!/usr/bin/env python3
"""
Test script to debug the shaping result and see what glyphs are actually produced.
"""

import ttxread
import ttxfont

def debug_shaping_result():
    """Debug what glyphs are produced by shaping"""
    try:
        # Load the Egyptian hieroglyph font
        font = ttxread.read_ttx("eot.ttx")
        print(f"Loaded font with {len(font.glyphs)} glyphs")
        
        # Create simulator
        simulator = ttxfont.Simulator(font)
        
        # Test the token sequence
        tokens = ["A1", "vj", "A1", "vj", "A1"]
        print(f"\nInput tokens: {tokens}")
        
        # Run shaping
        simulator.set_tokens(tokens)
        shaped_tokens = simulator.tokens
        positions = simulator.positionings
        print(f"Shaped tokens: {shaped_tokens}")
        print(f"Positions: {positions}")
        
        # Check each shaped token
        for i, token in enumerate(shaped_tokens):
            print(f"\nToken {i}: {token}")
            
            # Check if it exists in font
            exists_in_glyphs = token in font.glyphs
            has_contours = hasattr(font, 'contours') and token in font.contours
            has_components = hasattr(font, 'components') and token in font.components
            
            print(f"  Exists in font.glyphs: {exists_in_glyphs}")
            print(f"  Has contours: {has_contours}")
            print(f"  Has components: {has_components}")
            
            if has_contours:
                contours = font.contours[token]
                print(f"  Number of contours: {len(contours) if contours else 0}")
            
            if has_components:
                components = font.components[token]
                print(f"  Number of components: {len(components) if components else 0}")
                if components:
                    print(f"  Components: {components[:3]}...")  # Show first 3
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_shaping_result()