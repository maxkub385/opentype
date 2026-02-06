#!/usr/bin/env python3


import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import re
import traceback
import tempfile
import webbrowser
from html import escape
from ttxread import read_ttx
from ttxfont import Simulator



def units_per_em(font, default=1000):
    try:
        return int(font.properties.get("head", {}).get("unitsPerEm", default))
    except Exception:
        return default


def resolve_glyph_outline(glyph_name, font, resolved_cache=None, preserve_scale=False):

	if resolved_cache is None:
		resolved_cache = set()

	if glyph_name in resolved_cache:
		return []
	resolved_cache.add(glyph_name)

	contours = getattr(font, "contours", {}).get(glyph_name)
	if contours:
		return contours

	comps = getattr(font, "components", {}).get(glyph_name)
	if not comps:
		return []

	out = []
	for comp in comps:
		comp_name = comp.get("glyphName")
		if not comp_name:
			continue

		comp_contours = resolve_glyph_outline(comp_name, font, resolved_cache, preserve_scale=preserve_scale)
		if not comp_contours:
			continue

		x_off = float(comp.get("x", 0) or 0)
		y_off = float(comp.get("y", 0) or 0)

		if preserve_scale:
			sx = 1.0
			sy = 1.0
		else:
			sx = float(comp.get("scalex", 1.0) or 1.0)
			sy = float(comp.get("scaley", 1.0) or 1.0)

		for contour in comp_contours:
			new_contour = []
			for pt in contour:
				try:
					x, y, on = pt
					nx = float(x) * sx + x_off
					ny = float(y) * sy + y_off
					new_contour.append((str(int(nx)), str(int(ny)), on))
				except Exception:
					continue
			if new_contour:
				out.append(new_contour)

	return out



def contours_to_svg(contours):
    if not contours:
        return ""
    parts = []
    for contour in contours:
        if not contour:
            continue
        x0, y0, _ = contour[0]
        parts.append(f"M {x0} {y0}")
        for (x, y, _on) in contour[1:]:
            parts.append(f"L {x} {y}")
        parts.append("Z")
    return " ".join(parts)


def glyph_bbox_from_contours(contours):
    xs, ys = [], []
    for contour in contours:
        for (x, y, _on) in contour:
            try:
                xs.append(float(x))
                ys.append(float(y))
            except Exception:
                pass
    if not xs or not ys:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def place_to_xy(place):
    """Simulator.places are usually tuples (x,y) in font units, but accept dicts too."""
    if isinstance(place, dict):
        return float(place.get("XCoordinate", 0) or 0), float(place.get("YCoordinate", 0) or 0)
    if isinstance(place, (tuple, list)) and len(place) >= 2:
        return float(place[0] or 0), float(place[1] or 0)
    return 0.0, 0.0

CONTROL_GLYPH_RE = re.compile(
    r'^(?:'
    r'GB\d+(?:_\d+)?|'
    r'QB\d+|Qi|Qf|cleanup|trg\d+|m\d+|o\d+|'
    r'c\d+[A-Za-z0-9]+|r\d+[A-Za-z0-9]+|et\d+|tsh\d+|'
    r'eh\d+|ev\d+|im\d+'
    r')$'
)

def iter_drawable_glyph_instances(font, tokens, positions):
    """
    Yields (token, x, y, path_d, bbox) for glyphs that have drawable outlines
    AND are "real signs" (filters out control/placeholder glyphs).
    """
    for tok, pos in zip(tokens, positions):
        if CONTROL_GLYPH_RE.match(tok):
            continue


        contours = resolve_glyph_outline(tok, font, preserve_scale=True)

        # shaped position
        if isinstance(pos, dict):
            x = float(pos.get("XCoordinate", 0))
            y = float(pos.get("YCoordinate", 0))
        elif isinstance(pos, (tuple, list)) and len(pos) >= 2:
            x, y = float(pos[0]), float(pos[1])
        else:
            x, y = 0.0, 0.0

        contours = resolve_glyph_outline(tok, font, preserve_scale=True)
        if not contours:
            continue

        path_d = contours_to_svg(contours)
        xs, ys = [], []
        for c in contours:
            for pt in c:
                try:
                    xs.append(float(pt[0]))
                    ys.append(float(pt[1]))
                except Exception:
                    pass
        if not xs or not ys or not path_d:
            continue

        minx = x + min(xs)
        maxx = x + max(xs)
        miny = y + min(ys)
        maxy = y + max(ys)
        yield tok, x, y, path_d, (minx, miny, maxx, maxy)




def create_svg_from_shaped_result(font, tokens, positions, px_per_em=800, margin=30):
	unitsPerEm = units_per_em(font)
	scale = float(px_per_em) / float(unitsPerEm)

	instances = list(iter_drawable_glyph_instances(font, tokens, positions))
	if not instances:
		return '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200"></svg>'

	# tight bounds in font units
	min_x = min(b[0] for *_, b in instances)
	min_y = min(b[1] for *_, b in instances)
	max_x = max(b[2] for *_, b in instances)
	max_y = max(b[3] for *_, b in instances)

	width_px = int((max_x - min_x) * scale + 2 * margin)
	height_px = int((max_y - min_y) * scale + 2 * margin)

	svg = []
	svg.append(
		f'<svg xmlns="http://www.w3.org/2000/svg" '
		f'width="{width_px}" height="{height_px}" viewBox="0 0 {width_px} {height_px}">'
	)
	svg.append('<style>.g{fill:black;stroke:none}</style>')

	for tok, x, y, path_d, _bbox in instances:
		tx = (x - min_x) * scale + margin
		ty = (max_y - y) * scale + margin
		svg.append(f'<g transform="translate({tx:.3f},{ty:.3f}) scale({scale:.6f}, {-scale:.6f})">')
		svg.append(f'<path class="g" d="{escape(path_d)}"/>')
		svg.append('</g>')

	svg.append('</svg>')
	return "\n".join(svg)


class EmulatorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenType Font Analyzer")
        self.root.geometry("1200x800")

        self.current_font = None
        self.current_filename = ""
        self.current_svg = ""

        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding="10")
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(4, weight=1)

        # File row
        ttk.Label(main, text="TTX File:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        file_frame = ttk.Frame(main)
        file_frame.grid(row=0, column=1, sticky="ew", pady=(0, 5))
        file_frame.columnconfigure(0, weight=1)

        self.file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_var, state="readonly").grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(file_frame, text="Browse...", command=self.browse_file).grid(row=0, column=1)

        # Tokens row
        ttk.Label(main, text="Token Sequence:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=(10, 5))
        input_frame = ttk.Frame(main)
        input_frame.grid(row=1, column=1, sticky="ew", pady=(10, 5))
        input_frame.columnconfigure(0, weight=1)

        self.tokens_var = tk.StringVar()
        entry = ttk.Entry(input_frame, textvariable=self.tokens_var)
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        entry.bind("<Return>", lambda e: self.analyze_font())
        ttk.Button(input_frame, text="Analyze", command=self.analyze_font).grid(row=0, column=1)

        ttk.Label(main, text="Enter tokens separated by spaces (e.g., 'A1 vj A1 vj A1')",
                  font=("Arial", 8), foreground="gray").grid(row=2, column=1, sticky="w", pady=(0, 10))

        ttk.Label(main, text="Analysis Results:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=(10, 5))

        search_frame = ttk.Frame(main)
        search_frame.grid(row=3, column=1, sticky="ew", pady=(10, 5))
        search_frame.columnconfigure(0, weight=1)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.search_entry.insert(0, "")

        btn_prev = ttk.Button(search_frame, text="Prev", width=6, command=lambda: self.search_prev())
        btn_prev.grid(row=0, column=1, padx=(0,4))
        btn_next = ttk.Button(search_frame, text="Next", width=6, command=lambda: self.search_next())
        btn_next.grid(row=0, column=2, padx=(0,4))
        btn_clear = ttk.Button(search_frame, text="Clear", width=6, command=lambda: self.clear_search())
        btn_clear.grid(row=0, column=3)


        # Notebook and tabs
        self.notebook = ttk.Notebook(main)
        self.notebook.grid(row=4, column=0, columnspan=2, sticky="nsew")

        # Tabs (must add *direct* children of the Notebook)
        rules_tab = ttk.Frame(self.notebook)
        self.notebook.add(rules_tab, text="Rules Applied")
        self.rules_text = scrolledtext.ScrolledText(rules_tab, wrap=tk.WORD, font=("Consolas", 10))
        self.rules_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # expose the text widget from the tab for easy lookup by the search helpers
        rules_tab.text_widget = self.rules_text

        result_tab = ttk.Frame(self.notebook)
        self.notebook.add(result_tab, text="Final Result")
        self.result_text = scrolledtext.ScrolledText(result_tab, wrap=tk.WORD, font=("Consolas", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        result_tab.text_widget = self.result_text

        info_tab = ttk.Frame(self.notebook)
        self.notebook.add(info_tab, text="Font Info")
        self.info_text = scrolledtext.ScrolledText(info_tab, wrap=tk.WORD, font=("Consolas", 10))
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        info_tab.text_widget = self.info_text

        visual = ttk.Frame(self.notebook)
        self.notebook.add(visual, text="Visual Rendering")

        controls = ttk.Frame(visual)
        controls.pack(fill=tk.X, padx=5, pady=5)

        self.view_svg_button = ttk.Button(controls, text="Open Visual Rendering in Browser",
                                          command=self.open_svg_in_browser, state=tk.DISABLED)
        self.view_svg_button.pack(side=tk.LEFT, padx=5)

        self.svg_text = scrolledtext.ScrolledText(visual, wrap=tk.WORD, font=("Consolas", 9))
        self.svg_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        visual.text_widget = self.svg_text

        # Status bar
        self.status_var = tk.StringVar(value="Ready. Please select a TTX file to begin.")
        ttk.Label(main, textvariable=self.status_var, relief=tk.SUNKEN).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.tokens_var.set("A1 vj A1 vj A1")

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select TTX File",
            filetypes=[("TTX files", "*.ttx"), ("All files", "*.*")],
            initialdir=os.getcwd(),
        )
        if filename:
            self.file_var.set(filename)
            self.current_filename = filename
            self.load_font()

    def load_font(self):
        if not self.current_filename:
            return
        try:
            self.status_var.set("Loading font...")
            self.root.update()
            self.current_font = read_ttx(self.current_filename)
            self._display_font_info()
            self.status_var.set(f"Font loaded: {os.path.basename(self.current_filename)}")
        except Exception as e:
            self.status_var.set(f"Error loading font: {e}")
            messagebox.showerror("Error", f"Error loading font:\n{e}")
            self.clear_results()
            self.current_font = None

    def _display_font_info(self):
        if not self.current_font:
            return
        f = self.current_font
        lines = [
            f"Font File: {os.path.basename(self.current_filename)}",
            f"Script: {getattr(f, 'script', 'Unknown')}",
            f"Number of Glyphs: {len(getattr(f, 'glyphs', []))}",
            "",
            "GSUB Features:",
        ]
        for feat in getattr(f, "GSUB_features", []):
            lines.append(f"  {feat.tag}: lookups {list(feat.lookup_indexes)}")
        lines.append(f"\nGSUB Lookups: {len(getattr(f, 'GSUB_lookups', {}))}")
        for idx, lookup in getattr(f, "GSUB_lookups", {}).items():
            lines.append(f"  Lookup {idx}: Type {lookup.typ}, {len(lookup.substitutions)} rules")

        lines.append("")
        lines.append("GPOS Features:")
        for feat in getattr(f, "GPOS_features", []):
            lines.append(f"  {feat.tag}: lookups {list(feat.lookup_indexes)}")
        lines.append(f"\nGPOS Lookups: {len(getattr(f, 'GPOS_lookups', {}))}")
        for idx, lookup in getattr(f, "GPOS_lookups", {}).items():
            lines.append(f"  Lookup {idx}: Type {lookup.typ}, {len(lookup.positionings)} rules")

        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", "\n".join(lines))

    def analyze_font(self):
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

            tokens = tokens_input.split()
            sim = Simulator(self.current_font)
            sim.suppressed = ["ss01", "rtlm"]
            sim.set_tokens(tokens)

            self._display_analysis_results(sim, tokens)
            self.status_var.set("Analysis complete.")
        except Exception as e:
            self.status_var.set(f"Error during analysis: {e}")
            messagebox.showerror("Error", f"Error during analysis:\n{e}\n\n{traceback.format_exc()}")

    def _display_analysis_results(self, simulator, original_tokens):
        self.rules_text.delete("1.0", tk.END)
        self.result_text.delete("1.0", tk.END)

        rules = []
        rules.append(f"Input tokens: {' '.join(original_tokens)}")
        rules.append(f"Initial tokens: {simulator.in_tokens_str()}")
        rules.append("")
        rules.append("Rules Applied (in order):")
        rules.append("=" * 50)

        if simulator.applications:
            for i, a in enumerate(simulator.applications, 1):
                feature = a.get("feature", "unknown")
                lookup_index = a.get("index", "unknown")
                posses = a.get("posses", [])
                rule = a.get("rule")

                rules.append(f"\n{i}. Feature: {feature}, Lookup: {lookup_index}")
                rules.append(f"   Positions affected: {', '.join(map(str, posses)) if posses else 'None'}")
                if rule is not None:
                    rules.append(f"   Rule: {rule}")

                if "tokens" in a:
                    toks = a["tokens"].copy()
                    if posses:
                        ins = min(posses)
                        if 0 <= ins <= len(toks):
                            toks.insert(ins, ">")
                    rules.append(f"   Result: {' '.join(toks)}")
        else:
            rules.append("No rules were applied.")

        self.rules_text.insert("1.0", "\n".join(rules))

        out = []
        out.append("Final Shaped Result:")
        out.append("=" * 30)
        out.append("")
        for t, p in zip(simulator.tokens, simulator.places):
            out.append(f"{t} {p}")
        out.append("")
        out.append("Summary:")
        out.append(f"Input tokens: {len(original_tokens)}")
        out.append(f"Output tokens: {len(simulator.tokens)}")
        out.append(f"Rules applied: {len(simulator.applications)}")

        self.result_text.insert("1.0", "\n".join(out))

        self.generate_visual(simulator)

    def generate_visual(self, simulator):
        try:

            places = [place_to_xy(plc) for plc in simulator.places]
            self.current_svg = create_svg_from_shaped_result(self.current_font, simulator.tokens, places)

            self.svg_text.delete("1.0", tk.END)
            self.svg_text.insert("1.0", self.current_svg)
            self.view_svg_button.config(state=tk.NORMAL if self.current_svg else tk.DISABLED)
        except Exception as e:
            self.current_svg = ""
            self.svg_text.delete("1.0", tk.END)
            self.svg_text.insert("1.0", f"Error generating visualization: {e}\n\n{traceback.format_exc()}")
            self.view_svg_button.config(state=tk.DISABLED)

    def open_svg_in_browser(self):
        if not self.current_svg:
            messagebox.showwarning("Warning", "No visualization available.")
            return
        try:
            html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>OpenType Font Analysis - Visual Rendering</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    .header {{ background:#f0f0f0; padding: 10px; margin-bottom: 20px; }}
    .svg-container {{ border: 1px solid #ccc; padding: 10px; overflow:auto; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>OpenType Font Analysis - Visual Rendering</h1>
    <p>Font: {escape(os.path.basename(self.current_filename) if self.current_filename else "Unknown")}</p>
  </div>
  <div class="svg-container">
    {self.current_svg}
  </div>
</body>
</html>
"""
            with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
                f.write(html)
                tmp = f.name
            webbrowser.open(f"file://{tmp}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open visualization:\n{e}")

    def clear_results(self):
        self.rules_text.delete("1.0", tk.END)
        self.result_text.delete("1.0", tk.END)
        self.info_text.delete("1.0", tk.END)
        self.svg_text.delete("1.0", tk.END)
        self.current_svg = ""
        self.view_svg_button.config(state=tk.DISABLED)

    def get_active_text_widget(self):

        try:
            tab_id = self.notebook.select()
            tab_frame = self.notebook.nametowidget(tab_id)
            return getattr(tab_frame, "text_widget", None)
        except Exception:
            return None

    def clear_search(self):
        w = self.get_active_text_widget()
        if w:
            try:
                w.tag_remove("search", "1.0", tk.END)
            except Exception:
                pass
        self.search_var.set("")
        self.search_entry.focus_set()

    def search_next(self):
        query = self.search_var.get()
        if not query:
            return
        w = self.get_active_text_widget()
        if not w:
            return

        w.tag_remove("search", "1.0", tk.END)

        start_index = w.index(tk.INSERT)
        idx = w.search(query, f"{start_index} +1c", tk.END, nocase=True)
        if not idx:

            idx = w.search(query, "1.0", tk.END, nocase=True)
        if idx:
            end = f"{idx} + {len(query)}c"
            w.tag_add("search", idx, end)
            w.tag_config("search", background="yellow")
            w.mark_set(tk.INSERT, end)
            w.see(idx)

    def search_prev(self):
        query = self.search_var.get()
        if not query:
            return
        w = self.get_active_text_widget()
        if not w:
            return
        w.tag_remove("search", "1.0", tk.END)

        insert_index = w.index(tk.INSERT)
        idx = w.search(query, "1.0", insert_index, backwards=True, nocase=True)
        if not idx:

            idx = w.search(query, "1.0", tk.END, backwards=True, nocase=True)
        if idx:
            end = f"{idx} + {len(query)}c"
            w.tag_add("search", idx, end)
            w.tag_config("search", background="yellow")
            w.mark_set(tk.INSERT, idx)
            w.see(idx)


if __name__ == "__main__":
    try:
        root = tk.Tk()
        EmulatorUI(root)
        root.mainloop()
    except Exception as e:
        traceback.print_exc()
        try:
            messagebox.showerror("Error", f"Failed to start Font Analyzer:\n{e}")
        except Exception:
            pass