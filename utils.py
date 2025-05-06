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