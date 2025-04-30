# python2

import time, sys, argparse
sys.path.append("../")
from multiprocessing import Process, Queue
from functools import partial
from threading import Thread

from RecordingManagers import RecordingHandler, RecordingManager
from sketchOne import RobotState, RecordingState, HumanState
from config import *

def startRecording(filename, extension, bitrate, microphoneArray):
    time.sleep(0.2)
    print("recording started")
def stopRecording():
    time.sleep(0.1)
    print("recording stopped")
def fetchRecording():
    time.sleep(0.3)
    print("recording copied")
if __name__ == "__main__":
    '''
    Left here XXX
    ready to test if the recording loop can recording loop.
    currently it should:
    - make 5 second idle recordings and discard them if nothing
    - if speech detected, record until speech is over + padding seconds and put the filename into
    a queue for processing.
    '''
    queue_recordingsWithSpeech = Queue(maxsize=100)
    queue_recordingFilenameBuffer = Queue(maxsize=100)
    queue_transcriptions = Queue(maxsize=100)
    recordingState = RecordingState()
    robotState = RobotState()
    humanState = HumanState()

    recordingManager = RecordingManager(method_startRecording=startRecording, method_stopRecording=stopRecording)
    recordingHandler = RecordingHandler(method_fetchRecording=fetchRecording)

    thread_recordingManager = Thread(
        target = recordingManager.start,
        args = (recordingState,
                robotState,
                humanState,
                queue_recordingsWithSpeech,
                queue_recordingFilenameBuffer,),)
    thread_recordingManager.start()

    thread_recordingHandler = Thread(
        target = recordingHandler.start,
        args = (queue_recordingsWithSpeech,
                queue_recordingFilenameBuffer,
                queue_transcriptions,),)
    thread_recordingHandler.start()

    try:
  

        # TEST1: MULTIPLE SPEECH OVER ALL FILES TEST ##########################################
        # person speaks briefly for a second, then stops briefly then speaks again for a second for 10 times.
        # the recording handler should
        # - get the files as they appear in queue_recordingsWithSpeech
        # - release the recording filenames as they are copied
        # - transcribe them and put the transcriptions in the queue_transcriptions
        print("MULTIPLE SPEECH OVER ALL FILES TEST STARTING")
        input("enter to continue")
        time.sleep(2.0)
        # speech detected
        while not queue_recordingFilenameBuffer.empty():
            print(recordingState.getAttribute("currentFile"))
            print("speaking")
            humanState.setAttributes({
                "speaking": True,
                "lastSpoke": time.time(),
            })
            recordingState.setAttributes({
                "containsSpeech": True,
            })
            time.sleep(0.5)
            print("pause")
            humanState.setAttributes({
                "speaking": False,
                "lastSpoke": time.time(),
            })
            time.sleep(3.0)
        print(recordingState.getAttribute("currentFile"))
        print("speaking")
        humanState.setAttributes({
            "speaking": True,
            "lastSpoke": time.time(),
        })
        recordingState.setAttributes({
            "containsSpeech": True,
        })
        time.sleep(0.5)
        print("pause")
        humanState.setAttributes({
            "speaking": False,
            "lastSpoke": time.time(),
        })
        time.sleep(3.0)
        # end of speech
        start = time.time()
        while time.time() - start < 10:
            if queue_transcriptions.empty():
                print("queue_recordingsWithSpeech is empty")
            else:
                while not queue_transcriptions.empty():
                    transcription = queue_recordingsWithSpeech.get()
                    print("new transcription: ", transcription)
                start = time.time()
            time.sleep(2)
        print("MULTIPLE SPEECH OVER ALL FILES TEST OVER\n\n")
        #######################################################################################

    except KeyboardInterrupt:
        recordingManager.stop = True
        # thread_recordingManager.join()
        print("Exiting main loop.")