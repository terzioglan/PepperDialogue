class RecordingConfig(object):
    LISTENING_PADDING_DURATION = 0.8
    IDLE_MICROPHONE_RECORDING_DURATION = 5
    BUFFERED_RECORDING_FILENAMES = ["recording1.wav", 
                                    "recording2.wav", 
                                    "recording3.wav", 
                                    "recording4.wav", 
                                    "recording5.wav",
                                    ]
    SOURCE_AUDIO_FILE_PATH = "/home/nao/" # Path to audio file inside Pepper.
    LOCAL_AUDIO_FILE_PATH = "./audioRecordings/" # Path to local system to store that audio file.

recordingConfig = RecordingConfig()