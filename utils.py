import copy, os

def fixNameConflicts(filename,extension):
    i = 2
    newFilename = copy.deepcopy(filename)
    while(os.path.isfile(newFilename+extension)):
        print("file %s exists, assigning new name to file" %(newFilename+extension))
        newFilename = filename+"_("+str(i)+")" 
        i+=1
    return newFilename+extension