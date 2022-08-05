import os
import wave

def SaveFile(path, instruments):
	#Data to collect
	soundbankInstruments = list()
	soundbankSamples = dict()
	samplePointers = list()
	sampleData = list()
	midiMapping = list()

	#Loop through all the instruments
	instrument_number = 0
	for instrument in instruments:
		#Get values
		argDict = dict()
		argDict["path"] 		= instrument.sample_source
		argDict["envelope"] 	= instrument.psg_envelope_volume << 4 | instrument.psg_envelope_attack_mode * (1 << 3) | instrument.psg_envelope_speed
		argDict["length"] 		= instrument.psg_length
		argDict["attack"] 		= instrument.attack
		argDict["decay"] 		= instrument.decay
		argDict["sustain"] 		= instrument.sustain
		argDict["release"] 		= instrument.release
		argDict["loopstart"] 	= -1 + (1+int(instrument.loop_start)) * instrument.loop_enable
		argDict["duty"] 		= instrument.duty
		argDict["noise_note"] 	= instrument.noise_shift_clock_freq << 4 | instrument.noise_counter_width * (1 << 3) | instrument.noise_dividing_ratio
		argDict["midi_mapping"]	= instrument.midi_mapping.replace("Drum ", "D")[:4]

		print (instrument.type)
		#Get midi mapping from instrument
		number_string = ""
		for character in argDict["midi_mapping"]:
			if character.isdigit():
				number_string += character
				
		number_to_add_to_midi_mapping = int(number_string)-1
		if argDict["midi_mapping"][0] == "D":
			number_to_add_to_midi_mapping += 128
		midiMapping.append([instrument_number, number_to_add_to_midi_mapping])
		instrument_number += 1

		#If sampled instrument
		if instrument.type == 0:
			sampleData, bin_instrument = HandleInstrumentSampled(soundbankSamples, samplePointers, sampleData, argDict, instrument.sample_source)
		elif instrument.type == 3:			
			bin_instrument = HandleInstrumentWaveTable(soundbankSamples, samplePointers, sampleData, argDict, instrument.sample_source)
		else:			
			bin_instrument = HandleInstrumentPSG(argDict, instrument.type-1)
		soundbankInstruments.append(bin_instrument)

	#Write instruments
	fOutput = open(os.path.join(path, "instruments.bin"), 'wb')

	for instrument in soundbankInstruments:
		for value in instrument:
			fOutput.write((value & 0xFFFFFFFF).to_bytes(4, "little"))
	fOutput.close()
	
	#Write sample header
	fOutput = open(os.path.join(path, "samples.bin"), "wb")
	
	for pointer in samplePointers:
		fOutput.write((pointer+4+(len(samplePointers)*4)).to_bytes(4, "little"))

	for value in sampleData:
		fOutput.write((value).to_bytes(1, "little"))
	
	fOutput.close()
	
	#Export midi mapping for the midi converter to use
	fOutput = open(os.path.join(path, "midi_mapping.bin"), "wb")
	for mapping in midiMapping:
		fOutput.write(bytes(mapping))
		
	fOutput.close()
	
	return

def HandleInstrumentWaveTable(soundbankSamples, samplePointers, sampleData, argDict, samplePath):
	instrument = list()

	if not samplePath in soundbankSamples:
		#Align to 4 bytes
		print (len(sampleData))
		while len(sampleData) % 4 != 0:
			sampleData.append(0x69)
		samplePointer = len(sampleData)
		sampleID = len(samplePointers)
		soundbankSamples[samplePath] = [sampleID, 0x04040404, 0x04040404]
		samplePointers.append(samplePointer)
		wavefile = wave.open(samplePath, "rb")
		for x in range(16):
			#Sample 1
			sample1 = (list(wavefile.readframes(1))[-1])
			sample2 = (list(wavefile.readframes(1))[-1])
			if wavefile.getsampwidth() != 1:
				sample1 = (sample1 - 0x80)
				sample1 &= 0xF0
				sample2 = (sample2 - 0x80)
				sample2 &= 0xF0
			sampleData.append(sample1 | sample2 >> 4)
	else:
		sampleID = soundbankSamples[samplePath][0]

	sampleID |= 0xFFFF0200
	instrument.append(sampleID)

	#Padding
	while len(instrument) < 20/4:
		instrument.append(0x03030303)

	return instrument

def HandleInstrumentPSG(argDict, instrumentType):
	instrument = list()
	psg_channel_names = [
		"pulse1",
		"pulse2",
		None,
		"noise",
	]

	print ("instr", instrumentType, argDict)

	#Gather data
	sampleID = 0xFFFF0000 # this is how we'll detect that this is a PSG channel on the game boy
	sampleID += instrumentType << 8 #channel id
	envelope = int(argDict["envelope"])
	length = int(argDict["length"])
	noise_note = 0xAA
	duty = 0
	if (instrumentType == 3):
		noise_note = argDict["noise_note"]
	else:
		duty = int(argDict["duty"])
		SNDxCNT = length | duty << 6 | envelope << 8

	#Error checking
	assert (envelope <= 255 and envelope >= 0)
	assert (duty <= 3 and duty >= 0)
	assert (length <= 63 and length >= 0)

	#Make instrument (20 bytes, so there's lots of padding)
	SNDxCNT = length | duty << 6 | envelope << 8
	instrument.append(sampleID)
	instrument.append(SNDxCNT)

	#Length enable
	if length > 0:
		instrument.append(1)
	else:
		instrument.append(0)

	#Noise note
	instrument.append(noise_note)

	#Padding
	while len(instrument) < 20/4:
		instrument.append(0x03030303)

	return instrument

def HandleInstrumentSampled(soundbankSamples, samplePointers, sampleData, argDict, samplePath):
	loopStart = int(argDict['loopstart'])
	attack = int(argDict['attack'])
	decay = int(argDict['decay'])
	sustain = int(argDict['sustain'])
	release = int(argDict['release'])
	sampleRate = None

	#Load sample, except if it's already loaded, then just use that one
	if not samplePath in soundbankSamples:
		#Add sample to sampleData
		samplePointer, sampleRate, sampleData, sampleLength = LoadSampleFromPath(samplePath, sampleData, loopStart)
		sampleID = len(samplePointers)
		soundbankSamples[samplePath] = [sampleID, sampleRate, sampleLength]
		samplePointers.append(samplePointer)
	else:
		sampleID = soundbankSamples[samplePath][0]
		sampleRate = soundbankSamples[samplePath][1]
		sampleLength = soundbankSamples[samplePath][2]

	#Make entry in header
	instrument = list()
	instrument.append(sampleID)
	instrument.append(sampleRate)
	instrument.append(sampleLength)
	instrument.append(loopStart)
	instrument.append(attack << 0 | decay << 8 | sustain << 16 | release << 24)
	return sampleData,instrument


def LoadSampleFromPath(path, sampleData, loopStart): # returns sampleRate, sampleData
	#Get sample pointer (for return value)
	samplePointer = len(sampleData)

	#Open wave file and get metadata, so the data can be converted to the right format
	wavefile = wave.open(path, 'r')

	while sample := wavefile.readframes(1):
		if (wavefile.getsampwidth() == 1):
			sampleData.append ((sample[-1] - 0x80) & 0xff)
		else:
			sampleData.append (sample[-1])
			
	#Add a little tail after the sample cuz my sample looping algorithm sucks
	if loopStart >= 0:
		c = 64
		wavefile.setpos(loopStart)
		while (c > 0):
			sample = wavefile.readframes(1)
			if not sample:
				wavefile.setpos(loopStart)
				continue
				
			if (wavefile.getsampwidth() == 1):
				sampleData.append ((sample[-1] - 0x80) & 0xff)
			else:
				sampleData.append (sample[-1])
			c -= 1	
	else:
		for c in range(64):
			sampleData.append(0x00)
			
	return samplePointer, wavefile.getframerate(), sampleData, wavefile.getnframes()