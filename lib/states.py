from threading import Lock
from lib.mutexHandler import MutexHandler

class RobotState(MutexHandler):
    '''
    These will be set by the robot's state machine.
    '''
    speaking = False
    # canSpeak = True
    canListen = True
    lastSpoke = -1
    lock = Lock()

class RecordingState(MutexHandler):
    recording = False
    currentFile = ''
    startTime = -1
    containsSpeech = False
    pipelineClear = True # this is set to false once a recording gets into the pipeline,
    # and True once every last recording in the pipeline is transcribed.
    lock = Lock()

class HumanState(MutexHandler):
    '''
    These will be set by detection callbacks from the robot.
    '''
    id = -1
    distance = -1
    gazeAwayOnset = -1
    gazeOnRobot = False
    speaking = False
    lastSpoke = -1
    currentUtterance = ""
    lock = Lock()

# class EngagementState(MutexHandler):
#     '''
#     States here can be triggered immediately or after timeouts.
#     If human can't be detected, set humanPresent to False immediately.
#     If the human is silent for a certain amount of time, set longSilence to True.
#     If the human is looking away for a certain amount of time, set lookingAway to True.
#     If the human is beyond a certain distance from the robot, set leaving to True.
    
#     This will be handled in a timed refresh loop, which will set the states, and send a request to handler.
#     '''
#     humanPresent = False
#     longSilence = False # triggered by timeouts
#     leaving = False # triggered by timeouts
#     lookingAway = False # triggered by timeouts
#     lock = Lock()

# class SpeechRequest(object):
#     speechType = 'speech'
#     priority = 'normal'
#     content = ''

# class OpenAIResponseRequest(object):
#     responseType = 'response'
#     # responseType = 'sessionUpdate'
#     request = ''

