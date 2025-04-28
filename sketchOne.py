import sys, time
from threading import Lock
from MutexHandler import MutexHandler

class RobotState(MutexHandler):
    '''
    These will be set by the robot's state machine.
    '''
    recordingContainsSpeech = False
    speaking = False
    canSpeak = True
    canListen = True
    lastSpoke = -1
    lock = Lock()

class HumanState(MutexHandler):
    '''
    These will be set by detection callbacks from the robot.
    '''
    id = -1
    distance = -1
    gazeAwayOnset = -1
    speaking = False
    lastSpoke = -1
    currentUtterance = ""
    lock = Lock()

class EngagementState(MutexHandler):
    '''
    States here can be triggered immediately or after timeouts.
    If human can't be detected, set humanPresent to False immediately.
    If the human is silent for a certain amount of time, set longSilence to True.
    If the human is looking away for a certain amount of time, set lookingAway to True.
    If the human is beyond a certain distance from the robot, set leaving to True.
    
    This will be handled in a timed refresh loop, which will set the states, and send a request to handler.
    '''
    humanPresent = False
    longSilence = False # triggered by timeouts
    leaving = False # triggered by timeouts
    lookingAway = False # triggered by timeouts
    lock = Lock()

class RecordingState(MutexHandler):
    recording = False
    currentFile = ''
    startTime = -1
    containsSpeech = False
    lock = Lock()

class SpeechRequest(object):
    speechType = 'speech'
    priority = 'normal'
    utterance = ''

class OpenAIResponseRequest(object):
    responseType = 'response'
    # responseType = 'sessionUpdate'
    request = ''


class EngagementStateHandler(object):
    '''
    This will be the main handler for the engagement state.
    It will be called periodically and take action if there is no active dialog or human is disengaging by any means.
    '''
    def __init__(self):
        self.robotState = RobotState()
        self.humanState = HumanState()
        self.engagementState = EngagementState()

class TranscriptionService(object):
    '''
    This will be used to send requests to a python3 process running in parallel.
    '''
    def __init__(self):
        pass

class OpenAIService(object):
    '''
    This will be used to send requests to a python3 process running in parallel.
    '''
    def __init__(self):
        pass

def callback_speechDetected(robotState, humanState):
    robotState.setAttributes({"recordingContainsSpeech": True, "canSpeak": False})
    humanState.setAttributes({"speaking": True, "lastSpoke": time.time()})

def callback_humanDetected(humanState):
    humanState.setAttributes({"id": 1, "distance": 0.5})

def callback_gazeDetected(humanState, condition):
    if condition:
        humanState.setAttributes({"gazeAwayOnset": -1})
    else:
        humanState.setAttributes({"gazeAwayOnset": time.time()})

if __name__ == "__main__":
    robotState = RobotState()
    humanState = HumanState()
    engagementState = EngagementState()
    
    try:
        while True:
            print("yolo")
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(0)