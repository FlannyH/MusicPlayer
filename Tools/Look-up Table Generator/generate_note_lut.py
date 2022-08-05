base_note = 60

#----NOTE PITCH MULTIPLIERS----
file = open("note_lut.bin", "wb")

#LUT will be in 20.12 fixed point
for note in range(0,128):
    mul = 2 ** ((note-base_note)/12)
    fxp_mul = int(round((mul * (1 << 12))))
    pct_diff = (fxp_mul / (1 << 12) - mul) / mul * 100
    
    file.write(fxp_mul.to_bytes(4, 'little'))
file.close()

#----0.8x0.8 MUL----
file = open("mul08x08.bin", "wb")
#vertical axis: unsigned
#horizontal axis: signed
for y in range(256):
	for x in range(256):
		file.write (bytes([(int(round( (x-128) * (y/255) )) & 0xFF)]))
file.close()

#----NOTE PITCH PSG----
file = open("note_lut_psg.bin", "wb")
a4position = 57
for note in range(128):
	relative_note = note - a4position
	target = 440 * (2 ** (relative_note/12))
	
	x = min(2047, max(0, int(round(2048-(131072/target)))))

	file.write(x.to_bytes(2, "little"))
file.close()