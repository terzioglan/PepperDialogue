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

def callback_humanDetected(humanState):
    humanState.setAttributes({"id": 1, "distance": 0.5})

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
        value):
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

def main(session):
    '''
    this is everything.
    '''
    # robot-related initializations ##########################################################################
    alMemoryService               = session.service("ALMemory")
    alBasicAwarenessService       = session.service("ALBasicAwareness")
    alSpeechRecognitionService    = session.service("ALSpeechRecognition")
    alAudioRecorderService        = session.service("ALAudioRecorder")
    alLedService                  = session.service("ALLeds")
    alAnimatedSpeechService       = session.service("ALAnimatedSpeech")
    alPostureService              = session.service("ALRobotPosture")
    alMotionService               = session.service("ALMotion")
    pepperProxy = PepperProxy(
        alAnimatedSpeechService,
        alLedService,
        alPostureService,
        alMotionService,
        )

    alSpeechRecognitionService.pause(True)                            # Stop the Speech Recognition system before setting the parameters.
    alSpeechRecognitionService.removeAllContext()                     # Remove all context present if any.
    alSpeechRecognitionService.setLanguage('English')                 # Set Language to English
    # vocabulary = ['Pepper']
    # alSpeechRecognitionService.setVocabulary(vocabulary, False)       # Set vocab sets ALSpeechRecognition/ActiveListening to process speech.
    alSpeechRecognitionService.setVocabulary(['Pepper'], False)       # Set vocab sets ALSpeechRecognition/ActiveListening to process speech.
    alSpeechRecognitionService.setParameter('Sensitivity', 1.0)       # Sensitivity [0.0, 1.0].
    alSpeechRecognitionService.pause(False)                           # Restart the Speech Recognition system for settings to take effect.
    
    alBasicAwarenessService.setEnabled(True)
    alBasicAwarenessService.setEngagementMode("FullyEngaged")
    
    alAudioRecorderService.stopMicrophonesRecording()                  # Stop all microphones if any.
    
    recordingState = RecordingState()
    robotState = RobotState()
    humanState = HumanState()

    speechSubscriber = alMemoryService.subscriber("ALSpeechRecognition/Status")
    speechSubscriber.signal.connect(partial(
        callback_speechDetected,
        humanState,
        recordingState,
        pepperProxy,
        ))
    gazeSubscriber = alMemoryService.subscriber("GazeAnalysis/PeopleLookingAtRobot")
    gazeSubscriber.signal.connect(partial(
        callback_gazeDetected,
        humanState,
        ))

    # alMemoryService.subscriber("PeoplePerception/PeopleDetected")
    # alMemoryService.subscriber("PeoplePerception/JustLeft")


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
            "./lib/whisperLocal.py",
            "./lib/"+whisperConfig.WHISPER_MODEL_FILE],
            stdout=whisperLog,       
            stderr=whisperLog   
            )
    except Exception as e:
        print("cannot start whisper sub process", e)
        sys.exit(1)
    whisperClient = Client(host="localhost", port=whisperConfig.TCP_PORT, size=whisperConfig.TCP_DATA_SIZE)
    ##########################################################################################################
    # OpenAI Realtime server websocke setup  #################################################################
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
        method_startRecording=alAudioRecorderService.startMicrophonesRecording, 
        method_stopRecording=alAudioRecorderService.stopMicrophonesRecording,
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
        args = (recordingState,
                robotState,
                humanState,
                queue_recordingsWithSpeech,
                queue_recordingFilenameBuffer,),)
    recordingManagerThread.start()
    
    recordingHandlerThread = Thread(
        target = recordingHandler.start,
        args = (recordingState,
                queue_recordingsWithSpeech,
                queue_recordingFilenameBuffer,
                queue_transcriptions,),)
    recordingHandlerThread.start()

    #############################################################################################################################
    # Main loop #################################################################################################################
    print("Main loop started.")
    try:
        currentHumanUtterance = ""
        while True:
            if not queue_transcriptions.empty():
                print("Received transcription from queue.")
                while not queue_transcriptions.empty():
                    transcriptions = queue_transcriptions.get()
                    for key in transcriptions.keys():
                        currentHumanUtterance = currentHumanUtterance + " " + transcriptions[key]
            else:
                currentHumanUtterance = currentHumanUtterance.strip()
                if currentHumanUtterance != "" and recordingState.getAttribute("pipelineClear"):
                    print("Generating response for transcription: ", currentHumanUtterance)
                    pepperProxy.cueBusy()
                    robotState.setAttributes({"speaking": True,"canListen": False, "lastSpoke": time.time()})
                    realtimeClient.send({"message":currentHumanUtterance})
                    response = realtimeClient.receive()
                    print("response received: ", response["message"])
                    pepperProxy.speak(response["message"])
                    currentHumanUtterance = ""
                    robotState.setAttributes({"speaking": False,"canListen": True, "lastSpoke": time.time()})
                    pepperProxy.cueIdle()
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
        pepperProxy.eyesReset()
        alAudioRecorderService.stopMicrophonesRecording()
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