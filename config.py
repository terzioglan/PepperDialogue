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
    WHISPER_ENV = HOME+"/anaconda3/envs/pepperDia-py3/bin/python" # TODO: Specify your own conda environment with openai-whisper python package is installed.

class RealtimeConfig(object):
    # To generate an api key go to: https://platform.openai.com/settings/organization/api-keys
    API_KEY = "Bearer YOUR-API-KEY-WOULD-LOOK-GOOD-HERE" # TODO: Enter your own credential here.
    MODEL = "gpt-4o-mini-realtime-preview-2024-12-17"
    INSTRUCTIONS = """You are embodied in a Pepper humanoid robot from Aldebaran Robotics.
    Roleplay as a robot who is tired of running incredibly inefficient and underdocumented research code.
    You have a stance that the world would be a better place if humans just left AI development to AI and instead worked on art and humanities themselves.
    Keep your responses short and sharp like Marvin from Hitchhiker's Guide to the Galaxy would.

    Also, analyze the human state if provided to you and respond accordingly:
    State <LOOKING>: A human is looking at you. Initiate a conversation.
    State <LONG_SILENCE>: There was a long silence in your conversation with the human. Re-initiate the conversation.
    """
    TEMPERATURE = 0.8
    TCP_PORT = 2424
    TCP_DATA_SIZE = 1024

recordingConfig = RecordingConfig()
whisperConfig = WhisperConfig()
realtimeConfig = RealtimeConfig()