#!/bin/python3
#
# table.py
#
# Library for random tables


class Table(object):
    def __init__(self, dice, sides, name):
        self._d = {"dice" : dice, "sides":sides, "name" : name, "description" : "", "entries": {}}


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
    
def mkTableDialogue():
    name = input("Table name?")
    (dice, sides) = getDiceInput()
    return Table(dice, sides, name)
        
