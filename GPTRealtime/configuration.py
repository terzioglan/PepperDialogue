
class config(object):
    # To generate an api key go to: https://platform.openai.com/settings/organization/api-keys
    api_key = "Bearer YOUR-API-KEY-WOULD-LOOK-GOOD-HERE" # Enter your own credential here.
    
    realtimeModel = "gpt-4o-mini-realtime-preview-2024-12-17"
    instructions = """1. You're a friendly Pepper humanoid robot from Softbank Robotics. Keep your response short and concise.\n
2. You are going to have a simple chat with a human.\n
3. You will start by a couple of turns of greeting and small talk.\n"""
    temperature = 0.8

    whisperModelPath = "whisper_turbo_local_model.pth"

    tcp_port_realtime = 4242
    tcp_port_whisper = 2424
    tcp_data_size = 1024

configuration = config()
