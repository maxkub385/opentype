from lxml import etree
from collections import defaultdict

from ttxfont import Font

def add_properties(font, prop_name, parent):
	elem = etree.SubElement(parent, prop_name)
	for key, value in font.properties[prop_name].items():
		sub_elem = etree.SubElement(elem, key)
		if isinstance(value, str):
			sub_elem.set('value', value)
		else:
			for sub_key, sub_value in value.items():
				sub_sub_elem = etree.SubElement(sub_elem, sub_key)
				sub_sub_elem.set('value', sub_value)

def add_name(font, parent):
	names = font.name
	elem = etree.SubElement(parent, 'name')
	for name in names:
		namerecord_elem = etree.SubElement(elem, 'namerecord')
		namerecord_elem.set('nameID', name['nameID'])
		namerecord_elem.set('platformID', name['platformID'])
		namerecord_elem.set('platEncID', name['platEncID'])
		namerecord_elem.set('langID', name['langID'])
		namerecord_elem.text = name['text']
		if 'unicode' in name and name['unicode'] == 'True':
			namerecord_elem.set('unicode', name['unicode'])

def add_CPAL(font, parent):
	elem = etree.SubElement(parent, 'CPAL')
	version_elem = etree.SubElement(elem, 'version')
	version_elem.set('value', '1')
	numpalette_elem = etree.SubElement(elem, 'numPaletteEntries')
	n_entries = 0
	if len(font.palettes) > 0:
		n_entries = len(font.palettes[0]['colors'])
	numpalette_elem.set('value', str(n_entries))
	for palette_index, palette in enumerate(font.palettes):
		palette_elem = etree.SubElement(elem, 'palette')
		palette_elem.set('index', str(palette_index))
		palette_elem.set('type', palette['type'])
		for color_index, color in enumerate(palette['colors']):
			color_elem = etree.SubElement(palette_elem, 'color')
			color_elem.set('index', str(color_index))
			color_elem.set('value', color)

def add_cmap(font, parent):
	# cmap4 = font.charset_large
	cmap6 = font.charset_small
	cmap12 = font.charset_total
	elem = etree.SubElement(parent, 'cmap')
	tableversion_elem = etree.SubElement(elem, 'tableVersion')
	tableversion_elem.set('version', '0')
	add_cmap_format_various(font.cmap4, '4', '0', '3', elem)
	if len(cmap12) > 0:
		add_cmap_format12(cmap12, '0', '4', elem)
	if len(font.cmap0) > 0:
		add_cmap_format_various(font.cmap0, '0', '1', '0', elem)
	if len(font.vs_to_name) > 0:
		add_cmap_format14(font.vs_to_name, elem)
	if len(font.charset_small) > 0:
		add_cmap_format_various(cmap6, '6', '1', '0', elem)
	add_cmap_format_various(font.cmap4, '4', '3', '1', elem)
	if len(cmap12) > 0:
		add_cmap_format12(cmap12, '3', '10', elem)

def add_cmap_format_various(cmap, num, platformID, platEncID, parent):
	elem = etree.SubElement(parent, 'cmap_format_' + num)
	elem.set('platformID', platformID)
	elem.set('platEncID', platEncID)
	elem.set('language', '0')
	for code, name in cmap.items():
		map_elem = etree.SubElement(elem, 'map')
		map_elem.set('code', hex(code))
		map_elem.set('name', name)

def add_cmap_format12(cmap, platformID, platEncID, parent):
	elem = etree.SubElement(parent, 'cmap_format_12')
	elem.set('platformID', platformID)
	elem.set('platEncID', platEncID)
	elem.set('format', '12')
	elem.set('reserved', '0')
	elem.set('length', '1972') # Will be recalculated
	elem.set('language', '0')
	elem.set('nGroups', '163')
	for code, name in cmap.items():
		map_elem = etree.SubElement(elem, 'map')
		map_elem.set('code', hex(code))
		map_elem.set('name', name)

def add_cmap_format14(vs_to_name, parent):
	elem = etree.SubElement(parent, 'cmap_format_14')
	elem.set('platformID', '0')
	elem.set('platEncID', '5')
	for (uv, uvs), name in vs_to_name.items():
		map_elem = etree.SubElement(elem, 'map')
		map_elem.set('uv', hex(uv))
		map_elem.set('uvs', hex(uvs))
		map_elem.set('name', name)

def add_GlyphOrder(font, parent):
	elem = etree.SubElement(parent, 'GlyphOrder')
	for index, name in enumerate(font.glyphs):
		add_GlyphID(index, name, elem)

def add_GlyphID(id, name, parent):
	elem = etree.SubElement(parent, 'GlyphID')
	elem.set('id', str(id))
	elem.set('name', name)

def add_hmtx(font, parent):
	elem = etree.SubElement(parent, 'hmtx')
	for name in sorted(font.glyphs):
		width = font.width[name]
		if width == 0 and name in font.xmax:
			width = font.xmax[name]
		lsb = font.lsb[name]
		add_mtx(name, 'width', width, 'lsb', lsb, elem)

def add_vmtx(font, parent):
	elem = etree.SubElement(parent, 'vmtx')
	for name in sorted(font.glyphs):
		height = font.height[name]
		tsb = font.tsb[name]
		add_mtx(name, 'height', height, 'tsb', tsb, elem)

def add_mtx(name, dim, size, extreme, val, elem):
	sub_elem = etree.SubElement(elem, 'mtx')
	sub_elem.set('name', name)
	sub_elem.set(dim, str(size))
	sub_elem.set(extreme, str(val))

def add_post(font, parent):
	elem = etree.SubElement(parent, 'post')
	for key, value in font.post.items():
		sub_elem = etree.SubElement(elem, key)
		sub_elem.set('value', value)
	etree.SubElement(elem, 'psNames')
	extranames_elem = etree.SubElement(elem, 'extraNames')
	for name in font.extra_names:
		sub_elem = etree.SubElement(extranames_elem, 'psName')
		sub_elem.set('name', name)

def add_COLR(font, parent):
	elem = etree.SubElement(parent, 'COLR')
	version_elem = etree.SubElement(elem, 'version')
	version_elem.set('value', '0')
	for glyph_name, layers in font.color_layers.items():
		colorglyph_elem = etree.SubElement(elem, 'ColorGlyph')
		colorglyph_elem.set('name', glyph_name)
		for id, name in layers:
			layer_elem = etree.SubElement(colorglyph_elem, 'layer')
			layer_elem.set('colorID', str(id))
			layer_elem.set('name', name)

def add_GDEF(font, parent):
	elem = etree.SubElement(parent, 'GDEF')
	add_Version('0x00010002', elem) # must be this for MarkGlyphSetsDef to work
	add_GlyphClassDef(font, elem)
	add_LigCaretList(font, elem)
	add_MarkAttachClassDef(font, elem)
	add_MarkGlyphSetsDef(font, elem)

def add_GlyphClassDef(font, parent):
	if len(font.glyph_to_class) > 0:
		elem = etree.SubElement(parent, 'GlyphClassDef')
		for glyph, cl in font.glyph_to_class.items():
			sub_elem = etree.SubElement(elem, 'ClassDef')
			sub_elem.set('glyph', glyph)
			sub_elem.set('class', str(cl))

def add_LigCaretList(font, parent):
	elem = etree.SubElement(parent, 'LigCaretList')
	etree.SubElement(elem, 'Coverage')

def add_MarkAttachClassDef(font, parent):
	elem = etree.SubElement(parent, 'MarkAttachClassDef')
	for glyph, cl in font.mark_to_class.items():
		sub_elem = etree.SubElement(elem, 'ClassDef')
		sub_elem.set('glyph', glyph)
		sub_elem.set('class', str(cl))

def add_MarkGlyphSetsDef(font, parent):
	if len(font.index_to_glyphs) > 0:
		elem = etree.SubElement(parent, 'MarkGlyphSetsDef')
		format_elem = etree.SubElement(elem, 'MarkSetTableFormat')
		format_elem.set('value', '1')
		for index in range(len(font.index_to_glyphs.items())):
			glyphs = font.index_to_glyphs[index]
			coverage_elem = etree.SubElement(elem, 'Coverage')
			coverage_elem.set('index', str(index))
			for glyph in glyphs:
				glyph_elem = etree.SubElement(coverage_elem, 'Glyph')
				glyph_elem.set('value', glyph)

def add_glyf(font, parent):
	glyf_elem = etree.SubElement(parent, 'glyf')
	for name in sorted(font.glyphs):
		glyph_elem = etree.SubElement(glyf_elem, 'TTGlyph')
		glyph_elem.set('name', name)
		if name in font.xmin:
			glyph_elem.set('xMin', str(font.xmin[name]))
		if name in font.ymin:
			glyph_elem.set('yMin', str(font.ymin[name]))
		if name in font.xmax:
			glyph_elem.set('xMax', str(font.xmax[name]))
		if name in font.ymax:
			glyph_elem.set('yMax', str(font.ymax[name]))
		for contour in font.contours[name]:
			contour_elem = etree.SubElement(glyph_elem, 'contour')
			for pt in contour:
				pt_elem = etree.SubElement(contour_elem, 'pt')
				pt_elem.set('x', pt[0])
				pt_elem.set('y', pt[1])
				pt_elem.set('on', pt[2])
		if len(font.contours[name]) > 0:
			instruction_elem = etree.SubElement(glyph_elem, 'instructions')
			for assembly in font.assemblies[name]:
				assembly_elem = etree.SubElement(instruction_elem, 'assembly')
				assembly_elem.text = assembly
		for component in font.components[name]:
			component_elem = etree.SubElement(glyph_elem, 'component')
			component_elem.set('glyphName', component['glyphName'])
			component_elem.set('x', component['x'])
			component_elem.set('y', component['y'])
			if 'scale' in component:
				component_elem.set('scale', component['scale'])
			if 'scalex' in component:
				component_elem.set('scalex', component['scalex'])
			if 'scale01' in component:
				component_elem.set('scale01', component['scale01'])
			if 'scale10' in component:
				component_elem.set('scale10', component['scale10'])
			if 'scaley' in component:
				component_elem.set('scaley', component['scaley'])
			component_elem.set('flags', component['flags'])

def add_version(version, parent):
	elem = etree.SubElement(parent, 'version')
	elem.set('value', version)

def add_Version(version, parent):
	elem = etree.SubElement(parent, 'Version')
	elem.set('value', version)

def add_ScriptList(script, features, parent):
	list_elem = etree.SubElement(parent, 'ScriptList')
	record_elem = etree.SubElement(list_elem, 'ScriptRecord')
	record_elem.set('index', '0')
	tag_elem = etree.SubElement(record_elem, 'ScriptTag')
	tag_elem.set('value', script)
	script_elem = etree.SubElement(record_elem, 'Script')
	lang_elem = etree.SubElement(script_elem, 'DefaultLangSys')
	req_elem = etree.SubElement(lang_elem, 'ReqFeatureIndex')
	req_elem.set('value', '65535')
	for index, feature in enumerate(features):
		index_elem = etree.SubElement(lang_elem, 'FeatureIndex')
		index_elem.set('index', str(index))
		index_elem.set('value', str(index))

def add_FeatureList(features, parent):
	list_elem = etree.SubElement(parent, 'FeatureList')
	for index, feature in enumerate(features):
		record_elem = etree.SubElement(list_elem, 'FeatureRecord')
		record_elem.set('index', str(index))
		tag_elem = etree.SubElement(record_elem, 'FeatureTag')
		tag_elem.set('value', feature.tag)
		feature_elem = etree.SubElement(record_elem, 'Feature')
		for index, lookahead_index in enumerate(feature.lookup_indexes):
			index_elem = etree.SubElement(feature_elem, 'LookupListIndex')
			index_elem.set('index', str(index))
			index_elem.set('value', str(lookahead_index))

def add_coverages(coverages, elem, name):
	for i, cov in enumerate(coverages):
		cov_elem = etree.SubElement(elem, name)
		cov_elem.set('index', str(i))
		for glyph in cov:
			glyph_elem = etree.SubElement(cov_elem, 'Glyph')
			glyph_elem.set('value', glyph)

def add_coverage(coverage, elem):
	cov_elem = etree.SubElement(elem, 'Coverage')
	for glyph in coverage:
		glyph_elem = etree.SubElement(cov_elem, 'Glyph')
		glyph_elem.set('value', glyph)

def add_filter_set(filter_set, elem):
	sub_elem = etree.SubElement(elem, 'MarkFilteringSet')
	sub_elem.set('value', str(filter_set))

# Type 1

def add_single_subst1(lookup, elem):
	sub_elem = etree.SubElement(elem, 'SingleSubst')
	sub_elem.set('index', '0')
	add_single_subst_common(lookup, sub_elem)

def add_single_subst_ext(lookup, elem):
	sub_elem = etree.SubElement(elem, 'ExtensionSubst')
	sub_elem.set('index', '0')
	sub_elem.set('Format', '1')
	type_elem = etree.SubElement(sub_elem, 'ExtensionLookupType')
	type_elem.set('value', '1')
	singlesubst_elem = etree.SubElement(sub_elem, 'SingleSubst')
	add_single_subst_common(lookup, singlesubst_elem)

def add_single_subst_common(lookup, elem):
	for sub in lookup.substitutions:
		subst_elem = etree.SubElement(elem, 'Substitution')
		subst_elem.set('in', sub.input)
		subst_elem.set('out', sub.output)

# Type 2

def add_mult_subst(lookup, elem):
	sub_elem = etree.SubElement(elem, 'MultipleSubst')
	sub_elem.set('index', '0')
	add_mult_subst_common(lookup, sub_elem)

def add_mult_subst_ext(lookup, elem):
	sub_elem = etree.SubElement(elem, 'ExtensionSubst')
	sub_elem.set('index', '0')
	sub_elem.set('Format', '1')
	type_elem = etree.SubElement(sub_elem, 'ExtensionLookupType')
	type_elem.set('value', '2')
	multsubst_elem = etree.SubElement(sub_elem, 'MultipleSubst')
	add_mult_subst_common(lookup, multsubst_elem)

def add_mult_subst_common(lookup, elem):
	for sub in lookup.substitutions:
		subst_elem = etree.SubElement(elem, 'Substitution')
		subst_elem.set('in', sub.input)
		subst_elem.set('out', ','.join(sub.outputs))

# Type 4

def add_ligature_subst(lookup, elem):
	sub_elem = etree.SubElement(elem, 'LigatureSubst')
	sub_elem.set('index', '0')
	add_ligature_subst_common(lookup, sub_elem)

def add_ligature_subst_ext(lookup, elem):
	sub_elem = etree.SubElement(elem, 'ExtensionSubst')
	sub_elem.set('index', '0')
	sub_elem.set('Format', '1')
	type_elem = etree.SubElement(sub_elem, 'ExtensionLookupType')
	type_elem.set('value', '4')
	ligsubst_elem = etree.SubElement(sub_elem, 'LigatureSubst')
	add_ligature_subst_common(lookup, ligsubst_elem)

def add_ligature_subst_common(lookup, elem):
	first_to_subs = defaultdict(list)
	for sub in lookup.substitutions:
		first_to_subs[sub.inputs[0]].append(sub)
	for first in sorted(first_to_subs):
		subs = first_to_subs[first]
		set_elem = etree.SubElement(elem, 'LigatureSet')
		set_elem.set('glyph', first)
		for sub in subs:
			if sub.inputs[0] == first:
				lig_elem = etree.SubElement(set_elem, 'Ligature')
				lig_elem.set('components', ','.join(sub.inputs[1:]))
				lig_elem.set('glyph', sub.output)

# Type 6, Format 3

def add_chain_subst(lookup, elem):
	for index, sub in enumerate(lookup.substitutions):
		sub_elem = etree.SubElement(elem, 'ChainContextSubst')
		sub_elem.set('index', str(index))
		sub_elem.set('Format', '3')
		add_chain_subst_common(sub, sub_elem)

def add_chain_subst_ext(lookup, elem):
	for index, sub in enumerate(lookup.substitutions):
		sub_elem = etree.SubElement(elem, 'ExtensionSubst')
		sub_elem.set('index', str(index))
		sub_elem.set('Format', '1')
		type_elem = etree.SubElement(sub_elem, 'ExtensionLookupType')
		type_elem.set('value', '6')
		chainsubst_elem = etree.SubElement(sub_elem, 'ChainContextSubst')
		chainsubst_elem.set('Format', '3')
		add_chain_subst_common(sub, chainsubst_elem)

def add_chain_subst_common(sub, elem):
		add_coverages(sub.lefts, elem, 'BacktrackCoverage')
		add_coverages(sub.inputs, elem, 'InputCoverage')
		add_coverages(sub.rights, elem, 'LookAheadCoverage')
		for index, (seq, ref) in enumerate(sub.refs):
			rec_elem = etree.SubElement(elem, 'SubstLookupRecord')
			rec_elem.set('index', str(index))
			seq_elem = etree.SubElement(rec_elem, 'SequenceIndex')
			seq_elem.set('value', str(seq))
			seq_elem = etree.SubElement(rec_elem, 'LookupListIndex')
			seq_elem.set('value', str(ref))

# Type 8

def add_reverse_subst(lookup, elem):
	for index, sub in enumerate(lookup.substitutions):
		sub_elem = etree.SubElement(elem, 'ReverseChainSingleSubst')
		sub_elem.set('index', str(index))
		sub_elem.set('Format', '1')
		add_reverse_subst_common(sub, sub_elem)

def add_reverse_subst_ext(lookup, elem):
	for index, sub in enumerate(lookup.substitutions):
		sub_elem = etree.SubElement(elem, 'ExtensionSubst')
		sub_elem.set('index', str(index))
		sub_elem.set('Format', '1')
		type_elem = etree.SubElement(sub_elem, 'ExtensionLookupType')
		type_elem.set('value', '8')
		revsubst_elem = etree.SubElement(sub_elem, 'ReverseChainSingleSubst')
		revsubst_elem.set('Format', '1')
		add_reverse_subst_common(sub, revsubst_elem)

def add_reverse_subst_common(sub, elem):
	add_coverages(sub.lefts, elem, 'BacktrackCoverage')
	add_coverage(sub.inputs, elem)
	add_coverages(sub.rights, elem, 'LookAheadCoverage')
	for index, value in enumerate(sub.outputs):
		subst_elem = etree.SubElement(elem, 'Substitute') 
		subst_elem.set('index', str(index))
		subst_elem.set('value', value)

def flag(lookup):
	flag = 0
	if lookup.reverse:
		flag |= 1
	if lookup.ignore_base_glyphs:
		flag |= 2
	if lookup.ignore_ligatures:
		flag |= 4
	if lookup.ignore_marks:
		flag |= 8
	if lookup.filter_set is not None:
		flag |= 16
	flag |= 256 * lookup.mark_class
	return flag

def add_GSUB_lookups(lookups, parent):
	list_elem = etree.SubElement(parent, 'LookupList')
	for lookup in lookups:
		lookup_elem = etree.SubElement(list_elem, 'Lookup')
		lookup_elem.set('index', str(lookup.index))
		type_elem = etree.SubElement(lookup_elem, 'LookupType')
		flag_elem = etree.SubElement(lookup_elem, 'LookupFlag')
		flag_elem.set('value', str(flag(lookup)))
		match lookup.typ:
			case '1':
				add_single_subst1(lookup, lookup_elem)
				type_elem.set('value', '1')
			case '2':
				add_mult_subst(lookup, lookup_elem)
				type_elem.set('value', '2')
			case '4':
				add_ligature_subst(lookup, lookup_elem)
				type_elem.set('value', '4')
			case '6.3':
				add_chain_subst(lookup, lookup_elem)
				type_elem.set('value', '6')
			case '8':
				add_reverse_subst(lookup, lookup_elem)
				type_elem.set('value', '8')
			case '7/1':
				type_elem.set('value', '7')
				add_single_subst_ext(lookup, lookup_elem)
			case '7/2':
				type_elem.set('value', '7')
				add_mult_subst_ext(lookup, lookup_elem)
			case '7/4':
				type_elem.set('value', '7')
				add_ligature_subst_ext(lookup, lookup_elem)
			case '7/6.3':
				type_elem.set('value', '7')
				add_chain_subst_ext(lookup, lookup_elem)
			case '7/8':
				type_elem.set('value', '7')
				add_reverse_subst_ext(lookup, lookup_elem)
		if lookup.filter_set is not None:
			add_filter_set(lookup.filter_set, lookup_elem) 

def add_GSUB(font, parent):
	if len(font.GSUB_lookup_list) > 0:
		elem = etree.SubElement(parent, 'GSUB')
		add_Version('0x00010000', elem)
		add_ScriptList(font.script, font.GSUB_features, elem)
		add_FeatureList(font.GSUB_features, elem)
		add_GSUB_lookups(font.GSUB_lookup_list, elem)

def add_single_pos(posit, elem):
	sub_elem = etree.SubElement(elem, 'ExtensionPos')
	sub_elem.set('index', '0')
	sub_elem.set('Format', '1')
	type_elem = etree.SubElement(sub_elem, 'ExtensionLookupType')
	type_elem.set('value', '1')
	singlepos_elem = etree.SubElement(sub_elem, 'SinglePos')
	singlepos_elem.set('Format', '2')
	coverage_elem = etree.SubElement(singlepos_elem, 'Coverage')
	for adj in posit.adjustments:
		glyph_elem = etree.SubElement(coverage_elem, 'Glyph')
		glyph_elem.set('value', adj['glyph'])
	format_elem = etree.SubElement(singlepos_elem, 'ValueFormat')
	format_elem.set('value', posit.form)
	for index, adj in enumerate(posit.adjustments):
		value_elem = etree.SubElement(singlepos_elem, 'Value')
		value_elem.set('index', str(index))
		if posit.form == '1':
			value_elem.set('XPlacement', str(adj['placement']['XPlacement']))
		else:
			value_elem.set('YPlacement', str(adj['placement']['YPlacement']))

def add_mark_base_pos(posit, elem):
	n_classes = len({m['class'] for m in posit.marks})
	sub_elem = etree.SubElement(elem, 'ExtensionPos')
	sub_elem.set('index', '0')
	sub_elem.set('Format', '1')
	type_elem = etree.SubElement(sub_elem, 'ExtensionLookupType')
	type_elem.set('value', '4')
	markbase_elem = etree.SubElement(sub_elem, 'MarkBasePos')
	markbase_elem.set('Format', '1')
	markcov_elem = etree.SubElement(markbase_elem, 'MarkCoverage')
	for mark in posit.marks:
		glyph_elem = etree.SubElement(markcov_elem, 'Glyph')
		glyph_elem.set('value', mark['glyph'])
	basecov_elem = etree.SubElement(markbase_elem, 'BaseCoverage')
	for base in posit.bases:
		glyph_elem = etree.SubElement(basecov_elem, 'Glyph')
		glyph_elem.set('value', base['glyph'])
	markarray_elem = etree.SubElement(markbase_elem, 'MarkArray')
	for index, mark in enumerate(posit.marks):
		markrecord_elem = etree.SubElement(markarray_elem, 'MarkRecord')
		markrecord_elem.set('index', str(index))
		class_elem = etree.SubElement(markrecord_elem, 'Class')
		class_elem.set('value', str(mark['class']))
		anchor_elem = etree.SubElement(markrecord_elem, 'MarkAnchor')
		anchor_elem.set('Format', '1')
		x_elem = etree.SubElement(anchor_elem, 'XCoordinate')
		x_elem.set('value', str(mark['x']))
		y_elem = etree.SubElement(anchor_elem, 'YCoordinate')
		y_elem.set('value', str(mark['y']))
	basearray_elem = etree.SubElement(markbase_elem, 'BaseArray')
	for index, base in enumerate(posit.bases):
		baserecord_elem = etree.SubElement(basearray_elem, 'BaseRecord')
		baserecord_elem.set('index', str(index))
		for cl in range(n_classes):
			anchor_elem = etree.SubElement(baserecord_elem, 'BaseAnchor')
			anchor_elem.set('index', str(cl))
			anchor_elem.set('Format', '1')
			x_elem = etree.SubElement(anchor_elem, 'XCoordinate')
			x_elem.set('value', str(base['coordinates'][cl]['x']))
			y_elem = etree.SubElement(anchor_elem, 'YCoordinate')
			y_elem.set('value', str(base['coordinates'][cl]['y']))

def add_mark_mark_pos(posit, elem):
	n_classes = len({m['class'] for m in posit.marks1})
	sub_elem = etree.SubElement(elem, 'ExtensionPos')
	sub_elem.set('index', '0')
	sub_elem.set('Format', '1')
	type_elem = etree.SubElement(sub_elem, 'ExtensionLookupType')
	type_elem.set('value', '6')
	markmark_elem = etree.SubElement(sub_elem, 'MarkMarkPos')
	markmark_elem.set('Format', '1')
	markcov_elem = etree.SubElement(markmark_elem, 'Mark1Coverage')
	for mark in posit.marks1:
		glyph_elem = etree.SubElement(markcov_elem, 'Glyph')
		glyph_elem.set('value', mark['glyph'])
	markcov_elem = etree.SubElement(markmark_elem, 'Mark2Coverage')
	for mark in posit.marks2:
		glyph_elem = etree.SubElement(markcov_elem, 'Glyph')
		glyph_elem.set('value', mark['glyph'])
	markarray_elem = etree.SubElement(markmark_elem, 'Mark1Array')
	for index, mark in enumerate(posit.marks1):
		markrecord_elem = etree.SubElement(markarray_elem, 'MarkRecord')
		markrecord_elem.set('index', str(index))
		class_elem = etree.SubElement(markrecord_elem, 'Class')
		class_elem.set('value', str(mark['class']))
		anchor_elem = etree.SubElement(markrecord_elem, 'MarkAnchor')
		anchor_elem.set('Format', '1')
		x_elem = etree.SubElement(anchor_elem, 'XCoordinate')
		x_elem.set('value', str(mark['x']))
		y_elem = etree.SubElement(anchor_elem, 'YCoordinate')
		y_elem.set('value', str(mark['y']))
	markarray_elem = etree.SubElement(markmark_elem, 'Mark2Array')
	for index, mark in enumerate(posit.marks2):
		markrecord_elem = etree.SubElement(markarray_elem, 'Mark2Record')
		markrecord_elem.set('index', str(index))
		for cl in range(n_classes):
			anchor_elem = etree.SubElement(markrecord_elem, 'Mark2Anchor')
			anchor_elem.set('index', str(cl))
			anchor_elem.set('Format', '1')
			x_elem = etree.SubElement(anchor_elem, 'XCoordinate')
			x_elem.set('value', str(mark['coordinates'][cl]['x']))
			y_elem = etree.SubElement(anchor_elem, 'YCoordinate')
			y_elem.set('value', str(mark['coordinates'][cl]['y']))

def add_chain_pos(lookup, elem):
	for index, posit in enumerate(lookup.positionings):
		sub_elem = etree.SubElement(elem, 'ExtensionPos')
		sub_elem.set('index', str(index))
		sub_elem.set('Format', '1')
		type_elem = etree.SubElement(sub_elem, 'ExtensionLookupType')
		type_elem.set('value', '8')
		chain_elem = etree.SubElement(sub_elem, 'ChainContextPos')
		chain_elem.set('Format', '3')
		for left_index, lefts in enumerate(posit.left):
			left_elem = etree.SubElement(chain_elem, 'BacktrackCoverage')
			left_elem.set('index', str(left_index))
			for left in lefts:
				glyph_elem = etree.SubElement(left_elem, 'Glyph')
				glyph_elem.set('value', left)
		input_elem = etree.SubElement(chain_elem, 'InputCoverage')
		input_elem.set('index', str(0))
		for inp in posit.input:
			glyph_elem = etree.SubElement(input_elem, 'Glyph')
			glyph_elem.set('value', inp)
		for right_index, rights in enumerate(posit.right):
			right_elem = etree.SubElement(chain_elem, 'LookAheadCoverage')
			right_elem.set('index', str(right_elem))
			for right in rights:
				glyph_elem = etree.SubElement(right_elem, 'Glyph')
				glyph_elem.set('value', right)
		if posit.output is not None:
			lookup_elem = etree.SubElement(chain_elem, 'PosLookupRecord')
			lookup_elem.set('index', '0')
			seq_elem = etree.SubElement(lookup_elem, 'SequenceIndex')
			seq_elem.set('value', '0')
			index_elem = etree.SubElement(lookup_elem, 'LookupListIndex')
			index_elem.set('value', str(posit.output))

def add_GPOS_lookups(lookups, parent):
	list_elem = etree.SubElement(parent, 'LookupList')
	for lookup in lookups:
		lookup_elem = etree.SubElement(list_elem, 'Lookup')
		lookup_elem.set('index', str(lookup.index))
		type_elem = etree.SubElement(lookup_elem, 'LookupType')
		type_elem.set('value', '9')
		flag_elem = etree.SubElement(lookup_elem, 'LookupFlag')
		flag_elem.set('value', str(flag(lookup)))
		match lookup.typ:
			case '9/1': 
				add_single_pos(lookup.positionings[0], lookup_elem)
			case '9/4': 
				add_mark_base_pos(lookup.positionings[0], lookup_elem)
			case '9/6': 
				add_mark_mark_pos(lookup.positionings[0], lookup_elem)
			case '9/8': 
				add_chain_pos(lookup, lookup_elem)
		if lookup.filter_set is not None:
			add_filter_set(lookup.filter_set, lookup_elem) 

def add_GPOS(font, parent):
	if len(font.GPOS_lookup_list) > 0:
		elem = etree.SubElement(parent, 'GPOS')
		add_Version('0x00010000', elem)
		add_ScriptList(font.script, font.GPOS_features, elem)
		add_FeatureList(font.GPOS_features, elem)
		add_GPOS_lookups(font.GPOS_lookup_list, elem)

def add_loca(parent):
	etree.SubElement(parent, 'loca')

def add_DSIG(parent):
	elem = etree.SubElement(parent, 'DSIG')
	sub_elem = etree.SubElement(elem, 'tableHeader')
	sub_elem.set('flag', '0x1')
	sub_elem.set('numSigs', '0')
	sub_elem.set('version', '1')

def write_ttx(font, filename):
	root = etree.Element("ttFont")
	root.set('sfntVersion', '\\x00\\x01\\x00\\x00')
	root.set('ttLibVersion', '4.33')
	add_GlyphOrder(font, root)
	add_properties(font, 'head', root)
	add_properties(font, 'hhea', root)
	add_properties(font, 'maxp', root)
	add_properties(font, 'OS_2', root)
	add_hmtx(font, root)
	add_cmap(font, root)
	add_loca(root)
	add_glyf(font, root)
	add_name(font, root)
	add_post(font, root)
	# add_COLR(font, root)
	# add_CPAL(font, root)
	add_GDEF(font, root)
	add_GPOS(font, root)
	add_GSUB(font, root)
	add_properties(font, 'vhea', root)
	add_vmtx(font, root)
	add_DSIG(root)
	doc = etree.ElementTree(root)
	etree.indent(doc, space='  ', level=0)
	doc.write(filename, xml_declaration=True, encoding='utf-8')
