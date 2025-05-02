# python2

import time, sys, argparse
from multiprocessing import Process, Queue
from functools import partial
from threading import Thread
from scp import SCPClient
from paramiko import SSHClient

import qi

from RecordingManagers import RecordingManager, RecordingHandler
from sketchOne import RobotState, RecordingState, HumanState
from config import *

def callback_speechDetected(
        humanState,
        recordingState,
        # robotHandler,
        value):
        if value == "SpeechDetected":
            humanState.setAttributes({
                "speaking": True,
                "lastSpoke": time.time(),
            })
            recordingState.setAttributes({
                "containsSpeech": True,
                "pipelineClear": False,
            })
            # robotHandler.cueSpeechDetected()
        elif value == "EndOfProcess":
            humanState.setAttributes({
                "speaking": False,
                "lastSpoke": time.time(),
            })
            # robotHandler.cueEndOfSpeechDetected()
        else:
            print("Unknown value in callback_speechDetected: ", value)

def queueTest():
    transcriptionQueue = Queue(maxsize=100)
    recordingFileQueue = Queue(maxsize=100)
    recordingHandler = RecordingFileHandler()
    recordingHandlerProcess = Process(
        target = recordingHandler.start,
        args = (recordingFileQueue,transcriptionQueue,),)
    recordingHandlerProcess.start()

    filename = "recording"
    i = 0
    try:
        while True:
            recordingFileQueue.put(filename+'_'+str(i))
            while not transcriptionQueue.empty():
                transcription = transcriptionQueue.get()
                print("Got transcription: ", transcription)
            i += 1
            time.sleep(0.2)
    except KeyboardInterrupt:
        recordingHandler.stop = True
        recordingHandlerProcess.join()
        print("Exiting main loop.")

def main(session):
    '''
    Left here XXX
    ready to test if the recording loop can recording loop.
    currently it should:
    - make 5 second idle recordings and discard them if nothing
    - if speech detected, record until speech is over + padding seconds and put the filename into
    a queue for processing.
    '''
    # qi Session initializations ############################################
    alSpeechRecognitionService    = session.service("ALSpeechRecognition")
    alAudioRecorderService        = session.service("ALAudioRecorder")
    alMemoryService               = session.service("ALMemory")

    alSpeechRecognitionService.pause(True)                            # Stop the Speech Recognition system before setting the parameters.
    alSpeechRecognitionService.removeAllContext()                     # Remove all context present if any.
    vocabulary = ['Pepper']
    alSpeechRecognitionService.setLanguage('English')                 # Set Language to English
    alSpeechRecognitionService.setVocabulary(vocabulary, False)       # Set vocab sets ALSpeechRecognition/ActiveListening to process speech.
    alSpeechRecognitionService.setParameter('Sensitivity', 1.0)       # Sensitivity [0.0, 1.0]. Higher sensitivity, better audio capture.
    alSpeechRecognitionService.pause(False)                           # Restart the Speech Recognition system for settings to take effect.
    
    alAudioRecorderService.stopMicrophonesRecording()                  # Stop all microphones if any.
    
    speechSubscriber = alMemoryService.subscriber("ALSpeechRecognition/Status")
    speechSubscriber.signal.connect(partial(
        callback_speechDetected,
        humanState,
        recordingState,
        # robotHandler,
        ))
    #########################################################################
    # SSH file transfer setup for Pepper ################################################################
    ssh = SSHClient()
    ssh.load_system_host_keys()
    try:
        ssh.connect(hostname=args.ip, username="nao", password="nao")
    except Exception as e:
        print("cannot ssh into pepper", e)
        return 1
    scpClient = SCPClient(ssh.get_transport())
    #####################################################################################################

    
    queue_recordingsWithSpeech = Queue(maxsize=100)
    queue_recordingFilenameBuffer = Queue(maxsize=100)
    queue_transcriptions = Queue(maxsize=100)
    recordingState = RecordingState()
    robotState = RobotState()
    humanState = HumanState()

    recordingManager = RecordingManager(
        method_startRecording=alAudioRecorderService.startMicrophonesRecording, 
        method_stopRecording=alAudioRecorderService.stopMicrophonesRecording)
    
    recordingHandler = RecordingHandler(
        method_fetchRecording=scpClient.get,
        denoising=True,
        noiseSuppressionHeader = "./noiseSuppressionHeader.wav",
        noiseSuppressionCharset = r'f\W*f\W*m\W*[pb]\W*g\W*',
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
        args = (queue_recordingsWithSpeech,
                queue_recordingFilenameBuffer,
                queue_transcriptions,),)
    recordingHandlerThread.start()

    try:
        while True:
            # do stuff
            time.sleep(1.0)

    except KeyboardInterrupt:
        recordingManager.stop = True
        recordingHandler.stop = True
        recordingManagerThread.join()
        recordingHandlerThread.join()
        scpClient.close()
        print("Exiting main loop.")


if __name__ == "__main__":
    # main()

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

    recordingTest(session)