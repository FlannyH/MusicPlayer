#include "ChannelManager.h"
#include "global.h"
#include "structs.h"

void ChannelManager::fill_buffer_v_sync(Channel* channels, void* samples_bin, const int buffer_size, int8_t* output_buffer)
{
	//Fill write buffer
	for (int s = 0; s < buffer_size; s++)
	{
		//Update all channels
		for (u32 id = 0; id < CHANNEL_COUNT; id++)
		{
			//If channel is inactive, skip channel
			if (channels->play_state[id] == PLAYSTATE_INACTIVE) { continue; }

			const Instrument* instrument = channels->curr_instrument[id];
			
			//Move sample position
			channels->sample_position[id] += channels->sample_delta[id];

			//If past loop point, wrap around
			const Instrument* instr = channels->curr_instrument[id];
			const u32 sample_position_r12 = channels->sample_position[id] >> 12;
			const u32 sample_length_0 = instr->sample_length;
			const u32 loop_start_l12 = instr->loop_start << 12;
			const u32 condition_loop_sample = (sample_position_r12) > sample_length_0;

			//if loop_start < 0 and end of sample, stop playing
			channels->play_state[id] *= !(condition_loop_sample && instr->loop_start < 0);
			channels->sample_position[id] -= (condition_loop_sample) * ((sample_length_0 << 12) - loop_start_l12);

			//Get pointer to nearest 2 samples
			//Get offset from sample_bin to sample data
			const u32 sample_offset = static_cast<uint32_t*>(samples_bin)[instr->sample_id];

			//Get 2 samples
			const s8 sample1 = static_cast<int8_t*>(samples_bin)[sample_offset + (sample_position_r12)];
			const s8 sample2 = static_cast<int8_t*>(samples_bin)[sample_offset + 1 + (sample_position_r12)];

			//Interpolate between those 2 samples - shifts sample to the left 8 times
			const u8 sample_position_fine = (channels->sample_position[id] >> 4) & 0xFF;
			s32 sample_interpolated = (sample1 * (255 - sample_position_fine));
			sample_interpolated += (sample2 * sample_position_fine);
			sample_interpolated *= channels->volume[id];
			sample_interpolated *= channels->adsr_volume[id];
			sample_interpolated >>= 16;
			sample_interpolated = (((sample_interpolated * (255 - channels->panning[id])) >> 16) & 0x000000FF) | (((sample_interpolated * (channels->panning[id])) >> 0) & 0x00FF0000);

			channels->state[id] = sample_interpolated;
		}

		//Add up all the samples
		s32 sum = 0;

		//This feels cursed - I'm using the sample pointer as a loop counter
		for (s32* sample_pointer = &channels->state[0]; sample_pointer < &channels->state[CHANNEL_COUNT]; sample_pointer++)
		{
			sum += *sample_pointer;
		}
		output_buffer[static_cast<size_t>(s)*2  ] = static_cast<int8_t>((sum) >> 0);
		output_buffer[static_cast<size_t>(s)*2+1] = static_cast<int8_t>((sum) >> 16);
	}
}
