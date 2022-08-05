#pragma once
#include <xstring>

#include "global.h"
#include "structs.h"

class ChannelManager
{
public:
	Channel channels{};

	static void* load_file(const std::string& path);
	void init();
	void start_song(const std::string& sequence_path);
	void update_adsr(int id);
	void update_track(int id);
	void set_note(int id, int pitch);
	void update_all_tracks();
	void set_instrument(int id, int instrument_id);
	static void fill_buffer_v_sync(Channel* channels, void* samples_bin, int buffer_size, int8_t* output_buffer);
	u32 timer_period = 0;

private:
	u32 debug = 0;
	u32 track_count = 0;
	intptr_t track_pointer = 0;

	Instrument* instruments_bin = nullptr;
	u32* note_lut_bin = nullptr;
	u8* curr_loaded_song = nullptr;
};

