# python2

import time, sys, argparse, subprocess
from multiprocessing import Queue
from functools import partial
from threading import Thread
from scp import SCPClient
import paramiko 

import qi

from lib.recordingManagers import RecordingManager, RecordingHandler
from lib.states import RobotState, RecordingState, HumanState, EngagementState
from lib.serverClient import Client
from lib.pepperProxy import PepperProxy
from lib.utils import fixNameConflicts
from config import recordingConfig, whisperConfig, realtimeConfig

def callback_humanDetected(humanState, value):
    humanState.setAttributes({"id": value[1][0][0], "distance": value[1][0][1]})
 
def callback_humanLeft(humanState, value):
    humanState.setAttributes({"id": -1, "distance": -1,"gazeAwayOnset": time.time(), "gazeOnRobot": False})

def callback_gazeDetected(humanState, value):
    if value == []:
        print("gaze off")
        humanState.setAttributes({"gazeAwayOnset": time.time(), "gazeOnRobot": False})
    else:
        print("gaze on")
        humanState.setAttributes({"gazeAwayOnset": -1, "gazeOnRobot": True})

def callback_speechDetected(
        humanState,
        recordingState,
        pepperProxy,
        robotState,
        value):
        if robotState.getAttribute("speaking"):
            return
        if value == "SpeechDetected":
            pepperProxy.cueSpeechDetected()
            humanState.setAttributes({
                "speaking": True,
                "lastSpoke": time.time(),
            })
            recordingState.setAttributes({
                "containsSpeech": True,
                "pipelineClear": False,
            })
        elif value == "EndOfProcess":
            pepperProxy.cueIdle()
            humanState.setAttributes({
                "speaking": False,
                "lastSpoke": time.time(),
            })
        else:
            print("Unknown value in callback_speechDetected: ", value)

def processInputAndSpeak(input, pepperProxy, robotState, realtimeClient):
    pepperProxy.cueBusy()
    robotState.setAttributes({"speaking": True,"canListen": False, "lastSpoke": time.time()})
    try:
        realtimeClient.send({"message":input})
        response = realtimeClient.receive()
    except Exception as e:
        print("Error communicating to realtimeClient: ", e)
    else:
        print("response received: ", response["message"])
        pepperProxy.speak(response["message"])
    finally:
        robotState.setAttributes({"speaking": False,"canListen": True, "lastSpoke": time.time()})
        pepperProxy.cueIdle()

def main(session):
    '''
    this is everything.
    '''
    # robot-related initializations ##########################################################################
    pepperProxy = PepperProxy(session,)

    recordingState = RecordingState()
    robotState = RobotState()
    humanState = HumanState()

    speechSubscriber = pepperProxy.memoryService.subscriber("ALSpeechRecognition/Status")
    speechSubscriber.signal.connect(partial(
        callback_speechDetected,
        humanState,
        recordingState,
        pepperProxy,
        robotState,
        ))
    gazeSubscriber = pepperProxy.memoryService.subscriber("GazeAnalysis/PeopleLookingAtRobot")
    gazeSubscriber.signal.connect(partial(
        callback_gazeDetected,
        humanState,
        ))
    humanDetectedSubscriber = pepperProxy.memoryService.subscriber("PeoplePerception/PeopleDetected")
    humanDetectedSubscriber.signal.connect(partial(
        callback_humanDetected,
        humanState,
        ))
    humanLeftSubscriber = pepperProxy.memoryService.subscriber("PeoplePerception/JustLeft")
    humanLeftSubscriber.signal.connect(partial(
        callback_humanLeft,
        humanState,
        ))

    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=args.ip, username="nao", password="nao")
    except Exception as e:
        print("cannot ssh into pepper", e)
        return 1
    scpClient = SCPClient(ssh.get_transport()) # to copy files from Pepper to local machine
    ##########################################################################################################
    # local whisper transcription service setup ##############################################################
    try:
        whisperLogName = fixNameConflicts("./logs/whisper_log.log")
        whisperLog = open(whisperLogName, "w")
        whisperProcess = subprocess.Popen(
            [whisperConfig.WHISPER_ENV,
            "./lib/whisperLocal.py",],
            # "./lib/"+whisperConfig.WHISPER_MODEL_FILE],
            stdout=whisperLog,       
            stderr=whisperLog   
            )
    except Exception as e:
        print("cannot start whisper sub process", e)
        sys.exit(1)
    whisperClient = Client(host="localhost", port=whisperConfig.TCP_PORT, size=whisperConfig.TCP_DATA_SIZE)
    ##########################################################################################################
    # OpenAI Realtime server websocket setup  ################################################################
    try:
        realtimeLogName = fixNameConflicts("./logs/realtime_log.log")
        realtimeLog = open(realtimeLogName, "w")
        realtimeProcess = subprocess.Popen(
            ["python", "./lib/realtimeWebsocket.py",],
            stdout=realtimeLog,       
            stderr=realtimeLog   
            )
    except Exception as e:
        print("cannot start realtime sub process", e)
        sys.exit(1)
    realtimeClient = Client(host="localhost", port=realtimeConfig.TCP_PORT, size=realtimeConfig.TCP_DATA_SIZE)
    ##########################################################################################################

    queue_recordingsWithSpeech = Queue(maxsize=100)
    queue_recordingFilenameBuffer = Queue(maxsize=100)
    queue_transcriptions = Queue(maxsize=100)

    recordingManager = RecordingManager(
        method_startRecording=pepperProxy.audioRecorderService.startMicrophonesRecording, 
        method_stopRecording=pepperProxy.audioRecorderService.stopMicrophonesRecording,
        config = recordingConfig,
        verbose=False,
        )
    
    recordingHandler = RecordingHandler(
        method_fetchRecording=scpClient.get,
        config=recordingConfig,
        denoising=True,
        noiseSuppressionHeader = "./lib/noiseSuppressionHeader.wav",
        noiseSuppressionCharSet = r'f\W*f\W*m\W*[pb]\W*g\W*',
        transcriptionClient=whisperClient,
        verbose=False,
        )

    recordingManagerThread = Thread(
        target = recordingManager.start,
        args = (recordingState, robotState, humanState, queue_recordingsWithSpeech, queue_recordingFilenameBuffer,),)
    recordingManagerThread.start()
    
    recordingHandlerThread = Thread(
        target = recordingHandler.start,
        args = (recordingState, queue_recordingsWithSpeech, queue_recordingFilenameBuffer, queue_transcriptions,),)
    recordingHandlerThread.start()

    #############################################################################################################################
    # Main loop #################################################################################################################
    print("Main loop started.")
    try:
        currentHumanUtterance = ""
        while True:
            print("waiting for gaze on robot")
            while not humanState.getAttribute("gazeOnRobot"):
                time.sleep(0.2)
            if recordingState.getAttribute("pipelineClear"):
                processInputAndSpeak("<LOOKING>", pepperProxy, robotState, realtimeClient)
            while humanState.getAttribute("id") != -1:
                if not queue_transcriptions.empty():
                    print("Received transcription from queue.")
                    while not queue_transcriptions.empty():
                        transcriptions = queue_transcriptions.get()
                        for key in transcriptions.keys():
                            currentHumanUtterance = currentHumanUtterance + " " + transcriptions[key]
                elif recordingState.getAttribute("pipelineClear"):
                    currentHumanUtterance = currentHumanUtterance.strip()
                    if currentHumanUtterance != "":
                        print("Generating response for transcription: ", currentHumanUtterance)
                        processInputAndSpeak(currentHumanUtterance, pepperProxy, robotState, realtimeClient)
                        currentHumanUtterance = ""
                    elif (time.time() - humanState.getAttribute("lastSpoke") > 20 ) and (time.time() - robotState.getAttribute("lastSpoke")) > 10:
                        print("silence timeout")
                        processInputAndSpeak("<LONG_SILENCE>", pepperProxy, robotState, realtimeClient)
                time.sleep(0.1)
    #############################################################################################################################
    #############################################################################################################################
    except KeyboardInterrupt:
        recordingManager.stop = True
        recordingHandler.stop = True
        recordingManagerThread.join()
        recordingHandlerThread.join()
        scpClient.close()
        whisperProcess.terminate()
        whisperProcess.wait()
        realtimeProcess.terminate()
        realtimeProcess.wait()
        whisperLog.close()
        realtimeLog.close()
        whisperClient.exit()
        realtimeClient.exit()
        pepperProxy.exit()
        print("Exiting main loop.")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="192.168.1.3")
    parser.add_argument("--port", type=str, default="9559")
    args = parser.parse_args()
    try:
        session = qi.Session()
        session.connect("tcp://"+args.ip+":"+args.port)
    except RuntimeError:
        print("Unable to connect to pepper")
        sys.exit(0)
    finally:
        main(session)