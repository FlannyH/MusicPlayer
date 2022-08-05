#include "ChannelManager.h"

#include <fstream>

const u32 wait_times[] = {
		1, 		2, 		3, 		4, 		6, 		8, 		12, 	16,
		20, 	24, 	28, 	32, 	40, 	48, 	56, 	64,
		80, 	96, 	112, 	128, 	160, 	192, 	224, 	256,
		320,	384,	448,	512,	640,	768,	896,	1024,
};

void* ChannelManager::load_file(const std::string& path)
{
	std::ifstream instrument_file(path, std::ifstream::binary);
	instrument_file.seekg(0, std::ifstream::end);
	const size_t length = instrument_file.tellg();
	instrument_file.seekg(0, std::ifstream::beg);
	char* data = static_cast<char*>(malloc(length));
	instrument_file.read(data, static_cast<long long>(length));
	return data;
}

void ChannelManager::init()
{
	//Init channels
	for (u32 id = 0; id < CHANNEL_COUNT; id++)
	{
		channels.curr_instrument[id] = nullptr;
		channels.sample_position[id] = 0;
		channels.sample_delta[id] = 0;
		channels.state[id] = 0;
		channels.volume[id] = 255;
		channels.panning[id] = 127;
		channels.note[id] = 0;
		channels.play_state[id] = 0;
		channels.track_pointer[id] = nullptr;
		channels.wait_timer[id] = 0;
		channels.curr_note_length[id] = 12;
		channels.adsr_volume[id] = 0;
		channels.adsr_state[id] = 0;
	}

	//Load instrument and note binary files
	instruments_bin = static_cast<Instrument*>(load_file("assets/instruments.bin"));
	note_lut_bin = static_cast<uint32_t*>(load_file("assets/note_lut.bin"));
}

void ChannelManager::start_song(const std::string& sequence_path)
{
	//Load song data
	curr_loaded_song = static_cast<uint8_t*>(load_file(sequence_path));

	//Get song metadata
	u8* moving_seq_data_pointer = curr_loaded_song;
	timer_period = *(moving_seq_data_pointer++);
	timer_period += *(moving_seq_data_pointer++) << 8;
	track_count = *(moving_seq_data_pointer++);

	//Set track pointers, and fill the other tracks with nullptr
	u32 i = 0;
	while (i < track_count)
	{
		track_pointer =  static_cast<intptr_t>(*(moving_seq_data_pointer++));
		track_pointer |= static_cast<intptr_t>(*(moving_seq_data_pointer++)) << 8;
		track_pointer |= static_cast<intptr_t>(*(moving_seq_data_pointer++)) << 16;
		track_pointer |= static_cast<intptr_t>(*(moving_seq_data_pointer++)) << 24;
		track_pointer += reinterpret_cast<intptr_t>(curr_loaded_song);
		channels.track_pointer[i] = reinterpret_cast<uint8_t*>(track_pointer);
		i++;
	}
	while (i < CHANNEL_COUNT)
	{
		channels.track_pointer[i] = nullptr;
		i++;
	}
}


void ChannelManager::update_adsr(const int id)
{
	//If instrument isn't a sample channel, skip
	const Instrument* instrument = channels.curr_instrument[id];

	//Handle ADSR
	switch (channels.adsr_state[id])
	{
	case ADSRSTATE_ATTACK:
		channels.adsr_volume[id] += instrument->attack;
		if (channels.adsr_volume[id] >= 255)
		{
			channels.adsr_volume[id] = 255;
			channels.adsr_state[id] = ADSRSTATE_DECAY;
		}
		break;
	case ADSRSTATE_DECAY:
		channels.adsr_volume[id] -= instrument->decay;
		if (channels.adsr_volume[id] <= instrument->sustain)
		{
			channels.adsr_volume[id] = instrument->sustain;
			channels.adsr_state[id] = ADSRSTATE_SUSTAIN;
		}
		break;
	//case ADSRSTATE_SUSTAIN:
	//do nothing, wait for release
	case ADSRSTATE_RELEASE:
		channels.adsr_volume[id] -= instrument->release;
		if (channels.adsr_volume[id] <= 0)
		{
			channels.adsr_volume[id] = 0;
			channels.play_state[id] = PLAYSTATE_INACTIVE;
		}
		break;
	default: break;
	}
}

void ChannelManager::update_track(const int id)
{
	//Skip if nullptr
	if (channels.track_pointer[id] == nullptr)
	{
		return;
	}

	if (channels.curr_instrument[id] != nullptr)
		update_adsr(id);

	//Handle timer
	if (channels.wait_timer[id] > 1)
	{
		channels.wait_timer[id]--;
		return;
	}

	//If the timer reached zero, handle events
	while (true)
	{
		//Read next byte
		const u8 command = *(channels.track_pointer[id]++);

		if (command <= 0x7F) //Play note event
		{
			set_note(id, command);
			channels.wait_timer[id] = channels.curr_note_length[id];
			break;
		}
		if (command >= 0x80 && command <= 0x9F) //Set note length
		{
			channels.curr_note_length[id] = wait_times[command - 0x80];
		}
		else if (command == 0xA0) //Wait
		{
			channels.wait_timer[id] = channels.curr_note_length[id];
			break;
		}
		else if (command == 0xA1) //Stop note
		{
			channels.adsr_state[id] = ADSRSTATE_RELEASE;
			channels.wait_timer[id] = channels.curr_note_length[id];
			break;
		}
		else if (command == 0xB0) //Set instrument
		{
			channels.sample_position[id] = 0;
			const u8 argument = *(channels.track_pointer[id]++);
			channels.curr_instrument[id] = &instruments_bin[argument];
		}
		else if (command == 0xB1) //Set volume
		{
			const u8 argument = *(channels.track_pointer[id]++);
			channels.volume[id] = argument;
		}
		else if (command == 0xB2) //Set panning
		{
			//Set channel panning
			const u8 argument = *(channels.track_pointer[id]++);
			channels.panning[id] = argument;
		}
		else
		{
			channels.track_pointer[id] = nullptr;
			break;
		}
	}
}

void ChannelManager::set_note(const int id, const int pitch)
{
	channels.note[id] = pitch;
	channels.play_state[id] = PLAYSTATE_PLAYING;

	//Sampled instrument
	if (channels.curr_instrument[id]->sample_id < 0xFFFF0000)
	{
		const Instrument* instrument = channels.curr_instrument[id];
		channels.sample_position[id] = 0;
		const u32 base_sample_rate = instrument->sample_rate;
		const u32 note_multiplier = note_lut_bin[pitch];
		channels.sample_delta[id] = (base_sample_rate * note_multiplier) / (GLOBAL_SAMPLE_RATE);
		channels.adsr_volume[id] = instrument->attack;
		channels.adsr_state[id] = ADSRSTATE_ATTACK;
	}
}

void ChannelManager::update_all_tracks()
{
	for (int i = 0; i < CHANNEL_COUNT; i++)
		update_track(i);
}

void ChannelManager::set_instrument(const int id, const int instrument_id)
{
	channels.sample_position[id] = 0;
	channels.curr_instrument[id] = &instruments_bin[instrument_id];
}
