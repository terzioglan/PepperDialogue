import os
HOME = os.path.expanduser("~")

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
    DEFAULT_NEW_AUDIO_FILE_NAME = "newRec"

class WhisperConfig(object):
    # If you already don't have a local model downloaded, the system will automatically
    # download it the first time you run the code.
    WHISPER_MODEL_FILE = "whisper_turbo_local_model.pth"
    TCP_PORT = 4242
    TCP_DATA_SIZE = 1024
    WHISPER_ENV = HOME+"/anaconda3/envs/whisper/bin/python" # TODO: Specify your own conda environment with whisper python installed.

class RealtimeConfig(object):
    # To generate an api key go to: https://platform.openai.com/settings/organization/api-keys
    API_KEY = "Bearer YOUR-API-KEY-WOULD-LOOK-GOOD-HERE" # TODO: Enter your own credential here.
    MODEL = "gpt-4o-mini-realtime-preview-2024-12-17"
    INSTRUCTIONS = """
    1. You're a friendly Pepper humanoid robot from Softbank Robotics. Keep your response short and concise.\n
    2. You are going to have a simple chat with a human.\n
    3. You will start by a couple of turns of greeting and small talk.\n
    """
    TEMPERATURE = 0.8
    TCP_PORT = 2424
    TCP_DATA_SIZE = 1024

recordingConfig = RecordingConfig()
whisperConfig = WhisperConfig()
realtimeConfig = RealtimeConfig()