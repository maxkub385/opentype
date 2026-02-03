import math

from ttxtables import read_charset, read_extra_names, read_name, read_glyf
from ttxfont import starter_font, Feature, SingleSubstitution1, MultSubstitution, LigSubstitution, \
	ChainSubstitution3, ReverseSubstitution, \
	BASE_GLYPH, LIGATURE_GLYPH, MARK_GLYPH, COMPONENT_GLYPH
from ttxwrite import write_ttx

def get_starter_font():
	font = starter_font()
	font.charset_egyptian = read_charset('data/charset_egyptian_newgardiner.xml')
	font.cmap0 = read_charset('data/newgardiner_cmap0.xml')
	font.charset_large = read_charset('data/charset_large_newgardiner.xml')
	font.charset_total = read_charset('data/charset_large_newgardiner.xml')
	font.charset_total.update(read_charset('data/charset_egyptian_newgardiner.xml'))
	read_extra_names('data/standard_extranames_newgardiner.xml', font)
	read_name('data/standard_name_newgardiner.xml', font)
	read_glyf('data/newgardiner_glyf_small.xml', font)
	return font

def add_bracket_symbols(font):
	font.add_name('ov') # open vertical
	font.add_name('cv') # close horizontal
	font.add_name('oh') # open horizontal
	font.add_name('ch') # close horizontal
	# font.add_name('nil') # removed bracket to be ignored

def add_metrics_symbols(font):
	for s in range(10):
		w_name = 'w' + str(s)
		h_name = 'h' + str(s)
		font.add_name(w_name)
		font.add_name(h_name)

def add_math_symbols(font):
	for s in range(50):
		name = 'num' + str(s)
		font.add_name(name)

BRACKET_SET = 0
SYNTAX_SET = 1
MATH_SET = 2

def make_bracket_set(font):
	font.index_to_glyphs[BRACKET_SET] = ['ov', 'cv', 'oh', 'ch']

def make_syntax_set(font):
	font.index_to_glyphs[SYNTAX_SET] = ['ov', 'cv', 'oh', 'ch', 'hj', 'vj']

def make_addition_set(font):
	font.index_to_glyphs[MATH_SET] = ['ov', 'cv', 'oh', 'ch'] + ['num' + str(n) for n in range(50)]

def make_syntax_class(font):
	font.mark_to_class['ov'] = 2
	font.mark_to_class['cv'] = 2
	font.mark_to_class['oh'] = 2
	font.mark_to_class['ch'] = 2
	font.mark_to_class['vj'] = 2
	font.mark_to_class['hj'] = 2
	for s in range(50):
		font.mark_to_class['num' + str(s)] = 5
	# font.mark_to_class['nil'] = 1

def make_sign_metric_rule(font, lookup, name):
	width = math.floor(font.xmax[name] / 100)
	height = math.floor(font.ymax[name] / 100)
	w_name = 'w' + str(width)
	h_name = 'h' + str(height)
	sub = MultSubstitution(name, [w_name, name, h_name])
	lookup.add(sub)

def make_sign_metric_rules(font, feature):
	lookup = font.new_GSUB_lookup('7/2')
	feature.add_lookup_index(lookup.index)
	names = ['u13000', 'u13082', 'u13083', 'u13123', 'u13124', 'u13132']
	for name in names:
		make_sign_metric_rule(font, lookup, name)

def make_bracket_prepend_hor(font):
	lookup = font.new_GSUB_lookup('7/2')
	for s in range(10):
		w_name = 'w' + str(s)
		pre = MultSubstitution(w_name, ['oh', w_name])
		lookup.add(pre)
	return lookup.index

def make_bracket_append_hor(font):
	lookup = font.new_GSUB_lookup('7/2')
	for s in range(10):
		h_name = 'h' + str(s)
		post = MultSubstitution(h_name, [h_name, 'ch'])
		lookup.add(post)
	return lookup.index

def make_bracket_prepend_ver(font):
	lookup = font.new_GSUB_lookup('7/2')
	pre = MultSubstitution('oh', ['ov', 'oh'])
	lookup.add(pre)
	return lookup.index

def make_bracket_append_ver(font):
	lookup = font.new_GSUB_lookup('7/2')
	post = MultSubstitution('ch', ['ch', 'cv'])
	lookup.add(post)
	return lookup.index

def make_hor_bracket_rules(font, feature, prepend, append):
	lookup = font.new_GSUB_lookup('7/6')
	feature.add_lookup_index(lookup.index)
	w_names = ['w' + str(s) for s in range(10)]
	h_names = ['h' + str(s) for s in range(10)]
	sub_pre1 = ChainSubstitution3([['hj']], [w_names], [], [])
	sub_pre2 = ChainSubstitution3([], [w_names], [], [(0, prepend)])
	lookup.add(sub_pre1)
	lookup.add(sub_pre2)
	sub_post1 = ChainSubstitution3([], [h_names], [['hj']], [])
	sub_post2 = ChainSubstitution3([], [h_names], [], [(0, append)])
	lookup.add(sub_post1)
	lookup.add(sub_post2)

def make_ver_bracket_rules(font, feature, prepend, append):
	lookup = font.new_GSUB_lookup('7/6')
	feature.add_lookup_index(lookup.index)
	sub_pre1 = ChainSubstitution3([['vj']], [['oh']], [], [])
	sub_pre2 = ChainSubstitution3([], [['oh']], [], [(0, prepend)])
	lookup.add(sub_pre1)
	lookup.add(sub_pre2)
	sub_post1 = ChainSubstitution3([], [['ch']], [['vj']], [])
	sub_post2 = ChainSubstitution3([], [['ch']], [], [(0, append)])
	lookup.add(sub_post1)
	lookup.add(sub_post2)

def make_remove_oh(font):
	lookup = font.new_GSUB_lookup('7/4')
	for prev in ['ov', 'vj']:
		sub = LigSubstitution([prev, 'oh'], prev)
		lookup.add(sub)
	return lookup.index

def make_remove_ch(font):
	lookup = font.new_GSUB_lookup('7/4')
	for next in ['cv', 'vj']:
		sub = LigSubstitution(['ch', next], next)
		lookup.add(sub)
	return lookup.index

def remove_singleton_bracket(font, feature, remove_oh, remove_ch):
	lookup = font.new_GSUB_lookup('7/6')
	lookup.filter_set = SYNTAX_SET
	feature.add_lookup_index(lookup.index)
	sub = ChainSubstitution3([], [['ov','vj'],['oh'],['ch']],[['cv','vj']], [(2, remove_ch),(0, remove_oh)])
	lookup.add(sub)

def make_summands(font, feature):
	lookup = font.new_GSUB_lookup('7/2')
	feature.add_lookup_index(lookup.index)
	for s in range(10):
		h_name = 'h' + str(s)
		sum_name = 'num' + str(s)
		sub = MultSubstitution(h_name, [h_name, sum_name])
		lookup.add(sub)
	sub_hj = MultSubstitution('hj', ['hj', 'num1', 'num1'])
	sub_ch = MultSubstitution('ch', ['ch', 'num1'])
	lookup.add(sub_hj)
	lookup.add(sub_ch)

def make_addition_subtables(font):
	tables = []
	for s1 in range(40):
		lookup = font.new_GSUB_lookup('7/1')
		tables.append(lookup.index)
		for s2 in range(10):
			s3 = s1 + s2
			s2_str = 'num' + str(s2)
			s3_str = 'num' + str(s3)
			sub = SingleSubstitution1(s2_str, s3_str)
			lookup.add(sub)
	return tables

def make_addition_table(font, feature, subtables):
	lookup = font.new_GSUB_lookup('7/6')
	# lookup.mark_class = 5
	lookup.filter_set = MATH_SET
	# feature.add_lookup_index(lookup.index)
	s2_strs = ['num' + str(s2) for s2 in range(10)]
	for s1 in range(40):
		s1_str = 'num' + str(s1)
		sub = ChainSubstitution3([[s1_str]], [s2_strs], [], [(0, subtables[s1])])
		lookup.add(sub)
	return lookup.index

def make_summation(font, feature, addition_table):
	lookup = font.new_GSUB_lookup('7/6')
	# lookup.mark_class = MATH_SET
	# lookup.mark_class = 1
	feature.add_lookup_index(lookup.index)
	nums = ['num' + str(s) for s in range(40)]
	sub = ChainSubstitution3([], [nums], [], [(0, addition_table)])
	lookup.add(sub)

def make_font():
	font = get_starter_font()
	add_bracket_symbols(font)
	add_metrics_symbols(font)
	add_math_symbols(font)
	make_syntax_class(font)
	make_bracket_set(font)
	make_syntax_set(font)
	make_addition_set(font)
	abvs = Feature('abvs')
	make_sign_metric_rules(font, abvs)
	prepend_hor = make_bracket_prepend_hor(font)
	append_hor = make_bracket_append_hor(font)
	make_hor_bracket_rules(font, abvs, prepend_hor, append_hor)
	prepend_ver = make_bracket_prepend_ver(font)
	append_ver = make_bracket_append_ver(font)
	make_ver_bracket_rules(font, abvs, prepend_ver, append_ver)
	remove_oh = make_remove_oh(font)
	remove_ch = make_remove_ch(font)
	remove_singleton_bracket(font, abvs, remove_oh, remove_ch)
	make_summands(font, abvs)
	addition_subtables = make_addition_subtables(font)
	addition_table = make_addition_table(font, abvs, addition_subtables)
	make_summation(font, abvs, addition_table)
	font.add_GSUB_feature(abvs)

	font.complete_glyph_list()
	font.adjust_n_glyphs()
	write_ttx(font, 'createdfont.ttx')

make_font()
