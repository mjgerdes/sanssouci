#!/bin/python3
#
# table.py
#
# Library for random tables

from random import randint
from copy import deepcopy

class Table(object):
    def fromDict(d):
        # the dictionary will have strings instead of tuples for entries' keys
        entries = d["entries"]
        entries2 = dict([(eval(k), v) for (k, v) in entries.items()])

        t = Table(d["dice"], d["sides"], d["name"])
        t._d = d
        t._d["entries"] = entries2
        return t

    def toDict(self):
        d = deepcopy(self._d)
        d["entries"] = {str(k) : v for k,v in self._d["entries"].items()}
        return d

    def __init__(self, dice, sides, name):
        self._d = {"dice" : dice, "sides":sides, "name" : name, "description" : "", "entries": {}}


    def tableRange(self):
        """Returns the range of numbers that can be rolled on the table as a tuple. So a 2d6 table would have a range (2, 12)."""
        d = self._d["dice"]
        return (d, d * self._d["sides"])

    def entryProbability(self, i):
        return self._entryProbability(i,i)

    def entryRangeProbability(self, start, end):
        return self._entryProbability(start, end)


    def _entryProbability(self, start, end):
        (dice, sides) = (self._d["dice"], self._d["sides"])
        # we just brute force it by generating all combinations and counting
        
        def gen(n, k):
            fs = range(1, sides+1) # faces
            if n == 1:
                return [i+k for i in fs]

            return [gen(n-1, f) for f in fs]
        nestedResults = gen(dice, 0)
        while nestedResults and (type(nestedResults[0]) == type([])):
            acc = []
            for xs in nestedResults:
                for x in xs:
                    acc.append(x)
            
            nestedResults = acc

        return round(len([n for n in nestedResults if ((n >= start) and (n <= end))]) / (sides ** dice), 2) 


    def freeEntries(self):
        """Returns a list of all slots in the table that are free. Empty if none are free. Does not return a range, only single numbers are considered."""
        (lower, upper) = self.tableRange()
        acc = []
        for i in range(lower, upper+1):
            add = True
            for (a, b) in self._d["entries"].keys():
                if (i >= a) and (i <= b):
                    add = False

            if add:
                acc.append(i)

        return acc

    def dropEntry(self, n):
        self._dropEntry(n, n)
        return

    def dropEntryRange(self, start, end):
        self._dropEntryRange(start, end)
        return

    def _dropEntryRange(self, start, end):
        entries = self._d["entries"]
        if (start, end) in entries:
            del entries[(start, end)]
        return
        
    def setEntry(self, n, w):
        return self._setEntry((n,n), w)

    def setEntryRange(self, start, end, w):
        return self._setEntry((start,end), w)

    def _setEntry(self, bounds, w):
        (start, end) = bounds
        # reality check
        if start > end:
            return False
        
        entries = self._d["entries"]
        inRange = lambda x: (x >= start) and (x <= end)
        # check if other entries need to be modified
        for (a,b) in list(entries):
            v = entries[(a,b)]

            if inRange(a) and inRange(b):
                pythoniscool = "donothing"
            elif inRange(a):
                entries[(end+1,b)] = v
            elif inRange(b):
                entries[(a, start-1)] = v
            elif (start >= a) and (end <= b):
                entries[(a, start-1)] = v
                entries[(end+1, b)] = v
            else:
                continue
            del entries[(a,b)]
            
        # insert new entry
        entries[(start, end)] = w
        return True

    def pick(self, n):
        """Pick a number and return the corresponding entry on the table as a string. Empty string if no entry or out of range."""
        entries = self._d["entries"]
        for ((a, b), w) in entries.items():
            if (a <= n) and (b >= n):
                return entries[(a,b)]
        return ""

    def roll(self):
        """Rolls on the table and returns the result string.""" 
        (a, b) = self.tableRange()
        return self.pick(randint(a, b))

    def showTable(self, probabilities=False, showFree=False):
        w = ""
        dice = self._d["dice"]
        sides = self._d["sides"]
        dicestring = str(dice) + "d" + str(sides)
        w += " " +dicestring + " | " + self._d["name"] + "\n"
        l = len(dicestring) + 2
        w += (l * "-") + "+" + (12 * "-") + "\n"
        if showFree:
            fs = map(lambda e: ((e, e), ""), self.freeEntries())
            entryList = sorted(list(self._d["entries"].items()) + list(fs))
        else:
            entryList = sorted(self._d["entries"].items())
        for ((a,b), entry) in entryList:
            if a == b:
                numstring = " " + str(a)
            else:
                numstring = " " + str(a) + " - " + str(b)

            w += numstring + ((l - len(numstring)) * " ") + "| " + entry 
            if probabilities and (entry != ""):
                w += " (" + str(100 * self.entryRangeProbability(a, b)) + "%)"
            w += "\n"
        return w
    
    def printTable(self, probabilities=False, showFree=False):
        print(self.showTable(probabilities, showFree))



#########
# Interactive Functions
#######

def getDiceInput():
    while True:
        ws = input("Enter type of table, e.g. 1d8, 2d6, 1d100 etc.").split("d")
        if (len(ws) != 2):
            continue

        try:
            dice = int(ws[0])
            sides = int(ws[1])
        except ValueError:
            continue

        if (sides < 1) or (dice < 1):
            continue

        return (dice, sides)

def addEntryDialogue(t, entry=False):
    if entry:
        e = entry
    else:
        es = t.freeEntries()
        if not(es):
            return False
        e = (es[0], es[0])

    if e[0] != e[1]:
        msg = "Enter text for entries " + str(e[0]) + " - " + str(e[1])
    else:
        msg ="Enter text for entry " + str(e[0])
    w = input(msg + " (probability " + str(t.entryRangeProbability(e[0], e[1])) + "):")
    t.setEntryRange(e[0], e[1], w)
    return True

def addAllEntriesDialogue(t):
    while addEntryDialogue(t):
        pythoniscool = True
    return True

def editEntryDialogue(t, start, end):
    entries = t._d["entries"]
    (lower, upper) = t.tableRange()
    if (start < lower) or (end > upper):
        print("That's not on the table!")
        return

    if not((start, end) in entries):
        addEntryDialogue(t, (start, end))
        return

    w = entries[(start, end)]
    if start == end:
        v = str(start)
    else:
        v = str(start) + " - " + str(end)

    print(" " + v + " | " + w + " | " + str(t.entryRangeProbability(start, end)) + "\nType new value to edit. !d to drop entry. q to quit.\n")
    inp = input()
    if inp == "q":
        return
    elif inp == "!d":
        del entries[(start, end)]
        return

    t.setEntryRange(start, end, inp)
    return
    
def listFromRangeExpression(w):
    """Returns a list containing to elements if w was a string like 1-100 or 2 - 12 etc. Empty list if no parse."""
    ws = w.split("-")
    if len(ws) != 2:
        return []

    ws = list(map(str.strip, ws))
    if not(ws[0].isnumeric()) or not(ws[1].isnumeric()):
        return []

    return [int(ws[0]), int(ws[1])]

def editTableDialogue(t):
    inp = ""
    while inp != "q":
        if inp.isnumeric():
            n = int(inp)
            editEntryDialogue(t, n, n)
        elif "-" in inp:
            # it's a range expression like 2 - 12 (maybe)
            ns = listFromRangeExpression(inp)
            if ns:
                editEntryDialogue(t, ns[0], ns[1])
            else:
                print("Could not parse that range, try 2 - 12 or 1-100 or similar.")
        elif inp == "!wipe":
            t._d["entries"] = {}
        t.printTable(True, True)
        inp = input("Enter a number or a range to edit. !wipe to wipe the table. q to quit.")
    return

def mkTableDialogue():
    name = input("Table name?")
    (dice, sides) = getDiceInput()
    return Table(dice, sides, name)
        
