#!/usr/bin/env python3
"""
OpenType Font Analyzer GUI

A user interface for analyzing OpenType font shaping behavior.
Users can upload TTX files and input token sequences to see
all substitution and positioning rules applied in order.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import traceback
import tempfile
import webbrowser
from pathlib import Path

# Import the existing font processing modules
try:
    from ttxread import read_ttx
    from ttxfont import Simulator
except ImportError as e:
    print(f"Error importing font modules: {e}")
    print("Make sure ttxread.py and ttxfont.py are in the same directory")


def contours_to_svg_path(contours):
    """Convert font contours to SVG path string"""
    if not contours:
        return ""
    
    path_parts = []
    for contour in contours:
        if not contour:
            continue
            
        # Points are tuples (x, y, on) - extract coordinates
        first_pt = contour[0]
        x, y, on = first_pt
        path_parts.append(f"M {x} {y}")
        
        # Add the rest of the points
        for pt in contour[1:]:
            x, y, on = pt
            if on == '1':  # On-curve point
                path_parts.append(f"L {x} {y}")
            else:  # Off-curve point (control point for curves)
                # For simplicity, treat as line for now
                # In a full implementation, you'd handle Bezier curves
                path_parts.append(f"L {x} {y}")
        
        # Close the contour
        path_parts.append("Z")
    
    return " ".join(path_parts)


def resolve_glyph_outline(glyph_name, font, resolved_cache=None, preserve_scale=False):
    """Resolve glyph outline, handling components recursively.

    If preserve_scale is True, component scalex/scaley are ignored (treated as 1.0)
    to keep base glyph sizes consistent when stacking.
    """
    if resolved_cache is None:
        resolved_cache = set()
    
    # Prevent infinite recursion
    if glyph_name in resolved_cache:
        return []
    
    resolved_cache.add(glyph_name)
    
    # Check if glyph has direct contours
    if glyph_name in font.contours and font.contours[glyph_name]:
        return font.contours[glyph_name]
    
    # Check if glyph has components
    if glyph_name in font.components and font.components[glyph_name]:
        all_contours = []
        for component in font.components[glyph_name]:
            if 'glyphName' in component:
                component_name = component['glyphName']
                component_contours = resolve_glyph_outline(component_name, font, resolved_cache, preserve_scale)
                
                # Apply component transformation if present
                x_offset = float(component.get('x', 0))
                y_offset = float(component.get('y', 0))
                if preserve_scale:
                    scale_x = 1.0
                    scale_y = 1.0
                else:
                    scale_x = float(component.get('scalex', 1.0))
                    scale_y = float(component.get('scaley', 1.0))
                
                # Transform contours
                transformed_contours = []
                for contour in component_contours:
                    transformed_contour = []
                    for pt in contour:
                        orig_x, orig_y, on = pt
                        new_x = float(orig_x) * scale_x + x_offset
                        new_y = float(orig_y) * scale_y + y_offset
                        transformed_contour.append((str(int(new_x)), str(int(new_y)), on))
                    transformed_contours.append(transformed_contour)
                
                all_contours.extend(transformed_contours)
        
        return all_contours
    
    # No contours or components found
    return []


def create_svg_from_shaped_result(font, tokens, positions):
    """Create an SVG visualization showing only glyphs that actually draw.

    Filters out tokens that do not resolve to contours/components, so only
    drawable glyphs appear in the visualization.
    """
    if not tokens or not font:
        return "<svg></svg>"
    
    svg_width = 1200
    svg_height = 600
    baseline_y = svg_height // 2
    scale = 0.15
    target_height_units = 1860  # Normalize base sign height to this units value
    
    svg_parts = [
        f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">',
        '<style>',
        '.glyph { fill: black; stroke: none; }',
        '.glyph-missing { fill: red; stroke: red; stroke-width: 1; opacity: 0.5; }',
        '.baseline { stroke: #ccc; stroke-width: 1; }',
        '.debug-text { font-family: monospace; font-size: 10px; fill: #666; }',
        '</style>',
        f'<line x1="0" y1="{baseline_y}" x2="{svg_width}" y2="{baseline_y}" class="baseline"/>',
    ]
    
    # Group glyphs into logical units based on their positioning
    # Only include tokens that resolve to drawable outlines
    logical_glyphs = group_glyphs_into_logical_units(font, tokens, positions)
    
    # Render each logical glyph as a composite
    render_x = 50
    
    for logical_unit in logical_glyphs:
        # Consider only drawable tokens for rendering bounds
        drawable = [g for g in logical_unit if resolve_glyph_outline(g['token'], font, preserve_scale=True)]
        if not drawable:
            continue

        min_x = min(g['abs_x'] for g in drawable)
        max_x = max(g['abs_x'] for g in drawable)
        min_y = min(g['abs_y'] for g in drawable)
        max_y = max(g['abs_y'] for g in drawable)
        
        # Create a group for this logical glyph
        svg_parts.append(f'<g transform="translate({render_x}, 0)">')
        
        # Render all components of this logical unit
        for glyph_info in drawable:
            token = glyph_info['token']
            rel_x = (glyph_info['abs_x'] - min_x) * scale
            rel_y = baseline_y - (glyph_info['abs_y'] * scale)
            
            # Try to resolve glyph outline
            contours = resolve_glyph_outline(token, font, preserve_scale=True)
            
            if contours:
                svg_path = contours_to_svg_path(contours)
                if svg_path and svg_path != "M0,0":
                    # Compute per-token normalization to maintain consistent visual size
                    # Preserve original glyph size ratios: no per-token normalization
                    norm = 1.0
                    svg_parts.append(
                        f'<path d="{svg_path}" '
                        f'transform="translate({rel_x}, {rel_y}) scale({scale * norm}, {-scale * norm})" '
                        f'class="glyph"/>'
                    )
            # Do not render placeholders for non-drawable tokens
        
        svg_parts.append('</g>')
        
        # Advance to next logical glyph position
        logical_width = (max_x - min_x) * scale + 120
        render_x += logical_width
    
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def get_glyph_height(font, token):
    """Estimate glyph height from contours; returns 0 for non-drawable tokens."""
    contours = resolve_glyph_outline(token, font, preserve_scale=True)
    ys = []
    for contour in contours:
        for pt in contour:
            try:
                ys.append(int(pt[1]))
            except Exception:
                pass
    if ys:
        return max(ys) - min(ys)
    # Non-drawable or empty outline
    return 0


STACK_TOLERANCE = 0.1

def auto_stack_by_heights(font, tokens, tolerance=STACK_TOLERANCE):
    """Auto-stack successive small signs vertically to approximate the height of a large sign.

    - No scaling is applied. Sizes are derived from glyph contours.
    - Start a new column when adding another sign would exceed the target height (with tolerance).
    - Target height for a column is the height of its first sign.
    Returns a list of logical units (columns), each a list of glyph dicts with abs_x/abs_y.
    """
    columns = []
    current = []
    used_h = 0
    row_target_h = None
    col_x = 0
    col_index = 0

    # Determine row target height from first drawable token
    for t in tokens:
        h0 = get_glyph_height(font, t)
        if h0 > 0:
            row_target_h = h0
            break

    for idx, token in enumerate(tokens):
        h = get_glyph_height(font, token)
        if h <= 0:
            continue

        if not current:
            # Start new column with this sign
            current = [{'token': token, 'abs_x': col_x, 'abs_y': 0, 'index': idx}]
            used_h = h
        else:
            # Target for stacking small signs is the row target height
            target_h = row_target_h if row_target_h else used_h
            if used_h + h <= target_h * (1.0 + tolerance):
                # Stack above within the same column
                current.append({'token': token, 'abs_x': col_x, 'abs_y': used_h, 'index': idx})
                used_h += h
            else:
                # Finish current column and start a new column with this sign
                columns.append(current)
                col_index += 1
                col_x += 1000  # advance to next column position in font units
                current = [{'token': token, 'abs_x': col_x, 'abs_y': 0, 'index': idx}]
                used_h = h

    if current:
        columns.append(current)

    return columns


def auto_stack_optimized(font, tokens, tolerance=STACK_TOLERANCE):
    """Reverse-order optimized stacking without scaling or joiners.

    - Iterate from end to start, stacking smaller signs above within a column
      until reaching the target row height (set by the first drawable token).
    - Start a new column when the next sign would exceed target height.
    - Skip non-drawable tokens (height <= 0).
    Returns columns: list of lists of glyph dicts with abs_x, abs_y.
    """
    # Determine row target height from first drawable token (leftmost)
    row_target_h = None
    for t in tokens:
        h0 = get_glyph_height(font, t)
        if h0 > 0:
            row_target_h = h0
            break

    columns_rev = []  # build from right to left
    current = []
    used_h = 0

    for idx in range(len(tokens) - 1, -1, -1):
        token = tokens[idx]
        h = get_glyph_height(font, token)
        if h <= 0:
            continue

        if not current:
            current = [{'token': token, 'abs_x': 0, 'abs_y': 0, 'index': idx}]
            used_h = h
        else:
            target_h = row_target_h if row_target_h else used_h
            if used_h + h <= target_h * (1.0 + tolerance):
                current.append({'token': token, 'abs_x': 0, 'abs_y': used_h, 'index': idx})
                used_h += h
            else:
                columns_rev.append(current)
                current = [{'token': token, 'abs_x': 0, 'abs_y': 0, 'index': idx}]
                used_h = h

    if current:
        columns_rev.append(current)

    # Reverse to left-to-right order and assign x positions
    columns = list(reversed(columns_rev))
    col_x = 0
    advance = 1000
    for col in columns:
        for g in col:
            g['abs_x'] = col_x
        col_x += advance
    return columns


def group_glyphs_into_logical_units(font, tokens, positions):
    """Group drawable glyphs into logical hieroglyph units based on positioning.

    Skips tokens that do not resolve to any drawable outline (no contours and no
    drawable components), ensuring only actual rendered glyphs are included.
    """
    if not tokens:
        return []
    # Always auto-stack, ignoring joiners and font positions
    return auto_stack_optimized(font, tokens)
    


class FontAnalyzerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenType Font Analyzer")
        self.root.geometry("1200x800")  # Increased size for visual tab
        
        # Current font and simulation data
        self.current_font = None
        self.current_filename = ""
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the user interface layout"""
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # File selection section
        ttk.Label(main_frame, text="TTX File:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5)
        )
        
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        file_frame.columnconfigure(0, weight=1)
        
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_var, state="readonly")
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(file_frame, text="Browse...", command=self.browse_file).grid(
            row=0, column=1
        )
        
        # Input sequence section
        ttk.Label(main_frame, text="Token Sequence:", font=("Arial", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=(10, 5)
        )
        
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(10, 5))
        input_frame.columnconfigure(0, weight=1)
        
        self.tokens_var = tk.StringVar()
        self.tokens_entry = ttk.Entry(input_frame, textvariable=self.tokens_var)
        self.tokens_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.tokens_entry.bind('<Return>', lambda e: self.analyze_font())
        
        ttk.Button(input_frame, text="Analyze", command=self.analyze_font).grid(
            row=0, column=1
        )
        
        # Help text for token input
        help_text = "Enter tokens separated by spaces (e.g., 'A1 vj A1 vj A1')"
        ttk.Label(main_frame, text=help_text, font=("Arial", 8), foreground="gray").grid(
            row=2, column=1, sticky=tk.W, pady=(0, 10)
        )
        
        # Results section
        ttk.Label(main_frame, text="Analysis Results:", font=("Arial", 10, "bold")).grid(
            row=3, column=0, sticky=tk.W, pady=(10, 5)
        )
        
        # Create notebook for tabbed results
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Rules Applied tab
        self.rules_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.rules_frame, text="Rules Applied")
        
        self.rules_text = scrolledtext.ScrolledText(
            self.rules_frame, wrap=tk.WORD, font=("Consolas", 10)
        )
        self.rules_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Final Result tab
        self.result_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.result_frame, text="Final Result")
        
        self.result_text = scrolledtext.ScrolledText(
            self.result_frame, wrap=tk.WORD, font=("Consolas", 10)
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Font Info tab
        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="Font Info")
        
        self.info_text = scrolledtext.ScrolledText(
            self.info_frame, wrap=tk.WORD, font=("Consolas", 10)
        )
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Visual Rendering tab
        self.visual_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.visual_frame, text="Visual Rendering")
        
        # Create frame for visual controls and display
        visual_controls = ttk.Frame(self.visual_frame)
        visual_controls.pack(fill=tk.X, padx=5, pady=5)
        
        # Button to open SVG in browser
        self.view_svg_button = ttk.Button(
            visual_controls, text="Open Visual Rendering in Browser", 
            command=self.open_svg_in_browser, state=tk.DISABLED
        )
        self.view_svg_button.pack(side=tk.LEFT, padx=5)
        
        # Text area for SVG preview
        self.svg_text = scrolledtext.ScrolledText(
            self.visual_frame, wrap=tk.WORD, font=("Consolas", 9)
        )
        self.svg_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Store SVG content for browser viewing
        self.current_svg = ""
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Please select a TTX file to begin.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Set initial example
        self.tokens_var.set("A1 vj A1 vj A1")
    
    def browse_file(self):
        """Open file dialog to select TTX file"""
        filename = filedialog.askopenfilename(
            title="Select TTX File",
            filetypes=[
                ("TTX files", "*.ttx"),
                ("All files", "*.*")
            ],
            initialdir=os.getcwd()
        )
        
        if filename:
            self.file_var.set(filename)
            self.current_filename = filename
            self.load_font()
    
    def load_font(self):
        """Load and parse the selected TTX file"""
        if not self.current_filename:
            return
        
        try:
            self.status_var.set("Loading font...")
            self.root.update()
            
            # Parse the TTX file
            self.current_font = read_ttx(self.current_filename)
            
            # Display font information
            self.display_font_info()
            
            self.status_var.set(f"Font loaded: {os.path.basename(self.current_filename)}")
            
        except Exception as e:
            error_msg = f"Error loading font: {str(e)}"
            self.status_var.set(error_msg)
            messagebox.showerror("Error", error_msg)
            self.clear_results()
    
    def display_font_info(self):
        """Display information about the loaded font"""
        if not self.current_font:
            return
        
        info_lines = []
        info_lines.append(f"Font File: {os.path.basename(self.current_filename)}")
        info_lines.append(f"Script: {getattr(self.current_font, 'script', 'Unknown')}")
        info_lines.append(f"Number of Glyphs: {len(self.current_font.glyphs)}")
        info_lines.append("")
        
        # GSUB features and lookups
        info_lines.append("GSUB Features:")
        for feature in self.current_font.GSUB_features:
            info_lines.append(f"  {feature.tag}: lookups {list(feature.lookup_indexes)}")
        
        info_lines.append(f"\nGSUB Lookups: {len(self.current_font.GSUB_lookups)}")
        for index, lookup in self.current_font.GSUB_lookups.items():
            info_lines.append(f"  Lookup {index}: Type {lookup.typ}, {len(lookup.substitutions)} rules")
        
        info_lines.append("")
        
        # GPOS features and lookups
        info_lines.append("GPOS Features:")
        for feature in self.current_font.GPOS_features:
            info_lines.append(f"  {feature.tag}: lookups {list(feature.lookup_indexes)}")
        
        info_lines.append(f"\nGPOS Lookups: {len(self.current_font.GPOS_lookups)}")
        for index, lookup in self.current_font.GPOS_lookups.items():
            info_lines.append(f"  Lookup {index}: Type {lookup.typ}, {len(lookup.positionings)} rules")
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, "\n".join(info_lines))
    
    def analyze_font(self):
        """Analyze the font with the given token sequence"""
        if not self.current_font:
            messagebox.showwarning("Warning", "Please select a TTX file first.")
            return
        
        tokens_input = self.tokens_var.get().strip()
        if not tokens_input:
            messagebox.showwarning("Warning", "Please enter a token sequence.")
            return
        
        try:
            self.status_var.set("Analyzing...")
            self.root.update()
            
            # Parse tokens (split by whitespace)
            tokens = tokens_input.split()
            
            # Create simulator and run analysis
            simulator = Simulator(self.current_font)
            simulator.suppressed = ['ss01', 'rtlm']  # Suppress some features as in the original test
            simulator.set_tokens(tokens)
            
            # Display results
            self.display_analysis_results(simulator, tokens)
            
            self.status_var.set("Analysis complete.")
            
        except Exception as e:
            error_msg = f"Error during analysis: {str(e)}"
            self.status_var.set(error_msg)
            messagebox.showerror("Error", error_msg + "\n\n" + traceback.format_exc())
    
    def display_analysis_results(self, simulator, original_tokens):
        """Display the analysis results in the UI"""
        # Clear previous results
        self.rules_text.delete(1.0, tk.END)
        self.result_text.delete(1.0, tk.END)
        
        # Display rules applied
        rules_lines = []
        rules_lines.append(f"Input tokens: {' '.join(original_tokens)}")
        rules_lines.append(f"Initial tokens: {simulator.in_tokens_str()}")
        rules_lines.append("")
        rules_lines.append("Rules Applied (in order):")
        rules_lines.append("=" * 50)
        
        if simulator.applications:
            for i, application in enumerate(simulator.applications, 1):
                feature = application.get('feature', 'unknown')
                lookup_index = application.get('index', 'unknown')
                positions = application.get('posses', [])
                rule = application.get('rule', None)
                
                rules_lines.append(f"\n{i}. Feature: {feature}, Lookup: {lookup_index}")
                rules_lines.append(f"   Positions affected: {', '.join(map(str, positions))}")
                
                if rule:
                    rules_lines.append(f"   Rule: {str(rule)}")
                
                # Show token state if available
                if 'tokens' in application:
                    tokens_display = application['tokens'].copy()
                    if positions and len(positions) > 0:
                        # Insert marker to show where the rule was applied
                        insert_pos = min(positions)
                        if insert_pos < len(tokens_display):
                            tokens_display.insert(insert_pos, '>')
                    rules_lines.append(f"   Result: {' '.join(tokens_display)}")
                
                # Show positioning info if available
                if 'positionings' in application:
                    positionings = application['positionings']
                    pos_info = []
                    for j, pos_dict in enumerate(positionings):
                        if pos_dict:
                            pos_info.append(f"{simulator.tokens[j] if j < len(simulator.tokens) else 'unknown'}({dict(pos_dict.items())})")
                    if pos_info:
                        rules_lines.append(f"   Positioning: {' '.join(pos_info)}")
        else:
            rules_lines.append("No rules were applied.")
        
        self.rules_text.insert(1.0, "\n".join(rules_lines))
        
        # Display final result
        result_lines = []
        result_lines.append("Final Shaped Result:")
        result_lines.append("=" * 30)
        result_lines.append("")
        
        # Show final tokens with positions
        if hasattr(simulator, 'tokens') and hasattr(simulator, 'places'):
            for token, place in zip(simulator.tokens, simulator.places):
                result_lines.append(f"{token}{place}")
        else:
            result_lines.append("No final positioning information available.")
        
        result_lines.append("")
        result_lines.append("Summary:")
        result_lines.append(f"Input tokens: {len(original_tokens)}")
        result_lines.append(f"Output tokens: {len(simulator.tokens) if hasattr(simulator, 'tokens') else 0}")
        result_lines.append(f"Rules applied: {len(simulator.applications) if hasattr(simulator, 'applications') else 0}")
        
        self.result_text.insert(1.0, "\n".join(result_lines))
        
        # Generate and display visual rendering
        self.generate_visual_rendering(simulator)
    
    def generate_visual_rendering(self, simulator):
        """Generate SVG visualization of the shaped result"""
        try:
            if hasattr(simulator, 'tokens') and hasattr(simulator, 'places'):
                # Convert places to consistent format
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
                
                # Create SVG from the shaped result
                self.current_svg = create_svg_from_shaped_result(
                    self.current_font, simulator.tokens, places_list
                )
                
                # Display SVG source in the text area
                self.svg_text.delete(1.0, tk.END)
                self.svg_text.insert(1.0, self.current_svg)
                
                # Enable the view button
                self.view_svg_button.config(state=tk.NORMAL)
                
            else:
                self.svg_text.delete(1.0, tk.END)
                self.svg_text.insert(1.0, "No positioning data available for visualization.")
                self.view_svg_button.config(state=tk.DISABLED)
                self.current_svg = ""
                
        except Exception as e:
            self.svg_text.delete(1.0, tk.END)
            self.svg_text.insert(1.0, f"Error generating visualization: {str(e)}")
            self.view_svg_button.config(state=tk.DISABLED)
            self.current_svg = ""
    
    def open_svg_in_browser(self):
        """Open the SVG visualization in the default web browser"""
        if not self.current_svg:
            messagebox.showwarning("Warning", "No visualization available.")
            return
        
        try:
            # Create a temporary HTML file with the SVG
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>OpenType Font Analysis - Visual Rendering</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
        .svg-container {{ border: 1px solid #ccc; padding: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>OpenType Font Analysis - Visual Rendering</h1>
        <p>Font: {os.path.basename(self.current_filename) if self.current_filename else 'Unknown'}</p>
        <p>Generated by OpenType Font Analyzer</p>
    </div>
    <div class="svg-container">
        {self.current_svg}
    </div>
</body>
</html>
"""
            
            # Write to temporary file and open in browser
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                temp_file = f.name
            
            webbrowser.open(f'file://{temp_file}')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open visualization: {str(e)}")
    
    def clear_results(self):
        """Clear all result displays"""
        self.rules_text.delete(1.0, tk.END)
        self.result_text.delete(1.0, tk.END)
        self.info_text.delete(1.0, tk.END)
        self.svg_text.delete(1.0, tk.END)
        self.current_svg = ""
        self.view_svg_button.config(state=tk.DISABLED)


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = FontAnalyzerUI(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()


if __name__ == "__main__":
    main()