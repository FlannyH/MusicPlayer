#pragma once
#include <cstdint>
#include <cstdio>
#include <functional>
#include <utility>

#include "ChannelManager.h"
#include "global.h"
#include "include/PortAudio/portaudio.h"

class AudioDeviceManager
{
public:

	// ReSharper disable once CppParameterMayBeConst
	static int pa_callback(const void*, void* output_buffer, unsigned long frames_per_buffer, const PaStreamCallbackTimeInfo*, PaStreamCallbackFlags, void* user_data)
	{
		const auto* adm = static_cast<AudioDeviceManager*>(user_data);
		ChannelManager::fill_buffer_v_sync(adm->channels_pointer, adm->samples_bin, static_cast<int>(frames_per_buffer), static_cast<int8_t*>(output_buffer));
		return paContinue;
	}

	static void pa_stream_finished(void*)
	{
		return;
	}

    bool init(const int sample_rate);
    bool start() const;
	void set_callback_function(std::function<void(const void*, void*, unsigned long, const PaStreamCallbackTimeInfo*, PaStreamCallbackFlags, void*)> function)
	{
		audio_update_function = std::move(function);
	}

	int16_t sample = 0;
	Channel* channels_pointer;
	u8* samples_bin;
private:
	PaStream* stream = nullptr;
	std::function<void(const void*, void*, unsigned long, const PaStreamCallbackTimeInfo*, PaStreamCallbackFlags, void*)> audio_update_function;
};

