# Music Player
Music Engine originally written for the Game Boy Advance, then ported to Windows.
## Features:
- Custom music sequence format, with MIDI converter included
- Custom soundfont format, with Soundfont Creator tool included
- 8-bit software sampler with volume envelopes
> Note: the Game Boy Advance's PSG channels are not supported, despite the Soundfont Creator tool having options for them. This is a leftover from the Game Boy Advance version of the code.
## Custom Music Sequence Format
### Header:
The binary format for a Flan Sequence Binary File (.bin) is as follows:
```c++
u16 timer_period; // Time in ticks (range from 0 - 65536 maps to 0.0 - 1.0 seconds per tick)
u8 track_count; // Number of tracks in the file
u32 track_offsets[track_count]; // Offsets to start of track data, one for each track
u8 track_data[]; // The rest of the file is raw track data, to the end of the file
```

### Commands:
##### 0x00 - 0x7F: Play Note
Play a note. The command code itself is taken as the MIDI key. Sets the note wait timer, which means the channel will wait for the timer to run out after this command. Note length is set by the `Set Note Length` command.
##### 0x80 - 0x9F: Set Note Length
Sets the note length for all upcoming `Play Note` and `Wait Note` commands.
The new note length will be set to `wait_times[command & 0x1F]`.
```c++
const u32 wait_times[] = {
        1,      2,      3,      4,      6,      8,      12,     16,
        20,     24,     28,     32,     40,     48,     56,     64,
        80,     96,     112,    128,    160,    192,    224,    256,
        320,    384,    448,    512,    640,    768,    896,    1024,
};
```
##### 0xA0: Wait Note
Same as the `Play Note` command, except it does nothing but set, then wait out the note wait timer. Note length is set by the `Set Note Length` command.
##### 0xA1: Stop Note
Sets the channel's volume envelope into `Release` mode, comparable to a MIDI `note_off` event. Sets the note wait timer.
##### 0xA2: End of Track
Marks the end of the track. Playback will stop when this command is encountered.
##### 0xB0: Set Channel Instrument
Takes one extra byte of data as an argument. Changes the channel's instrument to the value of this byte. All new notes will play with the newly set instrument. Value must be between 0 - 127.
##### 0xB1: Set Channel Volume
Takes one extra byte of data as an argument. Changes the channel's volume to be equal to the value of the argument. Values can be 0 - 255, where 0 is silent and 255 is full volume.
##### 0xB2: Set Channel Panning
Takes one extra byte of data as an argument. Changes the channel's panning to be equal to the value of the argument. Values can be 0 - 255, where 0 is fully left, 127 is center, and 255 is fully right.
## Custom Soundfont Format
### instruments.bin:
This file contains all the data for instruments, generated from the Soundfont Creator Tool. The file data is a raw array of a 20-byte instrument struct, which looks like this:
```c++
u32 sample_id; // Index into the samples.bin header
u32 sample_rate; // The sample rate for middle C = note value 60 = note command 0x3C
u32 sample_length; // The length of the sample (in samples)
s32 loop_start; // Sample index to loop back to when the sample reaches the end. Only loop if >= 0
u8 attack; // Value to add to volume every tick during attack stage until volume reaches 255
u8 decay; // Value to subtract from volume every tick during decay stage until volume reaches sustain
u8 sustain; // Value to reach during decay stage, and to stay at during the sustain stage
u8 release; // Value to subtract from volume every tick during release stage until volume reaches 0
```
The old Game Boy Advance version also had a PSG version of the instrument. An instrument is a PSG instrument if the two most significant bytes of `sample_id` (little endian) are equal to  `0xFFFF`. A PSG instrument uses a different struct:
```c++
u8 wave_id; // The index into the samples.bin header. Wavetables for a PSG instrument are always 16 bytes long, just like on the Game Boy itself.
u8 channel_id; // Which PSG channel on the Game Boy Advance to use: 0-pulse1, 1-pulse2, 2-wave, 3-noise, other values are invalid.
u16 padding1; // Should be 0xFFFF, used as marker to detect PSG instruments.
u32 envelope; // Direct value to send to the PSG register: 0bVVVV_PEEE_DDLL_LLLL, where V-volume, P-envelope polarity, D-pulse duty cycke, L-length value
u32 length_enable; // Flag for Game Boy, determines whether the length value is used or not.
u32 noise_note; // Noise channel only: Properties for the noise generator. Only least significant byte is used, the rest is ignored.
u32 padding3; // PSG instruments should be the same size as sample instruments, but PSG doesn't need as much data.
```
The `envelope` property is a raw 16-bit value that will be sent to the PSG registers; the high byte going to the corresponding <a href="https://gbdev.gg8.se/wiki/articles/Sound_Controller#FF12_-_NR12_-_Channel_1_Volume_Envelope_.28R.2FW.29">Volume Envelope Register</a>, and the low byte going to the <a href="https://gbdev.gg8.se/wiki/articles/Sound_Controller#FF11_-_NR11_-_Channel_1_Sound_length.2FWave_pattern_duty_.28R.2FW.29">Duty/Length Register</a>.
The `noise_note` property is a raw 8-bit value that will be sent to the <a href="https://gbdev.gg8.se/wiki/articles/Sound_Controller#FF22_-_NR43_-_Channel_4_Polynomial_Counter_.28R.2FW.29">Noise Channel Polynomial Counter register</a>.

### samples.bin:
This file contains all the sample data. It starts with `u32 sample_offsets[sample_count]`, followed by raw sample data.
Sample offsets are relative to the start of the file, and are used by instrument structs to get the start of the sample data.
Sample data is in 8-bit unsigned mono PCM format for Sampled instruments.
> Note: the old Game Boy Advance version also supported PSG wavetables in the samples.bin file. These wavetables are 4-bit unsigned mono PCM samples, the same format as the <a href="https://gbdev.gg8.se/wiki/articles/Sound_Controller#FF30-FF3F_-_Wave_Pattern_RAM">Game Boy Wave Pattern RAM</a>.
