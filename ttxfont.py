import os
from lxml import etree
from datetime import datetime

import re
from ttxtables import read_basic_properties, read_post

CONTROL_GLYPH_RE = re.compile(
    r'^(?:'
    r'GB\d+(?:_\d+)?|'
    r'QB\d+|Qi|Qf|cleanup|trg\d+|m\d+|o\d+|'
    r'c\d+[A-Za-z0-9]+|r\d+[A-Za-z0-9]+|et\d+|tsh\d+|'
    r'eh\d+|ev\d+|im\d+'
    r')$'
)


def equiv(elem1, elem2):
	if isinstance(elem1, list):
		return elem2 in elem1
	elif isinstance(elem2, list):
		return elem1 in elem2
	else:
		return elem1 == elem2

def equiv_list(l1, l2):
	return all([equiv(pair[0], pair[1]) for pair in zip(l1, l2)])

def is_suffix_of(l1, l2):
	return len(l1) <= len(l2) and equiv_list(l1, l2[-len(l1):])
	
def is_prefix_of(l1, l2):
	return len(l1) <= len(l2) and equiv_list(l1, l2[:len(l1)])

def filter_glyph(glyph, font, lookup):

	if glyph in ("vj","hj"):
		print("filter_glyph", glyph, "class", font.glyph_to_class.get(glyph), "ignore_marks", lookup.ignore_marks)

	# Check if glyph exists in classification system
	if glyph not in font.glyph_to_class:
		return True  # Allow unclassified glyphs by default
	
	if lookup.ignore_base_glyphs and font.glyph_to_class[glyph] == BASE_GLYPH:
		return False
	if lookup.ignore_ligatures and font.glyph_to_class[glyph] == LIGATURE_GLYPH:
		return False
	if lookup.ignore_marks and font.glyph_to_class[glyph] == MARK_GLYPH:
		return False
	if lookup.mark_class != 0 and \
			(glyph not in font.mark_to_class or \
				font.mark_to_class[glyph] != lookup.mark_class):
		return False
	if lookup.filter_set is not None and \
			lookup.filter_set in font.index_to_glyphs and \
			glyph not in font.index_to_glyphs[lookup.filter_set]:
		return False
	return True

def filter_list(l, filter):
	return [token for token in l if filter(token)]

def first_filtered_left(l, filter):
	for i in range(len(l)):
		if filter(l[i]):
			return i
	return -1

def first_filtered_right(l, filter):
	for i in reversed(range(len(l))):
		if filter(l[i]):
			return i
	return -1

# Type 1
class SingleSubstitution1:
	def __init__(self, input, output):
		self.input = input
		self.output = output

	def length(self):
		return 1

	def recur(self, tokens, pos, font, lookup):
		return None

	def applicable(self, tokens, pos, font, lookup):
		return pos < len(tokens) and tokens[pos] == self.input

	def apply(self, tokens, pos, font, lookup):
		tokens = tokens.copy()
		tokens[pos] = self.output
		return tokens, 1, [pos]

	def __str__(self):
		return self.input + ' -> ' + self.output

# Type 2
class MultSubstitution:
	def __init__(self, input, outputs):
		self.input = input
		self.outputs = outputs

	def length(self):
		return 1

	def recur(self, tokens, pos, font, lookup):
		return None

	def applicable(self, tokens, pos, font, lookup):
		return pos < len(tokens) and tokens[pos] == self.input

	def apply(self, tokens, pos, font, lookup):
		tokens = tokens.copy()
		del tokens[pos]
		for token in reversed(self.outputs):
			tokens.insert(pos, token)
		return tokens, len(self.outputs), [pos]

	def __str__(self):
		return self.input + ' -> ' + ' '.join(self.outputs)

# Type 4
class LigSubstitution:
	def __init__(self, inputs, output):
		self.inputs = inputs
		self.output = output

	def length(self):
		return len(self.inputs)

	def recur(self, tokens, pos, font, lookup):
		return None

	def applicable(self, tokens, pos, font, lookup):
		return pos < len(tokens) and tokens[pos] == self.inputs[0] and \
			is_prefix_of(self.inputs[1:], \
				filter_list(tokens[pos+1:], lambda t : filter_glyph(t, font, lookup)))

	def apply(self, tokens, pos, font, lookup):
		tokens = tokens.copy()
		posses = [pos]
		i = pos+1
		while len(posses) < len(self.inputs):
			if filter_glyph(tokens[i], font, lookup):
				posses.append(i)
			i += 1
		for i in reversed(posses):
			del tokens[i]
		tokens.insert(pos, self.output)
		return tokens, 1, posses

	def __str__(self):
		return ' '.join(self.inputs) + ' -> ' + self.output

# Type 6, Format 3
class ChainSubstitution3:
	def __init__(self, lefts, inputs, rights, refs):
		self.lefts = lefts
		self.inputs = inputs
		self.rights = rights
		self.refs = refs

	def length(self):
		return len(self.lefts) + len(self.inputs) + len(self.rights)

	def recur(self, tokens, pos, font, lookup):
		posses = self.filtered_input_positions(tokens, pos, font, lookup)
		return [(posses[p], index) for (p, index) in self.refs]

	def applicable(self, tokens, pos, font, lookup):
		if False:
			if len(tokens) > 2 and tokens[1] == 'ch0' and lookup.index == 99 and pos == 1:
				print(self.left)
				print(self.input + self.right)
				print(filter_glyph(tokens[pos], font, lookup))
				print(tokens[:pos])
				print(filter_list(tokens[:pos], lambda t : filter_glyph(t, font, lookup)))
				print(tokens[pos:])
				print(filter_list(tokens[pos:], lambda t : filter_glyph(t, font, lookup)))
		return pos < len(tokens) and \
			equiv(tokens[pos], self.inputs[0]) and \
			is_suffix_of(self.lefts, filter_list(tokens[:pos], \
				lambda t : filter_glyph(t, font, lookup))) and \
			is_prefix_of(self.inputs[1:] + self.rights, filter_list(tokens[pos+1:], \
				lambda t : filter_glyph(t, font, lookup)))

	def apply(self, tokens, pos, font, lookup):
		# ChainSubstitution3 should not directly modify tokens
		# Instead, it triggers recursive lookups which handle the actual substitutions
		posses = self.filtered_input_positions(tokens, pos, font, lookup)
		return tokens, 0, posses

	def filtered_input_positions(self, tokens, pos, font, lookup):
		posses = [pos]
		for p in range(pos+1, len(tokens)):
			if filter_glyph(tokens[p], font, lookup):
				posses.append(p)
		return posses[:len(self.inputs)]

	def __str__(self):
		lefts = ' '.join([l if isinstance(l, str) else '/'.join(l) for l in self.lefts])
		rights = ' '.join([l if isinstance(l, str) else '/'.join(l) for l in self.rights])
		inputs = ' '.join([l if isinstance(l, str) else '/'.join(l) for l in self.inputs])
		refs = ' '.join([str(index) + '->' + str(lookup) for (index, lookup) in self.refs])
		return lefts + '|' + inputs + '|' + rights + ' ---> ' + refs

# Type 8
class ReverseSubstitution:
	def __init__(self, lefts, inputs, rights, outputs):
		self.lefts = lefts
		self.inputs = inputs
		self.rights = rights
		self.outputs = outputs

	def length(self):
		return len(self.lefts) + 1 + len(self.rights)

	def recur(self, tokens, pos, font, lookup):
		return None

	def applicable(self, tokens, pos, font, lookup):
		return False

	def apply(self, tokens, pos, font, lookup):
		print("Type 8 not implemented")
		exit(0)

	def __str__(self):
		return ' '.join(self.inputs) + ' -> ' + self.output

class GSUB_Lookup:
	def __init__(self, index, typ):
		self.index = index
		self.typ = typ
		self.reverse = (typ == '7/8' or typ == '8')
		self.ignore_base_glyphs = False
		self.ignore_ligatures = False
		self.ignore_marks = False
		self.mark_class = 0
		self.filter_set = None
		self.substitutions = []

	def add(self, substitution):
		self.substitutions.append(substitution)

	# Normally one shouldn't use this. The textual order should be the order
	# in which rules are attempted.
	def reorder(self):
		self.substitutions = sorted(self.substitutions, key=lambda s : s.length())

	def apply(self, tokens, font):
		pos = 0
		applications = []
		while pos < len(tokens):
			tokens, application, jump = self.apply_at(tokens, pos, font)
			if application is not None:
				applications.append(application)
				pos += jump
			else:
				pos += 1
		return tokens, applications

	def apply_at(self, tokens, pos, font):
		for substitution in sorted(self.substitutions, key=lambda s : -s.length()):
			if substitution.applicable(tokens, pos, font, self):
				recur = substitution.recur(tokens, pos, font, self)
				if recur is not None:
					if len(recur) > 0:
						posses = substitution.filtered_input_positions(tokens, pos, font, self)
						len_pre = len(tokens)
						application = {'index': str(self.index), 'posses': posses, 'rule': substitution, \
							'tokens': tokens}
						for pos2, recurred in recur:
							recur_lookup = font.GSUB_lookups[recurred]
							tokens, application_recur, _ = recur_lookup.apply_at(tokens, pos2, font)
							if application_recur is not None:
								application['index'] += '/' + application_recur['index']
						application['tokens'] = tokens
						len_post = len(tokens)
						jump = len_post-len_pre + 1
					else:
						application = {'index': str(self.index), 'posses': [pos], 'rule': substitution, \
							'tokens': tokens} 
						jump = 1
				else:
					tokens, jump, posses = substitution.apply(tokens, pos, font, self)
					application = {'index': str(self.index), 'posses': posses, 'rule': substitution, \
						'tokens': tokens}
				return tokens, application, jump
		return tokens, None, 0

	def __str__(self):
		s = 'GSUB LOOKUP ' + str(self.index)
		if self.ignore_base_glyphs:
			s += 'ignore_base_glyphs '
		if self.ignore_ligatures:
			s += 'ignore_ligatures '
		if self.ignore_marks:
			s += 'ignore_marks '
		if self.mark_class != 0:
			s += str(self.mark_class) + ' '
		if self.filter_set:
			s += str(self.filter_set)
		s += '\n'
		for sub in self.substitutions:
			s += '\n' + sub
		return s

# Type 1
class SingleAdjustment:
    def __init__(self, form, adjustments):
        self.form = form  # value_format bitmask
        self.adjustments = adjustments

    def length(self):
        return 1

    def recur(self):
        return None

    def applicable(self, tokens, pos, font, lookup):
        if pos < 0 or pos >= len(tokens):
            return False
        for adj in self.adjustments:
            if adj.get('glyph') == tokens[pos]:
                return True
        return False

    def apply(self, tokens, positionings, pos, font, lookup):
        positionings = [ (d.copy() if isinstance(d, dict) else {}) for d in positionings ]
        if pos < 0 or pos >= len(positionings):
            return positionings

        for adjs in self.adjustments:
            if adjs.get('glyph') == tokens[pos]:
                placement = adjs.get('placement', {})
                if positionings[pos] is None:
                    positionings[pos] = {}
                # store offsets separately from advances
                if 'XPlacement' in placement:
                    positionings[pos]['XOffset'] = placement['XPlacement']
                if 'YPlacement' in placement:
                    positionings[pos]['YOffset'] = placement['YPlacement']
                if 'XAdvance' in placement:
                    positionings[pos]['XAdvance'] = placement['XAdvance']
                if 'YAdvance' in placement:
                    positionings[pos]['YAdvance'] = placement['YAdvance']
        return positionings

    def __str__(self):
        return ' '.join([str((g,a)) for (g,a) in self.adjustments])


# Type 4
class MarkBaseAttachment:
    def __init__(self, marks, bases):
        self.marks = marks
        self.bases = bases

    def length(self):
        return 2

    def recur(self):
        return None

    def applicable(self, tokens, pos, font, lookup):
        mark_index = self.mark(tokens, pos, font, lookup)
        pos_base, base_index = self.base(tokens, pos, font, lookup)
        return mark_index >= 0 and base_index >= 0

    def apply(self, tokens, positionings, pos, font, lookup):
        positionings = [ (d.copy() if isinstance(d, dict) else {}) for d in positionings ]

        mark_index = self.mark(tokens, pos, font, lookup)
        pos_base, base_index = self.base(tokens, pos, font, lookup)
        if mark_index < 0 or pos_base < 0 or base_index < 0:
            return positionings

        mark = self.marks[mark_index]
        base = self.bases[base_index]
        cl = mark['class']

        if positionings[pos] is None:
            positionings[pos] = {}
        if positionings[pos_base] is None:
            positionings[pos_base] = {}

        coords = base.get('coordinates', {}).get(cl)
        if coords is None:
            return positionings

        # include base glyph's own current offset (if any)
        base_x = positionings[pos_base].get('XOffset', 0)
        base_y = positionings[pos_base].get('YOffset', 0)

        # mark anchor and base anchor -> mark offset
        if 'x' in coords and 'y' in coords and 'x' in mark and 'y' in mark:
            positionings[pos]['XOffset'] = (coords['x'] + base_x) - mark['x']
            positionings[pos]['YOffset'] = (coords['y'] + base_y) - mark['y']

        # marks typically have zero advance; you can enforce if desired:
        # positionings[pos]['XAdvance'] = 0
        return positionings

    def mark(self, tokens, pos, font, lookup):
        for index, mark in enumerate(self.marks):
            if mark['glyph'] == tokens[pos]:
                return index
        return -1

    def base(self, tokens, pos, font, lookup):
        for i in range(pos-1, -1, -1):
            tok = tokens[i]
            if not filter_glyph(tok, font, lookup):
                continue
            if font.glyph_to_class.get(tok) != BASE_GLYPH:
                continue
            for index, base in enumerate(self.bases):
                if base.get('glyph') == tok:
                    return i, index
        return -1, -1


# Type 6
class MarkMarkAttachment:
    def __init__(self, marks1, marks2):
        self.marks1 = marks1
        self.marks2 = marks2

    def length(self):
        return 2

    def recur(self):
        return None

    def applicable(self, tokens, pos, font, lookup):
        mark1_index = self.mark1(tokens, pos, font, lookup)
        pos_mark2, mark2_index = self.mark2(tokens, pos, font, lookup)
        return mark1_index >= 0 and mark2_index >= 0

    def apply(self, tokens, positionings, pos, font, lookup):
        positionings = [ (d.copy() if isinstance(d, dict) else {}) for d in positionings ]

        mark1_index = self.mark1(tokens, pos, font, lookup)
        pos_mark2, mark2_index = self.mark2(tokens, pos, font, lookup)
        if mark1_index < 0 or pos_mark2 < 0 or mark2_index < 0:
            return positionings

        mark1 = self.marks1[mark1_index]
        mark2 = self.marks2[mark2_index]
        cl = mark1.get('class')
        if cl is None:
            return positionings

        if positionings[pos] is None:
            positionings[pos] = {}
        if positionings[pos_mark2] is None:
            positionings[pos_mark2] = {}

        coords = mark2.get('coordinates', {}).get(cl)
        if coords is None:
            return positionings

        # include mark2's current offset (stacking!)
        m2x = positionings[pos_mark2].get('XOffset', 0)
        m2y = positionings[pos_mark2].get('YOffset', 0)

        if 'x' in coords and 'y' in coords and 'x' in mark1 and 'y' in mark1:
            positionings[pos]['XOffset'] = (coords['x'] + m2x) - mark1['x']
            positionings[pos]['YOffset'] = (coords['y'] + m2y) - mark1['y']

        # mark1 advance should be 0 in most fonts
        # positionings[pos]['XAdvance'] = 0
        return positionings

    def mark1(self, tokens, pos, font, lookup):
        for index, mark in enumerate(self.marks1):
            if mark['glyph'] == tokens[pos]:
                return index
        return -1

    def mark2(self, tokens, pos, font, lookup):
        for i in range(pos-1, -1, -1):
            tok = tokens[i]
            if not filter_glyph(tok, font, lookup):
                continue
            for index, mark in enumerate(self.marks2):
                if mark.get('glyph') == tok:
                    return i, index
        return -1, -1
    
    def __str__(self):
        return f'(1) {str(self.marks1)} (2) {str(self.marks2)}'

# Type 8
class ChainPos:
    def __init__(self, lefts, inputs, rights, records):
        self.lefts = lefts
        self.inputs = inputs
        self.rights = rights
        self.records = records  # list of (seq_index, lookup_index)

    def length(self):
        # not super meaningful; keep for compatibility
        return len(self.lefts) + len(self.inputs) + len(self.rights)

    def recur(self):
        # return list of (absolute_position, lookup_index) to apply
        return None  # handled by recur_at()

    def applicable(self, tokens, pos, font, lookup):
        # Must match first input coverage at current pos
        if pos < 0 or pos >= len(tokens):
            return False

        if len(self.inputs) == 0:
            return False

        def in_cov(tok, cov):
            return tok in cov

        if not in_cov(tokens[pos], self.inputs[0]):
            return False

        # Backtrack: self.lefts is list of coverages (each a list of glyph names)
        filtered_left = filter_list(tokens[:pos], lambda t: filter_glyph(t, font, lookup))
        if len(filtered_left) < len(self.lefts):
            return False
        # match suffix
        for i, cov in enumerate(reversed(self.lefts)):
            if filtered_left[-(i+1)] not in cov:
                return False

        # Lookahead: needs to match remaining inputs + rights after pos
        filtered_right = filter_list(tokens[pos+1:], lambda t: filter_glyph(t, font, lookup))

        need = []
        for cov in self.inputs[1:]:
            need.append(cov)
        for cov in self.rights:
            need.append(cov)

        if len(filtered_right) < len(need):
            return False

        for i, cov in enumerate(need):
            if filtered_right[i] not in cov:
                return False

        return True

    def recur_at(self, tokens, pos, font, lookup):
        # Determine absolute positions of the input sequence (filtered)
        # Input length = len(self.inputs)
        input_positions = [pos]
        i = pos + 1
        while i < len(tokens) and len(input_positions) < len(self.inputs):
            if filter_glyph(tokens[i], font, lookup):
                input_positions.append(i)
            i += 1

        if len(input_positions) < len(self.inputs):
            return []

        out = []
        for (seq_index, lookup_index) in self.records:
            if 0 <= seq_index < len(input_positions):
                out.append((input_positions[seq_index], lookup_index))
        return out

    def apply(self, tokens, positionings, pos, font, lookup):
        # ChainPos itself doesn't change; it triggers other lookups
        return positionings

    def __str__(self):
        return f'ChainPos records={self.records}'


class GPOS_Lookup:
	def __init__(self, index, typ):
		self.index = index
		self.typ = typ
		self.ignore_base_glyphs = False
		self.ignore_ligatures = False
		self.ignore_marks = False
		self.mark_class = 0
		self.filter_set = None
		self.positionings = []

	def add_positioning(self, positioning):
		self.positionings.append(positioning)

	# Normally one shouldn't use this. The textual order should be the order
	# in which rules are attempted.
	def reorder(self):
		self.positionings = sorted(self.positionings, key=lambda s : s.length())

	def apply(self, tokens, positionings, font):
		applications = []
		for pos in range(len(tokens)):
			positionings, application = self.apply_at(tokens, positionings, pos, font)
			if application is not None:
				applications.append(application)
		return positionings, applications

	def apply_at(self, tokens, positionings, pos, font):
    # IMPORTANT: keep authoring order; do NOT sort by length.
		for posit in self.positionings:
			if posit.applicable(tokens, pos, font, self):
				# Special handling: ChainPos triggers other lookups at specific positions
				if isinstance(posit, ChainPos):
					application = {'index': str(self.index), 'posses': [pos], 'rule': posit,
								'tokens': tokens, 'positionings': positionings}
					for pos2, lookup_index in posit.recur_at(tokens, pos, font, self):
						if lookup_index in font.GPOS_lookups:
							recur_lookup = font.GPOS_lookups[lookup_index]
							positionings, app2 = recur_lookup.apply_at(tokens, positionings, pos2, font)
							if app2 is not None:
								application['index'] += '/' + app2.get('index', str(lookup_index))
					application['positionings'] = positionings
					return positionings, application

				# Normal positioning
				recur = posit.recur()
				if recur is not None:
					if recur in font.GPOS_lookups:
						recur_lookup = font.GPOS_lookups[recur]
						positionings, application = recur_lookup.apply_at(tokens, positionings, pos, font)
						if application is not None:
							application['index'] = str(self.index) + '/' + application.get('index', str(recur))
						else:
							application = {'index': str(self.index) + '/' + str(recur),
										'posses': [pos],
										'rule': posit,
										'tokens': tokens,
										'positionings': positionings}
						return positionings, application
					else:
						continue
				else:
					positionings = posit.apply(tokens, positionings, pos, font, self)
					application = {'index': str(self.index),
								'posses': [pos],
								'rule': posit,
								'tokens': tokens,
								'positionings': positionings}
					return positionings, application

		return positionings, None


class Feature:
	def __init__(self, tag):
		self.tag = tag
		self.lookup_indexes = []

	def add_lookup_index(self, index):
		self.lookup_indexes.append(index)

	def __str__(self):
		return "FEATURE " + self.tag + ' ' + str(self.lookup_indexes)

# Glyph classes (cf. glyph_to_class)
BASE_GLYPH = 1
LIGATURE_GLYPH = 2
MARK_GLYPH = 3
COMPONENT_GLYPH = 4

class Font:
	def __init__(self):
		self.properties = {}
		self.properties['head'] = {}
		self.properties['hhea'] = {}
		self.properties['vhea'] = {}
		self.properties['maxp'] = {}
		self.properties['OS_2'] = {}
		self.name = []
		self.palettes = []
		self.script = 'latn'

		self.cmap0 = {}
		self.cmap4 = {}
		self.charset_large = {}
		self.charset_small = {}
		self.charset_total = {}
		self.vs_to_name = {}

		self.glyphs = []
		self.width = {}
		self.lsb = {}
		self.height = {}
		self.tsb = {}
		self.xmin = {}
		self.ymin = {}
		self.xmax = {}
		self.ymax = {}
		self.contours = {}
		self.components = {}
		self.assemblies = {}
		self.post = {}
		self.extra_names = [] 
		self.color_layers = {}

		self.glyph_to_class = {}
		self.mark_to_class = {}
		self.index_to_glyphs = {}

		self.GSUB_features = []
		self.GSUB_lookup_list = []
		self.GSUB_lookups = {}
		self.GSUB_lookup_index_to_feature = {}
		self.GPOS_features = []
		self.GPOS_lookup_list = []
		self.GPOS_lookups = {}
		self.GPOS_lookup_index_to_feature = {}

	def set_property(self, section, prop, val):
		self.properties[section][prop] = str(val)

	def set_today(self):
		now = datetime.now().strftime('%a %b %d %H:%M:%S %Y')
		self.set_property('head', 'created', now)
		self.set_property('head', 'modified', now)

	def adjust_n_glyphs(self):
		n_glyphs = str(len(self.glyphs))
		self.set_property('hhea', 'numberOfHMetrics', n_glyphs)
		self.set_property('maxp', 'numGlyphs', n_glyphs)

	def add_glyph(self, name):
		self.glyphs.append(name)
		if name not in self.width:
			self.width[name] = 0
		if name not in self.lsb:
			self.lsb[name] = 0
		if name not in self.height:
			self.height[name] = 0
		if name not in self.tsb:
			self.tsb[name] = 0
		if name not in self.contours:
			self.contours[name] = []
		if name not in self.components:
			self.components[name] = []

	def complete_name(self, name, name_set):
		if name not in name_set:
			name_set.add(name)
			self.add_glyph(name)
		if name not in self.glyph_to_class:
			self.glyph_to_class[name] = MARK_GLYPH
		if name not in self.mark_to_class:
			self.mark_to_class[name] = 1

	def complete_glyph_list(self):
		name_set = set(self.glyphs)
		for name in self.charset_0.values():
			self.complete_name(name, name_set)
		for name in self.charset_large.values():
			self.complete_name(name, name_set)
		for name in self.charset_small.values():
			self.complete_name(name, name_set)
		for name in self.charset_total.values():
			self.complete_name(name, name_set)
		for name in self.extra_names:
			self.complete_name(name, name_set)

	def add_name_extra(self, name):
		self.add_glyph(name)
		self.extra_names.append(name)

	def add_GSUB_feature(self, feature):
		self.GSUB_features.append(feature)
		for lookup_index in feature.lookup_indexes:
			self.GSUB_lookup_index_to_feature[lookup_index] = feature

	def add_GSUB_lookup(self, index, lookup):
		self.GSUB_lookup_list.append(lookup)
		self.GSUB_lookups[index] = lookup

	def add_GPOS_feature(self, feature):
		self.GPOS_features.append(feature)
		for lookup_index in feature.lookup_indexes:
			self.GPOS_lookup_index_to_feature[lookup_index] = feature

	def add_GPOS_lookup(self, index, lookup):
		self.GPOS_lookup_list.append(lookup)
		self.GPOS_lookups[index] = lookup

	def string_to_tokens(self, s):
		return [self.charset_total[ord(c)] for c in s]

	def new_GSUB_lookup(self, t, feat=None):
		# use integer index for consistency with readers/writers
		index = len(self.GSUB_lookup_list)
		lookup = GSUB_Lookup(index, t)
		self.add_GSUB_lookup(index, lookup)
		if feat is not None:
			feat.add_lookup_index(index)
		return lookup

	def apply(self, tokens, suppressed=[]):
		applications = []
		for lookup in self.GSUB_lookup_list:
			if lookup.index in self.GSUB_lookup_index_to_feature:
				tag = self.GSUB_lookup_index_to_feature[lookup.index].tag
				if tag not in suppressed:
					tokens, applications_lookup = lookup.apply(tokens, self)
					for a in applications_lookup:
						a['feature'] = tag
						applications.append(a)
		positionings = [{} for t in tokens]
		for lookup in self.GPOS_lookup_list:
			if lookup.index in self.GPOS_lookup_index_to_feature:
				tag = self.GPOS_lookup_index_to_feature[lookup.index].tag
				if tag not in suppressed:
					positionings, applications_lookup = lookup.apply(tokens, positionings, self)
					for a in applications_lookup:
						a['feature'] = tag
						applications.append(a)
		return tokens, positionings, applications

	def shape(self, tokens, positionings):
		places = []
		pen_x = 0
		pen_y = 0

		for i, tok in enumerate(tokens):
			pos = positionings[i] if i < len(positionings) else {}

			xoff = pos.get('XOffset', 0)
			yoff = pos.get('YOffset', 0)

			gx = pen_x + xoff
			gy = pen_y + yoff
			places.append((gx, gy))

			cl = self.glyph_to_class.get(tok)

			# zero advance for:
			# - your explicit control/operator glyphs
			# - marks (since signs like A1_33 are positioned onto a base/root)
			# - components/operators (vj/hj etc)
			if CONTROL_GLYPH_RE.match(tok) or cl in (MARK_GLYPH, COMPONENT_GLYPH):
				xadv = 0
				yadv = 0
			else:
				xadv = self.width.get(tok, 0) + pos.get('XAdvance', 0)
				yadv = pos.get('YAdvance', 0)

			pen_x += xadv
			pen_y += yadv

		return places






	def render(self, tokens, suppressed=[]):
		tokens, positionings, applications = self.apply(tokens, suppressed=suppressed)
		return tokens, positionings, applications, self.shape(tokens, positionings)

	def __str__(self):
		s = ''
		for feature in self.GSUB_features:
			s += feature
		for lookup in self.GSUB_lookup_list:
			s += lookup
		for feature in self.GPOS_features:
			s += feature
		for lookup in self.GPOS_lookup_list:
			s += lookup
		return s

data_dir = 'data'

def starter_font():
	font = Font()
	font.add_glyph('.notdef')
	read_basic_properties(os.path.join(data_dir, 'standard_head.xml'), 'head', font)
	read_basic_properties(os.path.join(data_dir, 'standard_hhea.xml'), 'hhea', font)
	read_basic_properties(os.path.join(data_dir, 'standard_maxp.xml'), 'maxp', font)
	read_basic_properties(os.path.join(data_dir, 'standard_os2.xml'), 'OS_2', font)
	read_post(os.path.join(data_dir, 'standard_post.xml'), font)
	read_basic_properties(os.path.join(data_dir, 'standard_vhea.xml'), 'vhea', font)
	return font

class Simulator:
	def __init__(self, font):
		self.font = font
		self.suppressed = []
		self.in_tokens = []
		self.tokens = []
		self.positionings = []
		self.applications = []
		self.places = []

	def set_tokens(self, tokens):
		self.in_tokens = tokens
		self.tokens, self.positionings, self.applications, self.places = \
			self.font.render(tokens, suppressed=self.suppressed)

	def set_string(self, string):
		self.in_tokens = self.font.string_to_tokens(string)
		self.set_tokens(self.in_tokens)

	def in_tokens_str(self):
		return ' '.join(self.in_tokens)
		
	def steps_str(self):
		s = ''
		for a in self.applications:
			s += 'feature: {}, lookup: {}, pos: {}'.format(a['feature'], a['index'], \
				','.join([str(p) for p in a['posses']])) + '\n'
			if 'positionings' not in a:
				s += str(a['rule']) + '\n'
				tokens_copy = a['tokens'].copy()
				tokens_copy.insert(a['posses'][0], '>')
				s += ' '.join(tokens_copy) + '\n'
			else:
				for index, (t, p) in enumerate(zip(a['tokens'], a['positionings'])):
					if index == a['posses'][0]:
						s += '> '
					if len(p) == 0:
						s += t + ' '
					else:
						s += t + '(' + str(p.items()) + ')\n'
				s += '\n'
			s += '\n'
		return s

	def shaped_str(self):
		s = 'Shaped\n'
		for t, p in zip(self.tokens, self.places):
			s += t + str(p) + ' '
		return s
