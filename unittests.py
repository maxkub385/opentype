import os
import string
import subprocess

# Tests various substitutions by creating fonts.

from ttxtables import read_cmap, read_extra_names, read_name, read_glyf
from ttxfont import starter_font, Feature, MARK_GLYPH, \
	SingleSubstitution1, MultSubstitution, LigSubstitution, ChainSubstitution3, ReverseSubstitution, \
	Simulator
from ttxwrite import write_ttx

data_dir = 'data'
gen_dir = 'generated'
trace_dir = 'traces'

def filename_triple(name):
	filename = os.path.join(gen_dir, 'test' + str(name) + '.ttx')
	filename_tmp = os.path.join(gen_dir, 'test' + str(name) + '.ttf')
	filename_copy = os.path.join(gen_dir, 'test' + str(name) + '#1.ttx')
	return filename, filename_tmp, filename_copy

def ttx_to_ttx(file1, file2, file3):
	if os.path.isfile(file2):
		os.remove(file2)
	if os.path.isfile(file3):
		os.remove(file3)
	proc1 = subprocess.Popen(['ttx', file1])
	proc1.wait()
	proc2 = subprocess.Popen(['ttx', file2])
	proc2.wait()

def simulate_subst(font, tokens, filename):
	sim = Simulator(font)
	sim.set_tokens(tokens)
	with open(os.path.join(trace_dir, 'trace' + str(filename) + '.txt'), "w") as file:
		file.write(sim.in_tokens_str() + '\n\n')
		file.write(sim.steps_str())

def capital_font():
	font = starter_font()
	font.add_glyph('.null')
	font.add_glyph('nonmarkingreturn')
	for c in string.ascii_uppercase:
		font.add_glyph(c)
	font.set_property('head', 'unitsPerEm', 1700)
	font.set_today()
	font.set_property('hhea', 'ascent', 1492)
	font.set_property('hhea', 'descent', -114)
	font.set_property('hhea', 'lineGap', 153)
	font.set_property('vhea', 'ascent', 1000)
	font.set_property('vhea', 'descent', 1000)
	font.set_property('vhea', 'lineGap', 0)
	font.cmap0 = read_cmap(os.path.join(data_dir, 'capitals_cmap0.xml'))
	font.cmap4 = read_cmap(os.path.join(data_dir, 'capitals_cmap4.xml'))
	read_glyf(os.path.join(data_dir, 'capitals_glyf.xml'), font)
	read_name(os.path.join(data_dir, 'capitals_name.xml'), font)
	font.adjust_n_glyphs()
	return font

def make_all_mark(font):
	for c in string.ascii_uppercase:
		font.glyph_to_class[c] = MARK_GLYPH

def make_some_mark(font):
	for c in ['A','B','C','D','E']:
		font.glyph_to_class[c] = MARK_GLYPH

# Simple font without substitutions.
def test_type0():
	font = capital_font()
	filename, filename_tmp, filename_copy = filename_triple('0')
	write_ttx(font, filename)
	ttx_to_ttx(filename, filename_tmp, filename_copy)

# Simple font with Type 1 substitution.
def test_type1():
	font = capital_font()
	abvs = Feature('abvs')
	lookup = font.new_GSUB_lookup('1', feat=abvs)
	lookup.add(SingleSubstitution1('A', 'B'))
	lookup.add(SingleSubstitution1('B', 'C'))
	font.add_GSUB_feature(abvs)
	filename, filename_tmp, filename_copy = filename_triple('1')
	write_ttx(font, filename)
	ttx_to_ttx(filename, filename_tmp, filename_copy)
	simulate_subst(font, ['A','B','C'], '1')

# Simple font with Type 1 substitution in extension.
def test_type1ext():
	font = capital_font()
	abvs = Feature('abvs')
	lookup = font.new_GSUB_lookup('7/1')
	lookup.add(SingleSubstitution1('A', 'B'))
	lookup.add(SingleSubstitution1('B', 'C'))
	abvs.add_lookup_index(lookup.index)
	font.add_GSUB_feature(abvs)
	filename, filename_tmp, filename_copy = filename_triple('71')
	write_ttx(font, filename)
	ttx_to_ttx(filename, filename_tmp, filename_copy)
	simulate_subst(font, ['A','B','C'], '71')

# Simple font with Type 2 substitution.
def test_type2():
	font = capital_font()
	abvs = Feature('abvs')
	lookup = font.new_GSUB_lookup('2')
	lookup.add(MultSubstitution('A', ['B','C']))
	lookup.add(MultSubstitution('B', ['C','D']))
	abvs.add_lookup_index(lookup.index)
	font.add_GSUB_feature(abvs)
	filename, filename_tmp, filename_copy = filename_triple('2')
	write_ttx(font, filename)
	ttx_to_ttx(filename, filename_tmp, filename_copy)
	simulate_subst(font, ['A','B','C'], '2')

# Simple font with Type 2 substitution in extension.
def test_type2ext():
	font = capital_font()
	abvs = Feature('abvs')
	lookup = font.new_GSUB_lookup('7/2')
	lookup.add(MultSubstitution('A', ['B','C']))
	lookup.add(MultSubstitution('B', ['C','D','E','F','G']))
	abvs.add_lookup_index(lookup.index)
	font.add_GSUB_feature(abvs)
	filename, filename_tmp, filename_copy = filename_triple('72')
	write_ttx(font, filename)
	ttx_to_ttx(filename, filename_tmp, filename_copy)
	simulate_subst(font, ['A','B','C'], '72')

# Simple font with Type 4 substitution.
def test_type4():
	font = capital_font()
	liga = Feature('liga')
	lookup = font.new_GSUB_lookup('4')
	lookup.add(LigSubstitution(['A','B','C','D'], 'T'))
	lookup.add(LigSubstitution(['A','B'], 'R'))
	lookup.add(LigSubstitution(['A','B','C'], 'S'))
	lookup.add(LigSubstitution(['A','B','C','D','E'], 'U'))
	liga.add_lookup_index(lookup.index)
	font.add_GSUB_feature(liga)
	filename, filename_tmp, filename_copy = filename_triple('4')
	write_ttx(font, filename)
	ttx_to_ttx(filename, filename_tmp, filename_copy)
	simulate_subst(font, ['A','B','C'], '4')

# Simple font with Type 4 substitution in extension.
def test_type4ext():
	font = capital_font()
	liga = Feature('liga')
	lookup = font.new_GSUB_lookup('7/4')
	lookup.add(LigSubstitution(['A','B','C','D'], 'T'))
	lookup.add(LigSubstitution(['A','B'], 'R'))
	lookup.add(LigSubstitution(['A','B','C'], 'S'))
	lookup.add(LigSubstitution(['A','B','C','D','E'], 'U'))
	liga.add_lookup_index(lookup.index)
	font.add_GSUB_feature(liga)
	filename, filename_tmp, filename_copy = filename_triple('74')
	write_ttx(font, filename)
	ttx_to_ttx(filename, filename_tmp, filename_copy)
	simulate_subst(font, ['A','B','C'], '74')

# Simple font with Type 4 substitution.
# Filter with class. The glyphs to be replaced should be in class.
def test_type4filterclass():
	font = capital_font()
	make_all_mark(font)
	font.mark_to_class['A'] = 2
	font.mark_to_class['B'] = 2
	font.mark_to_class['C'] = 2
	liga = Feature('liga')
	lookup = font.new_GSUB_lookup('4')
	lookup.mark_class = 2
	lookup.add(LigSubstitution(['A','B','C'], 'B'))
	lookup.add(LigSubstitution(['A','B'], 'S'))
	liga.add_lookup_index(lookup.index)
	font.add_GSUB_feature(liga)
	filename, filename_tmp, filename_copy = filename_triple('4filterclass')
	write_ttx(font, filename)
	ttx_to_ttx(filename, filename_tmp, filename_copy)
	simulate_subst(font, ['A','X','B','Y','C','A','Y','B','Y','A','B'], '4filterclass')

# Simple font with Type 4 substitution.
# Filter with set. The glyphs to be replaced should be in set.
def test_type4filterset():
	font = capital_font()
	make_all_mark(font)
	liga = Feature('liga')
	lookup = font.new_GSUB_lookup('4')
	font.index_to_glyphs[0] = ['A','B','D'] # filter sets needs to be numbered from 0 up
	lookup.filter_set = 0
	lookup.add(LigSubstitution(['A','B','D'], 'B'))
	lookup.add(LigSubstitution(['A','B'], 'S'))
	# LigSubstitution(['X','B'], 'Z') # would be useless because X not in set
	liga.add_lookup_index(lookup.index)
	font.add_GSUB_feature(liga)
	filename, filename_tmp, filename_copy = filename_triple('4filterset')
	write_ttx(font, filename)
	ttx_to_ttx(filename, filename_tmp, filename_copy)
	simulate_subst(font, ['A','X','B','Y','D','A','Y','B','Y','A','B','X','B'], '4filterset')

# Simple font with Type 6 (Format 3) substitution.
# Here the simulator would not be correct.
def test_type6():
	font = capital_font()
	make_some_mark(font)
	font.index_to_glyphs[0] = ['A','D']
	font.index_to_glyphs[1] = ['A','B']
	liga = Feature('liga')
	lookup1 = font.new_GSUB_lookup('4')
	lookup1.add(LigSubstitution(['A','D'], 'C'))
	lookup1.filter_set = 0
	lookup2 = font.new_GSUB_lookup('4')
	lookup2.add(LigSubstitution(['B','B'], 'E'))
	lookup3 = font.new_GSUB_lookup('6.3', feat=liga)
	lookup3.add(ChainSubstitution3([], [['A'],['B']], [],                   
        [(0, lookup1.index),(1, lookup2.index)]))
	lookup3.filter_set = 1
	lookup4 = font.new_GSUB_lookup('1', feat=liga)
	lookup4.add(SingleSubstitution1('A', 'P'))
	lookup4.add(SingleSubstitution1('B', 'Q'))
	lookup4.add(SingleSubstitution1('C', 'R'))
	lookup4.add(SingleSubstitution1('D', 'S'))
	lookup4.add(SingleSubstitution1('E', 'T'))
	font.add_GSUB_feature(liga)
	filename, filename_tmp, filename_copy = filename_triple('6')
	write_ttx(font, filename)
	ttx_to_ttx(filename, filename_tmp, filename_copy)
	simulate_subst(font, ['A','B','B','D'], '6a')
	simulate_subst(font, ['A','B','B','F'], '6b')

# Simple font with Type 6 (Format 3) substitution in extension.
def test_type6ext():
	font = capital_font()
	make_all_mark(font)
	liga = Feature('liga')
	lookup1 = font.new_GSUB_lookup('4')
	lookup1.add(LigSubstitution(['A','A'], 'C'))
	lookup2 = font.new_GSUB_lookup('4')
	lookup2.add(LigSubstitution(['B','B'], 'D'))
	lookup3 = font.new_GSUB_lookup('7/6.3', feat=liga)
	lookup3.add(ChainSubstitution3([], [['A','B'],['A','B']], [], \
		[(0, lookup1.index),(1, lookup2.index)]))
	font.add_GSUB_feature(liga)
	filename, filename_tmp, filename_copy = filename_triple('76')
	write_ttx(font, filename)
	ttx_to_ttx(filename, filename_tmp, filename_copy)
	simulate_subst(font, ['A','A','B','B'], '76a')
	simulate_subst(font, ['A','A','A','B','B'], '76b')

# Simple font with Type 8 substitution.
def test_type8():
	font = capital_font()
	liga = Feature('liga')
	lookup = font.new_GSUB_lookup('8', feat=liga)
	lookup.add(ReverseSubstitution([['A']], ['A','B','C','D'], [], ['E','F','G','H']))
	font.add_GSUB_feature(liga)
	filename, filename_tmp, filename_copy = filename_triple('8')
	write_ttx(font, filename)
	ttx_to_ttx(filename, filename_tmp, filename_copy)
	simulate_subst(font, ['A','A','A'], '8')

# Simple font with Type 8 substitution in extension.
def test_type8ext():
	font = capital_font()
	liga = Feature('liga')
	lookup = font.new_GSUB_lookup('7/8', feat=liga)
	lookup.add(ReverseSubstitution([['A']], ['A','B','C','D'], [], ['E','F','G','H']))
	font.add_GSUB_feature(liga)
	filename, filename_tmp, filename_copy = filename_triple('78')
	write_ttx(font, filename)
	ttx_to_ttx(filename, filename_tmp, filename_copy)
	simulate_subst(font, ['A','A','A'], '78')

if __name__ == '__main__':
	if not os.path.exists(gen_dir):
		os.makedirs(gen_dir)
	if not os.path.exists(trace_dir):
		os.makedirs(trace_dir)
	# test_type0()
	# test_type1()
	# test_type1ext()
	# test_type2()
	# test_type2ext()
	# test_type4()
	# test_type4ext()
	# test_type4filterclass()
	# test_type4filterset()
	test_type6()
	# test_type6ext()
	# test_type8()
	# test_type8ext()
