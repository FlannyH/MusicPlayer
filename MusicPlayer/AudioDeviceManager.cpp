#include "AudioDeviceManager.h"

bool AudioDeviceManager::init(const int sample_rate)
{
    //Init PortAudio
    Pa_Initialize();

    //Get output device index
    const int device_index = Pa_GetDefaultOutputDevice();
    if (device_index == paNoDevice) { return false; }

    //Setup output stream parameters
    const PaStreamParameters output_parameters
    {
        device_index,
        2,
        paInt8,
        Pa_GetDeviceInfo(device_index)->defaultLowOutputLatency,
        nullptr,
    };

    //Get device info
    const PaDeviceInfo* device_info = Pa_GetDeviceInfo(device_index);
    if (device_info != nullptr)
    {
        printf("Audio output device: \"%s\"\n", device_info->name);
    }

    PaError error = Pa_OpenStream(
        &stream,
        nullptr,
        &output_parameters,
        sample_rate,
        paFramesPerBufferUnspecified,
        paClipOff,
        &AudioDeviceManager::pa_callback,
        this
    );
    if (error != paNoError)
    {
        printf("Error opening audio stream!\n");
        return false;
    }

    //Set stream finished callback
    error = Pa_SetStreamFinishedCallback(stream, &AudioDeviceManager::pa_stream_finished);
    if (error != paNoError)
    {
        printf("Error setting up audio stream!\n");
        Pa_CloseStream(stream);
        stream = nullptr;
        return false;
    }

    samples_bin = static_cast<uint8_t*>(ChannelManager::load_file("assets/samples.bin"));

    return true;
}

bool AudioDeviceManager::start() const
{
    if (stream == nullptr)
    {
        printf("Error starting audio stream!\n");
        return false;
    }

    const PaError error = Pa_StartStream(stream);

    return (error == paNoError);
}
