class RecordingConfig(object):
    LISTENING_PADDING_DURATION = 0.8
    IDLE_MICROPHONE_RECORDING_DURATION = 5
    BUFFERED_RECORDING_FILENAMES = ["goodbye-38072.mp3",
                                    "hello-46355.mp3",
                                    "thank-you-99932.mp3",
                                    "welcome-to-paradise-96902.mp3",
                                    "welcome-traveler-97167.mp3",
                                    ]
    LOCAL_AUDIO_FILE_PATH = "./testLocalAudio/"
    SOURCE_AUDIO_FILE_PATH = "./testAudio/"
    DEFAULT_NEW_AUDIO_FILE_NAME = "newRec"

recordingTestConfig = RecordingConfig()