from lxml import etree

from ttxfont import Simulator
from ttxread import read_ttx
from ttxwrite import write_ttx

def copy(filein, fileout):
	doc = etree.parse(filein)
	doc.write(fileout, xml_declaration=True, encoding='utf-8')

def read_write(filein, fileout):
	font = read_ttx(filein)
	write_ttx(font, fileout)

def test_read_simulate_tokens(filename, tokens):
	font = read_ttx(filename)
	# simulate(font, tokens)
	sim = Simulator(font)
	sim.suppressed = ['ss01', 'rtlm']
	sim.set_tokens(tokens)
	print(sim.in_tokens_str() + '\n')
	print(sim.steps_str(), end='')
	print(sim.shaped_str())

def test_read_simulate_string(filename, string):
	font = read_ttx(filename)
	sim = Simulator(font)
	sim.suppressed = ['ss01', 'rtlm']
	sim.set_string(string)
	print(sim.in_tokens_str() + '\n')
	print(sim.steps_str(), end='')
	print(sim.shaped_str())
	
# copy('eot.ttx', 'eotcopy.ttx')

# test_read_simulate_tokens('eot.ttx', ['A1'])
# test_read_simulate_tokens('eot.ttx', ['A1', 'vj', 'A1', 'hj', 'A1'])
test_read_simulate_tokens('eot.ttx', ['A1', 'vj', 'A1', 'vj', 'A1', 'vj', 'A1'])
# test_read_simulate_tokens('eot.ttx', ['A1', 'vj', 'A1', 'vj', 'X1', 'vj', 'A1'])

# test_read_simulate_string('eot.ttx', '𓀀𓐰𓁐')

# read_write('eot.ttx', 'reparsed.ttx')

# test_read_simulate_tokens('createdfont.ttx', ['u13000', 'vj', 'u13000', 'hj', 'u13000'])
