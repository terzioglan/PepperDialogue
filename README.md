# LLM-powered dialogues with a Pepper robot
`mainApplication.py` uses Pepper's voice activity detection system to start/stop audio recordings, copy the recording files from the robot to the local system, transcribes the recordings using `openai-whisper` package using a local Whisper model, and uses OpenAI Realtime webclient to request and receive responses through a WebSocket. The LLM response is later uttered by the robot.

Overall system architecture looks like this:


The system is implemented for Pepper robots running NAOqi 2.5 operating system, and uses qi Python API and SDK.
qi SDK only supports Python 2, so the `mainApplication.py` should be run using Python 2.7.X.
Step-by-step test codes are available in `./tesCode/`, which may help using the system with a different robot and/or a different verbal interaction system.
These can be run using either Python2 or Python3. 

## Setup
It is recommended to setup two conda environments, one with Python 2.7.x to use NAOqi SDK, and one with Python 3.x to use `openai-whisper` package.
Anaconda environment files for these two environments are provided in `pepper-env.yml` and `whisper-env.yml` respectively.
To create these environments, run:
```bash
conda env create -f pepper-env.yml
conda env create -f whisper-env.yml
```
Additionally, `qi Python SDK` should also be installed on your system.

Once all the installations are complete
1. Edit the `config.py` file and make sure the Python3 environment path is set correctly
2. Enter your OpenAI access key in `config.py` to access the Realtime servers
3. Feel free to edit the LLM prompt in `config.py`
4. Activate your Python2 environment (`conda activate pepperDia-py2`)
5. And run
```bash
python mainApplication.py --ip your.pepper.robot.ip
``` 

The application should then:
1. Wait until the robot detects a human gaze on it
2. Request a conversation initiation utterance from the Realtime server
3. Keep conversing with the person as long as the person is still visible
4. Break long silences by initiation conversation
5. Go to step 1 if the person is no longer detected.


The sub-process outputs are exported in `./logs/` directory.
Error message, OpenAI request costs, and similar relevant information can be tracked using these log files.