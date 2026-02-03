from ttxfont import Font, Feature, GSUB_Lookup, Substitution, \
	GPOS_Lookup, SingleAdjustment, MarkBaseAttachment, MarkMarkAttachment, ChainPos, \
	BASE_GLYPH
	
from ttxwrite import write_ttx

font = Font()
font.properties['head'] = {'tableVersion': '1.0'}
font.properties['hhea'] = {'ascent': '1422'}
font.properties['vhea'] = {'ascent': '1035'}
font.properties['maxp'] = {'tableVersion': '0x10000'}
font.properties['OS_2'] = {'xAvgCharWidth': '1135'}
font.properties['OS_2']['panose'] = {'bProportion': '0'}
font.name = [{'nameID': '1', 'platformID': '1', 'platEncID': '0', \
					'langID': '0x0', 'unicode': 'True', 'text': 'This is the text'}]
font.palettes = [{'type': '2', 'colors': ['#252525FF', '#000000FF']}]

font.charset_large = {int('0x2046', 0): 'RightLeftbracketquill'}
font.charset_small = {int('0x22', 0): 'quotedbl'}
font.charset_total = {int('0x13000', 0): 'A1'}
font.vs_to_name = {(int('0x13455', 0), int('0xfe00', 0)): 'dq1234'}

font.glyphs = ['A', 'B']
font.properties['maxp']['numGlyphs'] = str(len(font.glyphs))
font.width = {'A': 200, 'B': 300}
font.lsb = {'A': 800, 'B': 900}
font.height = {'A': 400, 'B': 500}
font.tsb = {'A': 600, 'B': 700}
font.post = {'formatType': '2.0'}
font.extra_names = ['tcbb', 'tcbe']
font.color_layers = {'vj': [(1, 'c85'), (4, 'c92')]}
font.glyph_to_class = {'zwnj': BASE_GLYPH}
font.mark_to_class = {'c0bA': 3}
font.index_to_glyphs = {1: ['tcbb','ts']}

gsub_feature1 = Feature('pres')
gsub_feature1.add_lookup_index(3)
gsub_feature2 = Feature('ss01')
gsub_feature2.add_lookup_index(6)
font.add_GSUB_feature(gsub_feature1)
font.add_GSUB_feature(gsub_feature2)

substitution01 = Substitution([], ['a'], [], ['b'])
substitution02 = Substitution([], ['a'], [], ['b'])
lookup0 = GSUB_Lookup(10, '0')
lookup0.add(substitution01)
lookup0.add(substitution02)
font.add_GSUB_lookup(10, lookup0)

substitution11 = Substitution([], ['a'], [], ['b'])
substitution12 = Substitution([], ['a'], [], ['b'])
lookup1 = GSUB_Lookup(10, '1')
lookup1.add(substitution11)
lookup1.add(substitution12)
font.add_GSUB_lookup(10, lookup1)

substitution21 = Substitution([], ['A1'], [], ['et56','tsh56454435332211','A1','Qf'])
substitution22 = Substitution([], ['A11'], [], ['et66','tsh665544332211','A10','Qf'])
lookup2 = GSUB_Lookup(20, '2')
lookup2.add(substitution21)
lookup2.add(substitution22)
font.add_GSUB_lookup(20, lookup2)

substitution41 = Substitution([], ['Qf','mr']], [], ['mr'])
substitution42 = Substitution([], ['Qf','dq1']], [], ['dq1'])
lookup4 = GSUB_Lookup(30, '4')
lookup4.add(substitution41)
lookup4.add(substitution42)
font.add_GSUB_lookup(30, lookup4)

substitution61 = Substitution([['pre1'],['pre2']], ['Qf','mr'], [], [])
substitution62 = Substitution([], ['Qf','dq1'], [['post1','post2'],['post3']], 30)
lookup6 = GSUB_Lookup(60, '6')
lookup6.add(substitution61)
lookup6.add(substitution62)
lookup6.mark_class = 2
font.add_GSUB_lookup(60, lookup6)

adjustments1 = [{'glyph': 'it41', 'placement': {'YPlacement': 94}}, \
			{'glyph': 'it41R', 'placement': {'YPlacement': 95}}]
posit1 = SingleAdjustment('2', adjustments1)
lookup01 = GPOS_Lookup(910, '1')
lookup01.add_positioning(posit1)
font.add_GPOS_lookup(910, lookup01)

marks4 = [{'glyph': 'm1', 'class': 0, 'x': 0, 'y': 1}, {'glyph': 'm2', 'class': 1, 'x': 2, 'y': 3}]
bases4 = [{'glyph': 'b1', 'coordinates': {0: {'x': 4, 'y': 5}, 1: {'x': 6, 'y': 7}}}]
posit4 = MarkBaseAttachment(marks4, bases4)
lookup04 = GPOS_Lookup(940, '4')
lookup04.add_positioning(posit4)
font.add_GPOS_lookup(940, lookup04)

marks61 = [{'glyph': 'm1', 'class': 0, 'x': 0, 'y': 1}, {'glyph': 'm2', 'class': 1, 'x': 2, 'y': 3}]
marks62 = [{'glyph': 'm2', 'coordinates': {0: {'x': 4, 'y': 5}, 1: {'x': 6, 'y': 7}}}]
posit6 = MarkMarkAttachment(marks61, marks62)
lookup06 = GPOS_Lookup(960, '6')
lookup06.add_positioning(posit6)
font.add_GPOS_lookup(960, lookup06)

back81 = [['c0s0p25', 'c0s0p33'], ['c0s0p5', 'c0s0p66']]
input81 = [['c0h1', 'c0h2']]
fore81 = [['c0h4', 'c0h5'], ['c0h6', 'c0h7']]
rec81 = 123
posit8 = ChainPos(back81, input81, fore81, rec81)
lookup08 = GPOS_Lookup(980, '8')
lookup08.add_positioning(posit8)
lookup08.filter_set = 456
font.add_GPOS_lookup(980, lookup08)

gpos_feature1 = Feature('mkmk')
gpos_feature1.add_lookup_index(6)
font.add_GPOS_feature(gpos_feature1)

font.glyf = []

write_ttx(font, 'testfont.ttx')
