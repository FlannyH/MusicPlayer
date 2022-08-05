#include <chrono>
#include "AudioDeviceManager.h"
#include "ChannelManager.h"

int main()
{
    ChannelManager channel_manager;
    AudioDeviceManager audio_device_manager;

    channel_manager.init();
    channel_manager.start_song("assets/SunriseSeq.bin");

    audio_device_manager.init(GLOBAL_SAMPLE_RATE);
    audio_device_manager.channels_pointer = &channel_manager.channels;
    audio_device_manager.start();

    Pa_Sleep(1000);

    const float frame_target = static_cast<float>(channel_manager.timer_period) / 65536.f;
    auto start = std::chrono::steady_clock::now();
    float dt_prev_rest = 0.0f;

    for (int x = 0; x < CHANNEL_COUNT; x++)
    {
    	printf("Channel %i          ", x);
    }
    printf("\n");

    while (true)
    {
        //Timing
        auto end = std::chrono::steady_clock::now();
        std::chrono::duration<float> elapsed_chrono_time = end - start;
        const float delta_time = elapsed_chrono_time.count();
        //printf("%f\n", delta_time);

        //If waited long enough, update all tracks
        if (delta_time + dt_prev_rest >= frame_target)
        {
            dt_prev_rest = (delta_time + dt_prev_rest) - frame_target;
            start = std::chrono::steady_clock::now();
            channel_manager.update_all_tracks();

            //Debug print
            const std::string note_names[]
            {
                "C-",
                "C#",
                "D-",
                "D#",
                "E-",
                "F-",
                "F#",
                "G-",
                "G#",
                "A-",
                "A#",
                "B-",
            };

            for (int x = 0; x < CHANNEL_COUNT; x++)
            {
                if (channel_manager.channels.play_state[x] == PLAYSTATE_INACTIVE)
                    printf("... v.. x v.. p..  ");
                else
                    printf("%s%i v%02X x v%02X p%02X  ", 
                        note_names[channel_manager.channels.note[x] % 12].c_str(), 
                        channel_manager.channels.note[x] / 12, 
                        channel_manager.channels.volume[x], 
                        channel_manager.channels.adsr_volume[x], 
                        channel_manager.channels.panning[x]);

            }
        printf("\n");
        }
    }
}
