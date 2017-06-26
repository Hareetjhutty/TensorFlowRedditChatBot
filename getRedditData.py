import re

import _thread
import praw
from cffi import lock

import secrets
import threading

subreddit_data = list()
mylock = _thread.allocate_lock()
num_threads = 0
thread_started = False
class GenData(object):
    def __init__(self, subreddit):
        self.subreddit = subreddit
        self.reddit = praw.Reddit(client_id= secrets.client_id,
                             client_secret= secrets.client_secret,
                             password= secrets.password,
                             user_agent='chatbot',
                             username= secrets.user)
        self.start = 1

    def qualifyData(self, string):
        string = string.lower()
        if len(string) > 1000:
            return False
        if len(string) < 50:
            return False
        if string == " ":
            return False
        if "deleted" in string:
            return False
        if "removed" in string:
            return False
        if "http://" in string:
            return False
        if "https://" in string:
            return False
        if "edit:" in string:
            return False
        if "edited:" in string:
            return False
        if "/u" in string:
            return False
        if "/r" in string:
            return False
        isascii = lambda string: len(string) == len(string.encode())
        if not isascii(string):
            return False
        if "<" in string:
            return False
        if ">" in string:
            return False
        return True

    def stringJoin(self, string):
        string = string.replace("\r", " ")
        tempSplit = string.split(" ")
        temp = ""
        for c in tempSplit:
            temp += c + " "
        string = temp
        splitStr = string.split('\n')
        strJoin = ""
        for s in splitStr:
            strJoin += s + " "
        strJoin = re.sub('[ \t\n]+', ' ', strJoin)
        strJoin = re.sub('\^', '', strJoin)
        strJoin = re.sub('\\\\', '', strJoin)
        return strJoin

    def writeToFile (self, top_level, child):
        if top_level is not None:
            if child is not None:
                #global input
                #global output
                #input.write(str(top_level) + '\n')
                #output.write(str(child) + '\n')
                #self.start += 1
                return True
        return False

    def generateData(self, age = 'all', limit = 100):
        count = 0
        #print ("######### " + self.subreddit + " ############")
        subreddit = self.reddit.subreddit(self.subreddit)
        top = subreddit.top(age, limit = (limit))
        top_level = None
        child = None
        my_dict = dict()
        global num_threads
        num_threads += 1
        global thread_started
        thread_started = True
        for thread in top:
            #print (thread.title)
            #One off posts that all has the same comments...not the best for our dataset :)
            if (thread.title == "What bot accounts on reddit should people know about?"):
                continue
            if (thread.title == "You and a super intelligent snail both get 1 million dollars, and you both become immortal, however you die if the snail touches you. It always knows where you are and slowly crawls toward you. What's your plan?"):
                continue
            #increase limit for bigger dataset
            thread.comments.replace_more(limit=0)
            #Use this command to get all replies for top level -> second level, seconed level - > third level, etc
            #for comment in thread.comments.list():
            for comment in thread.comments.list():
                if (self.qualifyData(comment.body)):
                    top_level = self.stringJoin(comment.body)
                    #print ("Top Leve: " + top_level)
                    comment.replies.replace_more(limit=None, threshold=0)
                    for c in list(comment.replies):
                        #print ("Original subcomment: " + c.body)
                        if self.qualifyData(c.body):
                            #print ("actually chosen: " + self.stringJoin(c.body))
                            child = self.stringJoin(c.body)
                            break
                    if (self.writeToFile(top_level, child)):
                        my_dict[top_level] = child
                        count += 1
                    top_level = None
                    child = None
        mylock.acquire()
        input = open("inputData", 'a')
        output = open("outputData", 'a')
        print("length: " + str(len(my_dict)))
        for k,v in my_dict.items():
            input.write(k + "\n")
            output.write(v + "\n")
        num_threads -= 1
        mylock.release()
        #subreddit_data.append(my_dict)
        print("Count: " + str(count) + " subreddit: " + self.subreddit)
        _thread.exit()

def main():
    global num_threads
    global thread_started
    #splititng into specific subreddits allows more control over content
    white_list = ['philosophy', 'askreddit', 'casualconversation', 'iama', 'all']
    #white_list = ['philosophy']
    for subreddit in white_list:
        mysub = GenData(str(subreddit))
        #mysub.generateData()
        #mysub.generateData("week")
        _thread.start_new_thread(mysub.generateData, ())
        _thread.start_new_thread(mysub.generateData, ("week",))

    while not thread_started:
        pass
    while num_threads>0:
        pass
    #~ For testing purposes ~
    #askreddit = GenData("askreddit")
    #askreddit.generateData()
    #askreddit.generateData("week",5)
    #philosophy = GenData("philosophy")
    #philosophy.generateData()
    #philosophy.generateData("week",5)
    #casualConv = GenData("casualconversation")
    #casualConv.generateData()
    #casualConv.generateData("week", 5)
    #ama = GenData("iama")
    #ama.generateData()
    #ama.generateData("week", 5)
    #all = GenData("all")
    #all.generateData()
    #all.generateData("week", 5)

if __name__ == '__main__':
    main()