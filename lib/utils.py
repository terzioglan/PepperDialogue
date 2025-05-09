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

# Cost tracker for OpenAI's GPT-4o Realtime websocket API.
# MENU contains the cost info for the models.
# Cost info here: https://platform.openai.com/docs/pricing#latest-models
# response data structure here: https://platform.openai.com/docs/api-reference/realtime-server-events/response/done
MENU = {
    "gpt-4o-realtime-preview-2024-12-17":{
        "text":{
            "input":5.00,
            "cached":2.50,
            "output":20.00
        },
        "audio":{
            "input": 40.00,
            "cached": 2.50,
            "output": 80.00
        },
        "info": "Units are USD per 1M tokens."
    },
    "gpt-4o-mini-realtime-preview-2024-12-17":{
        "text":{
            "input":0.60,
            "cached":0.30,
            "output":2.40
        },
        "audio":{
            "input": 10.00,
            "cached": 0.30,
            "output": 20.00
        },
        "info": "Units are USD per 1M tokens."
    }
}

class GptCostTracker(object):
    def __init__(self,model, cumulative = True):
        self.menu = MENU
        self.totalCost = 0.0
        self.latestRequestCost = 0.0
        self.model = model
        self.cumulative = cumulative

    def computeCost(self, response, verbose = True):
        """
        Computes the cost of a given response based on token usage details.
        Parameters:
        response (dict): The response.done object containing token usage details.
        sum (bool, optional): If True, adds the computed cost to the total cost. Defaults to True.
        verbose (bool, optional): If True, prints detailed token usage and cost information. Defaults to True.
        Returns:
        float: The computed cost of the response. Returns 0.0 if there is an error in computing the cost.
        Raises:
        KeyError: If the response object does not contain the expected keys.
        """
        cost = 0.0
        try:
            usage = response["usage"]
            costIndices = self.menu[self.model]
        except Exception as e:
            print("cannot compute cost for this request {e}")
            return 0.0
        else:
            cost += usage["input_token_details"]["text_tokens"] * costIndices["text"]["input"]
            cost += usage["input_token_details"]["audio_tokens"] * costIndices["audio"]["input"]

            cost += usage["input_token_details"]["cached_tokens_details"]["text_tokens"] * costIndices["text"]["cached"]
            cost += usage["input_token_details"]["cached_tokens_details"]["audio_tokens"] * costIndices["audio"]["cached"]

            cost += usage["output_token_details"]["text_tokens"] * costIndices["text"]["output"]
            cost += usage["output_token_details"]["audio_tokens"] * costIndices["audio"]["output"]
            
            cost = cost/1000000.0
            
            if self.cumulative:
                self.totalCost += cost
            
            self.latestRequestCost = cost
            
            if verbose:
                print("Input tokens: Text=",usage['input_token_details']['text_tokens'],", Cached text=",usage['input_token_details']['cached_tokens_details']['text_tokens'],", Audio=",usage['input_token_details']['audio_tokens'],", Cached audio=",usage['input_token_details']['cached_tokens_details']['audio_tokens'],"; Output tokens: Text=",usage['output_token_details']['text_tokens'],", Audio=",usage['output_token_details']['audio_tokens'],".")
                print("Last requests cost: $%2.7f, session total cost: $%2.7f" %(self.latestRequestCost, self.totalCost))
            return cost
    


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