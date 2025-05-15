from threading import Lock
from lib.mutexHandler import MutexHandler

class RobotState(MutexHandler):
    '''
    These are set in the mainApplication before and after the robot speaks.
    Has a direct effect on how speech recognition callbacks are handled.
    '''
    speaking = False
    # canSpeak = True
    canListen = True
    lastSpoke = -1
    lock = Lock()

class RecordingState(MutexHandler):
    '''
    recording, currentFile, startTime are set by the recordingManager
    containsSpeech and pipelineClear are set by the voice activity detection callback
    pipeline clear is reset to True once the last recording is handled by the recordingHandler.
    '''
    recording = False
    currentFile = ''
    startTime = -1
    containsSpeech = False
    pipelineClear = True # this is set to false once a recording gets into the pipeline,
    # and True once every last recording in the pipeline is transcribed.
    lock = Lock()

class HumanState(MutexHandler):
    '''
    These are set by the speech and human detection callbacks.
    currentUtterance is currently not used, but it can be used to store the last utterance
    '''
    id = -1
    distance = -1
    gazeAwayOnset = -1
    gazeOnRobot = False
    speaking = False
    lastSpoke = -1
    currentUtterance = ""
    lock = Lock()

# Looking further:
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

