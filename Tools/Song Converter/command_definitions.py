import itertools

NOTE_LENGTH_TABLE = [
	1, 		2, 		3, 		4, 		6, 		8, 		12, 	16,
	20, 	24, 	28, 	32, 	40, 	48, 	56, 	64,
	80, 	96, 	112, 	128, 	160, 	192, 	224, 	256,
	320,	384,	448,	512,	640,	768,	896,	1024,
]

PREV_LENGTH = None

def CMD_PLAY_NOTE(note):
	assert (note <= 0x7F)
	return [0x00 + note]
	
def CMD_SET_NOTE_LENGTH_BY_INDEX(index):
	assert (index <= 0x1F)
	return [0x80 + index]
	
def CMD_SET_NOTE_LENGTH_BY_VALUE(value):
	assert (value in NOTE_LENGTH_TABLE)
	return [0x80 + NOTE_LENGTH_TABLE.index(value)]
	
def CMD_WAIT_NOTE():
	return [0xA0]
	
def CMD_STOP_NOTE():
	return [0xA1]
	
def CMD_STOP_TRACK():
	return [0xA2]
	
def CMD_SET_INSTRUMENT(instrument):
	assert (instrument <= 0x7F)
	return [0xB0, instrument]
	
def CMD_SET_VOLUME(volume):
	assert (volume <= 0xFF)
	return [0xB1, volume]
	
def CMD_SET_PANNING(panning):
	print (panning)
	assert (panning <= 0xFF)
	return [0xB2, panning]
	
def CMD_COMMAND_WITH_LENGTH(command, length):
	global PREV_LENGTH
	command_list = list()
	next_up_is_command = True
	while (length > 0):
		#Find highest value in NOTE_LENGTH_TABLE that fits
		i = len(NOTE_LENGTH_TABLE)
		while (i > 0):
			i -= 1
			#When found
			if (NOTE_LENGTH_TABLE[i] <= length):
				#Subtract length
				length -= NOTE_LENGTH_TABLE[i]
				
				#If the length is different from the last length, add a set length command
				if (PREV_LENGTH != NOTE_LENGTH_TABLE[i]):
					command_list.append(CMD_SET_NOTE_LENGTH_BY_INDEX(i))
					PREV_LENGTH = NOTE_LENGTH_TABLE[i]
					
				if next_up_is_command:
					command_list.append(command)
					next_up_is_command = False
				else:
					command_list.append(CMD_WAIT_NOTE())
				
				break
				
	return list(itertools.chain.from_iterable(command_list))