# OpenType Font Analyzer

A Python-based graphical user interface for analyzing OpenType font shaping behavior. This tool allows you to load TTX files and analyze how substitution and positioning rules are applied to token sequences.

## Original OpenType Simulator

This project builds upon an OpenType simulator tool in Python to help understand complicated sets of substitution rules in OpenType. Only a small part of OpenType has been implemented, and what has been implemented may not be completely accurate.

## New Features

- **Interactive GUI**: User-friendly interface for font analysis
- **TTX File Upload**: Browse and load TTX (TrueType XML) font files
- **Token Sequence Input**: Enter custom token sequences for analysis
- **Rule Visualization**: See all substitution and positioning rules applied in order
- **Detailed Results**: View step-by-step application of OpenType features
- **Font Information**: Display font metadata and available features

## Requirements

- Python 3.6 or later
- lxml library
- tkinter (included with Python)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure all required Python modules are in the same directory:
   - `font_analyzer_ui.py` (main GUI application)
   - `ttxread.py` (TTX file parser)
   - `ttxfont.py` (Font model and simulator)
   - `ttxtables.py` (Table reading utilities)

## Usage

### Method 1: Using the GUI

1. **Launch the application**:
   ```bash
   python font_analyzer_ui.py
   ```
   
   Or on Windows, double-click `run_analyzer.bat`

2. **Load a TTX file**:
   - Click "Browse..." button
   - Select a `.ttx` font file
   - The font information will be displayed in the "Font Info" tab

3. **Enter token sequence**:
   - Type tokens separated by spaces in the "Token Sequence" field
   - Example: `A1 vj A1 vj A1`

4. **Analyze**:
   - Click "Analyze" button or press Enter
   - View results in the tabs:
     - **Rules Applied**: Step-by-step rule applications
     - **Final Result**: Shaped output with coordinates
     - **Font Info**: Font metadata and features

### Method 2: Command Line

You can also use the underlying modules directly:

```python
from ttxread import read_ttx
from ttxfont import Simulator

# Load font
font = read_ttx('your_font.ttx')

# Create simulator
sim = Simulator(font)
sim.set_tokens(['A1', 'vj', 'A1'])

# Get results
print(sim.steps_str())  # Rules applied
print(sim.shaped_str())  # Final result
```

## Understanding the Output

### Rules Applied Tab
Shows each rule application in order:
- **Feature**: OpenType feature being applied (e.g., 'rlig', 'mark')
- **Lookup**: Lookup table index
- **Positions**: Token positions affected
- **Rule**: The specific substitution or positioning rule
- **Result**: Token sequence after rule application

### Final Result Tab
Shows the final shaped output:
- Token names with final coordinates
- Summary statistics (input/output token counts, rules applied)

### Font Info Tab
Displays font metadata:
- Script and language information
- Available GSUB/GPOS features
- Lookup table summaries

## Example Token Sequences

For Egyptian hieroglyph fonts:
- `A1 vj A1 vj A1` - Simple vertical stacking
- `A1 hj A1 hj A1` - Horizontal arrangement
- `QB5 r0v1 c0h5` - Complex glyph combinations

For Latin fonts:
- `f i` - Ligature formation
- `a acute` - Accent attachment
- `A B C` - Basic character sequence

## Troubleshooting

### Common Issues

1. **"Error loading font"**:
   - Ensure the TTX file is valid and readable
   - Check that all required Python modules are available

2. **"No rules were applied"**:
   - Check if the token names exist in the font
   - Verify the font contains the expected OpenType features

3. **Import errors**:
   - Ensure all Python files are in the same directory
   - Install required dependencies: `pip install lxml`

### Debug Mode

For more detailed error information, run from command line:
```bash
python font_analyzer_ui.py
```

Error messages and stack traces will be displayed in the console.

## Architecture

The application consists of several components:

- **`font_analyzer_ui.py`**: Main GUI application using tkinter
- **`ttxread.py`**: Parses TTX XML files into font objects
- **`ttxfont.py`**: Font model classes and shaping simulator
- **`ttxtables.py`**: Utilities for reading font tables

The simulator applies OpenType rules in this order:
1. GSUB (Glyph Substitution) features
2. GPOS (Glyph Positioning) features

Each feature contains multiple lookup tables with specific rules for transforming the glyph sequence.

## Contributing

This tool is designed for analyzing and debugging OpenType font behavior. It's particularly useful for:

- Font developers testing shaping rules
- Researchers studying complex script behavior
- Students learning about OpenType technology

## License

This software is provided as-is for educational and research purposes.
handle all cases correctly.

## Getting started

See `unittests.py`, which generate fonts and compute traces in directories `generated` and `traces`.

## Note

I have concentrated on subsitution rules for now. The positioning rules still need to be revised.
