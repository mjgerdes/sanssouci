#!/bin/python3
#
# table.py
#
# Library for random tables


class Table(object):
    def __init__(self, dice, sides, name):
        self._d = {"dice" : dice, "sides":sides, "name" : name, "description" : "", "entries": {}}


    def tableRange(self):
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

        return round(len([n for n in nestedResults if ((n >= start) and (n <= end))]) / (dice * sides), 2) 


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
            
    def showTable(self):
        w = ""
        dice = self._d["dice"]
        sides = self._d["sides"]
        dicestring = str(dice) + "d" + str(sides)
        w += " " +dicestring + " | " + self._d["name"] + "\n"
        l = len(dicestring) + 2
        w += (l * "-") + "+" + (12 * "-") + "\n"

        for ((a,b), entry) in sorted(self._d["entries"].items()):
            if a == b:
                numstring = " " + str(a)
            else:
                numstring = " " + str(a) + " - " + str(b)

            w += numstring + ((l - len(numstring)) * " ") + "| " + entry + "\n"

        return w
        
    def printTable(self):
        print(self.showTable())
        
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

def addEntryDialogue(t):
    es = t.freeEntries()
    if not(es):
        print("Table is full. Set an entry to something else or drop an entry to make space.")
        return
    
    e = es[0]
    w = input("Enter text for entry " + str(e) + " (probability " + str(t.entryProbability(e)) + "):")
    t.setEntry(e, w)
    return 
        
    
def mkTableDialogue():
    name = input("Table name?")
    (dice, sides) = getDiceInput()
    return Table(dice, sides, name)
        
