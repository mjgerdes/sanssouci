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
        
    def freeEntries(self):
        """Returns a list of all slots in the table that are free. Empty if none are free."""
        (lower, upper) = self.tableRange()
        acc = []
        for i in range(lower, upper+1):
            add = True
            for (a, b) in self._d["entries"].keys():
                if (i >= a) and (i <= b):
                    add = False

            if add:
                acc.append((i,i))

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
    return
        
    
def mkTableDialogue():
    name = input("Table name?")
    (dice, sides) = getDiceInput()
    return Table(dice, sides, name)
        
