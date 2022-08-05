from mido import MidiFile
import sys
from command_definitions import *
import os

#Open midi file
midi_file = MidiFile(sys.argv[1])
tracks = list()
output_data = bytes()

tempo_bpm = None
tempo_resolution = midi_file.ticks_per_beat

instr_map = [0] * 128
#instr_map[81] = 0
#instr_map[80] = 1
#instr_map[61] = 8
#instr_map[60] = 2
#instr_map[38] = 3
#instr_map[29] = 9
#instr_map[30] = 0x0A
#instr_map[34] = 1
#
drum_map = [0] * 128
#drum_map[36] = 4
#drum_map[38] = 0x0C
#drum_map[40] = 5
#drum_map[41] = 0x0D
#drum_map[46] = 6
#drum_map[47] = 0x0D
#drum_map[48] = 0x0D
#drum_map[49] = 7
#drum_map[51] = 0x0B
#drum_map[53] = 0x0B

#Setup instrument map
#file_mapping = open(os.path.split(sys.argv[1])[0]
path_to_this_file = os.path.split(sys.argv[1])[0]
if (len(path_to_this_file) > 0):
    path_to_this_file += "\\"
    
try:
    data = open(path_to_this_file + "midi_mapping.bin", "rb")
except FileNotFoundError:
    print ("[ERROR] Unable to find file 'midi_mapping.bin'! Have you created a soundfont? If so, copy the 'midi_mapping.bin' file to the same folder as the MIDI file.")
    exit(1)

while True:
    mapping_part = data.read(2)
    if len(mapping_part) < 2:
        break
    if (mapping_part[1] >= 0x80):
        drum_map[mapping_part[1]-128] = mapping_part[0]
    else:
        instr_map[mapping_part[1]] = mapping_part[0]
        
        
print (instr_map)

#Loop over each track
for i, track in enumerate(midi_file.tracks):
	print('Track {}: {}'.format(i, track.name))
	track_commands = list()
	
	#Check for time signature/tempo events
	for message in track:
		#if message.type == "time_signature":
		#	tempo_resolution = message.clocks_per_click
		#	print ("\t\t",message)
		if message.type == "set_tempo":
			tempo_bpm = 1_000_000 / message.tempo * 60
	
	#Check if there are any notes in this track
	has_notes = False
	for message in track:
		if message.type == "note_on":
			has_notes = True
	
	#Skip this track if there are no notes
	if not has_notes:
		continue
		
	curr_time = 0
	curr_instr = 0
	curr_pan = 63.5
	curr_vol = 100
	curr_velocity = 100
	filtered_track = dict()
	
	#Filter all the messages in this track, only keep the messages we need (such as note on/off, panning, volume, instrument changes)
	for message in track:
		print(message)
		curr_time += message.time
		
		#Handle instrument changes
		if message.type == "program_change":
			curr_instr = instr_map[message.program]
			
		#Handle control changes (panning, volume)
		if message.type == "control_change":
			if message.control == 7: #Volume
				curr_vol = message.value
			elif message.control == 10: #Panning
				curr_pan = message.value
				
		if message.type == "note_on":
			curr_velocity = message.velocity
			if message.channel == 9:
				curr_instr = drum_map[message.note]
				message.note = 60
				
		filtered_track[curr_time] = [message, curr_instr, curr_pan, curr_vol, curr_velocity]
		
	#Get event lengths
	i = -1
	time_prev = 0
	lengths = list()
	for time in filtered_track:
		print (time)
		lengths.append(time - time_prev)
		time_prev = time
	lengths.append(0)
		
	y = 0
	for x in filtered_track:
		#print (lengths[y], filtered_track[x])
		y += 1
	#Parse the filtered list, turn it into commands
	commands = list()
	time_prev = 0
	time_curr = 0
	vol_x_vel_prev = None
	vol_x_vel_curr = 0
	pan_prev = None
	pan_curr = 0
	instrument_prev = None
	if lengths[0] > 0:
		commands.append(CMD_COMMAND_WITH_LENGTH(CMD_WAIT_NOTE(), lengths[0]))
	
	i = 0
	for time in filtered_track:
		#Get message, update time values
		i += 1
		length = lengths[i]
		message, instrument, panning, volume, velocity = filtered_track[time]
		vol_x_vel_prev = vol_x_vel_curr
		vol_x_vel_curr = volume * velocity
		pan_prev = pan_curr
		pan_curr = panning
		
		#Handle instrument
		if instrument_prev != instrument:
			commands.append(CMD_SET_INSTRUMENT(instrument))
			instrument_prev = instrument
		
		#Some dumb midi files use note on to cut a note, correct for this
		if velocity == 0:
			vol_x_vel_curr = vol_x_vel_prev
		
		#Handle control changes (panning, volume)
		if vol_x_vel_curr != vol_x_vel_prev:
			channel_volume_target = int(vol_x_vel_curr >> 6)
			commands.append(CMD_SET_VOLUME(channel_volume_target))
		if pan_curr != pan_prev:
			channel_panning_target = int(pan_curr * 2)
			if (channel_panning_target > 255):
				channel_panning_target = 255
			#print (channel_panning_target)
			commands.append(CMD_SET_PANNING(channel_panning_target))
				
		#todo: fix panning and volume
				
		#Handle notes
		if message.type == "note_on":
			if message.velocity > 0:
				commands.append(CMD_COMMAND_WITH_LENGTH(CMD_PLAY_NOTE(message.note), length))
			if message.velocity == 0:
				commands.append(CMD_COMMAND_WITH_LENGTH(CMD_STOP_NOTE(), length))
		elif message.type == "note_off":
			commands.append(CMD_COMMAND_WITH_LENGTH(CMD_STOP_NOTE(), length))
		elif length > 0:
			commands.append(CMD_COMMAND_WITH_LENGTH(CMD_WAIT_NOTE(), length))
			
			
	commands.append(CMD_STOP_TRACK())
	for command in commands:
		print (command)
	tracks.append(list(itertools.chain.from_iterable(commands)))
	#print ([hex(x)[2:].zfill(2).upper() for x in list(itertools.chain.from_iterable(commands))])
	
#Get timer period and write it
print (tempo_resolution, tempo_bpm)
ticks_per_second = (tempo_bpm / 60) * tempo_resolution
print (ticks_per_second)
timer_period = int(round(65536 / ticks_per_second))
print (timer_period)
output_data += timer_period.to_bytes(2, 'little')
	
#Write track count
output_data += len(tracks).to_bytes(1, 'little')
	
#Write pointers
track_pointer = len(tracks)*4 + 3
for track in tracks:
	output_data += track_pointer.to_bytes(4, 'little')
	track_pointer += len(track)
	
#Write tracks
for track in tracks:
	for b in track:
		output_data += bytes([b])
		
#Write file
output_file = open(sys.argv[1].replace(".mid", "") + ".bin", "wb")
output_file.write(output_data)
output_file.close()