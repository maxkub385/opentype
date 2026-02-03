# DO NOT USE
class Substitution:
	def __init__(self, left, input, right, output):
		self.left = left
		self.input = input
		self.right = right
		self.output = output

	def length(self):
		return len(self.left) + len(self.input) + len(self.right)

	def recur(self, tokens, pos, font, lookup):
		return self.output if isinstance(self.output, int) else None

	def applicable(self, tokens, pos, font, lookup):
		if False and len(tokens) > 2 and tokens[1] == 'ch0' and lookup.index == 99 and pos == 1:
			print(self.left)
			print(self.input + self.right)
			print(filter_glyph(tokens[pos], font, lookup))
			print(tokens[:pos])
			print(filter_list(tokens[:pos], lambda t : filter_glyph(t, font, lookup)))
			print(tokens[pos:])
			print(filter_list(tokens[pos:], lambda t : filter_glyph(t, font, lookup)))
		return pos < len(tokens) and filter_glyph(tokens[pos], font, lookup) and \
			is_suffix_of(self.left, filter_list(tokens[:pos], \
				lambda t : filter_glyph(t, font, lookup))) and \
			is_prefix_of(self.input + self.right, filter_list(tokens[pos:], \
				lambda t : filter_glyph(t, font, lookup)))

	def apply(self, tokens, pos, font, lookup):
		tokens = tokens.copy()
		posses = []
		i = pos
		while len(posses) < len(self.input):
			if filter_glyph(tokens[i], font, lookup):
				posses.append(i)
			i += 1
		for i in reversed(posses):
			del tokens[i]
		if self.output is not None:
			for token in reversed(self.output):
				tokens.insert(pos, token)
			return tokens, len(self.output), posses
		else:
			return tokens, 0, posses

	def __str__(self):
		left = ' '.join([l if isinstance(l, str) else '/'.join(l) for l in self.left])
		right = ' '.join([l if isinstance(l, str) else '/'.join(l) for l in self.right])
		out = ' '.join(self.output) if self.output is not None else 'None'
		return left + ' ' + self.input + ' ' + right + ' -> ' + out
