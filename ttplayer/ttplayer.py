#! /usr/bin/python3
import time
import os
from subprocess import *
import re



FILES = {}
FILES[1] = os.listdir("./1/")
FILES[2] = os.listdir("./2/")
FILES[3] = os.listdir("./3/")

CMD = {}
CMD[1] = "cvlc -Z -R ".split()
CMD[2] = "mplayer -volume 100".split()
CMD[3] = "cvlc -Z -R ".split()

def getSoundTime(file):
    process = subprocess.Popen(['ffmpeg',  '-i', file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = process.communicate()
    matches = re.search(r"Duration:\s{1}(?P<hours>\d+?):(?P<minutes>\d+?):(?P<seconds>\d+\.\d+?),", stdout, re.DOTALL).groupdict()
    return (matches["hours"], matches["minutes"], mathces["seconds"])



def getDir(w, channel=1):
    if not(w):
        return w
        
    for file in FILES[channel]:
        if(w in file):
            return file
            return ""


class State(object):
    def __init__(self):
        self.ps = { 1 : Popen(["echo", "Channel 1 open"]),
                    2 : Popen(["echo", "Channel 2 open"]),
                    3 : Popen(["echo", "Channel 3 open"])}
        self.currentChannel = 1

    def shutDown(self, c = 0):
        if c != 0:
            try:
                self.ps[c].terminate()
            except:
                print("")
            return

        for (k, process) in self.ps.items():
            try:
                process.terminate()
            except:
                print("")

    def setChannel(self, n):
        if n < 1 or n > 3:
            print("Not a channel")
            return
            
        self.currentChannel = n
        print("Now on channel " + str(n))
        
    def channel(self):
        return self.currentChannel

    def play(self, file):
        c = self.channel()
        try:
            self.ps[c].terminate()
        except:
            print("")

        del self.ps[c]

        if c == 2:
            self.effect(file)
        else:
            newcmd = CMD[c] + ["./" + str(c) + "/" + file + "/"]
            time.sleep(0.1)
            self.ps[c] = Popen(newcmd,stderr=PIPE)

    def _effectCollect(self, es):
        d = {}
        for e in es:
            if e[0] in d:
                d[e[0]].append(e)
            else:
                d[e[0]] = [e]
        return sorted(d.items())

    def _timesteps(self, el):
        acc = []
        for w in el:
            if not("+" in w):
                acc.append((w, 0.0))
            else:
                a = w.split("+")
                b = a[1].split("_")
                c = b[0]
                acc.append((w, float(c)))

        return sorted(acc)

    def effect(self, file):
        es = sorted(os.listdir("./2/" + file))
        for (k, el) in self._effectCollect(es):
            for (effect, timestep) in self._timesteps(el):
                newcmd = CMD[2] + ["./2/" + file + "/" + effect]
                time.sleep(timestep)
                self.ps[2] = Popen(newcmd, stderr = PIPE, stdout = PIPE)

            self.ps[2].wait()



def setVolume(p):
    p      = Popen(["amixer","-D","pulse","sset", "Master",str(p) + "%"],stderr=PIPE)

def main():
    print("Listening...")
    state = State()
    while(True):
        w = input()
        
        if(w == "q"):
            state.shutDown()
            return

        if w.isdigit():
            state.setChannel(int(w))
            continue

        if w == "":
            state.shutDown()
            continue


        if w[0] == "!":
            if len(w) == 1:
                setVolume(50)
            else:
                try:
                    setVolume(int(w[1:]))
                except:
                    print("Eror setting volume.")
            continue

        file = getDir(w, state.channel())
        if(file):
            print("playing " + file)
            state.play(file)
               
        else:
            state.shutDown(state.channel())
            print("Not found: " + w)


if(__name__=="__main__"):
    main()
