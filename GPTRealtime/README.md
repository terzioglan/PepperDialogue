# Setup
Open the `configuration.py` and enter your organizational credentials in the `api_key` field.

To generate an api key, go to: https://platform.openai.com/settings/organization/api-keys

Feel free to edit the `instructions` (a.k.a 'the prompt') in the `configuration.py` to your needs.

Depending on your OS, you might need to install the websocket python package:

```bash
pip install websocket-client
```

## If you are intending to use the local Whisper audio transcription
You need to install `torch` and `whisper` python packages for this application

To install `torch` go to https://pytorch.org/get-started/locally/ , check your OS option and run what it says in the "Run this Command" field.

To install `whisper` python package:
```bash
pip install git+https://github.com/openai/whisper.git 

```


Install `ffmpeg` if your system doesn't have it:
```bash
sudo apt update && sudo apt install ffmpeg
```

# Realtime API WebSocket demo
Run

```bash
python3 realtimeDemo.py
```

to interact with the OpenAI Realtime servers through text.

This code only asks the server to generate text output, so is cheaper than trying it out on the [platform.openai.com](https://platform.openai.com).


# Realtime API Websocket - TCP integration demo
Start the Realtime local server process in one terminal window:
```bash
python3 realtimeLocalServer.py
```

run your application on another terminal window:


```bash
python3 yourApplication.py
```

`yourApplication` communicates with the `realtimeLocalServer` through the TCP port on your localhost, simulating a case where you may want to use multiple processes that will interact with the Realtime servers.

# Whisper transcription to Realtime API Websocket - TCP integration demo
Start the whisper transcription local server process in one terminal window:
```bash
python3 whisperLocalServer.py
```

in another terminal window, start the Realtime local server process:
```bash
python3 realtimeLocalServer.py
```

on a third terminal, run your audio to response application,
```bash
python3 yourAudioToResponseApplication.py
```

`yourAudioToResponseApplication` makes two localhost connections through two TCP ports. It first communicates with the `whisperLocalServer` to transcribe the audio file named `hello-278029.mp3`, and then sends the transcription to `realtimeLocalServer` to generate an LLM response.
