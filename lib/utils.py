import copy, os

def fixNameConflicts(file):
    i = 2
    extension = '.'+file.split('.')[-1]
    newFile = copy.deepcopy(file)
    while(os.path.isfile(newFile)):
        print("file %s exists, assigning new name to file" %(newFile))
        newFile = file.replace(extension,'')+"_("+str(i)+")"+extension
        i+=1
    return newFile

# def queueTest():
#     transcriptionQueue = Queue(maxsize=100)
#     recordingFileQueue = Queue(maxsize=100)
#     recordingHandler = RecordingFileHandler()
#     recordingHandlerProcess = Process(
#         target = recordingHandler.start,
#         args = (recordingFileQueue,transcriptionQueue,),)
#     recordingHandlerProcess.start()

#     filename = "recording"
#     i = 0
#     try:
#         while True:
#             recordingFileQueue.put(filename+'_'+str(i))
#             while not transcriptionQueue.empty():
#                 transcription = transcriptionQueue.get()
#                 print("Got transcription: ", transcription)
#             i += 1
#             time.sleep(0.2)
#     except KeyboardInterrupt:
#         recordingHandler.stop = True
#         recordingHandlerProcess.join()
#         print("Exiting main loop.")