#ifndef STRUCTS
#define STRUCTS
#include "global.h"

enum PLAY_STATE
{
	PLAYSTATE_INACTIVE	= 0, //Channel is idle, and will not be sampled
	PLAYSTATE_PLAYING	= 1, //Channel is currently sampling audio
	PLAYSTATE_LOOPING	= 2, //Channel is currently looping sample data
};

enum ADSR_STATE
{
	ADSRSTATE_ATTACK  = 0,
	ADSRSTATE_DECAY   = 1,
	ADSRSTATE_SUSTAIN = 2,
	ADSRSTATE_RELEASE = 3,
};

typedef struct
{
	u32 sample_id;
	
	u32 sample_rate;
	u32 sample_length;
	s32 loop_start; //signed, since I need an invalid value, and -1 is very convenient for that
	u8 attack;
	u8 decay;
	u8 sustain;
	u8 release;
} Instrument;

typedef struct
{
	u8 wave_id;
	u8 channel_id;
	u16 padding1;
	u32 envelope;
	u32 length_enable;
	u32 noise_note;
	u32 padding3;
} InstrumentPSG;

typedef struct
{
	Instrument* curr_instrument[CHANNEL_COUNT];
	u32 sample_position[CHANNEL_COUNT]; //fixed point 20.12, max sample size this gives is 1 MiB, should be plenty lmao
	u32 sample_delta[CHANNEL_COUNT]; // fixed point 20.12, gets added to sample_position every update
	s32 state[CHANNEL_COUNT];
	s32 volume[CHANNEL_COUNT]; //0 to 255
	s32 panning[CHANNEL_COUNT]; //0 to 255, where 127 is center
	u32 note[CHANNEL_COUNT]; //0 to 127
	u32 play_state[CHANNEL_COUNT];
	u8* track_pointer[CHANNEL_COUNT];
	u32 wait_timer[CHANNEL_COUNT];
	u32 curr_note_length[CHANNEL_COUNT];
	s32 adsr_volume[CHANNEL_COUNT];
	u32 adsr_state[CHANNEL_COUNT];
} Channel;

typedef struct
{
	u8* data;
	u32 sample_rate;
	u32 loop_start;
} Sample;


#endif