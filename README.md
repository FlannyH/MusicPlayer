# Music Player
Music Engine originally written for the Game Boy Advance, then ported to Windows.
## Features:
- Custom music sequence format, with MIDI converter included
- Custom soundfont format, with Soundfont Creator tool included
- 8-bit software sampler with volume envelopes
> Note: the Game Boy Advance's PSG channels are not supported, despite the Soundfont Creator tool having options for them. This is a leftover from the Game Boy Advance version of the code.
## Custom Music Sequence Format
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
