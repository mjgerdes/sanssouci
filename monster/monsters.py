#!/usr/bin/python3
#
# monsters.py
#
# Manages a JSON monster database. This program fulfills two main functions:
# 1. When invoked without arguments, tries to open monsters.json
# in order to dump a sorted and formated monster database in the emacs org-mode format to stdout
#
# 2. when invoked with "g" or "generate" goes into monster encounter generation mode, using the monster.json database.
# This mode has its own query syntax, which is currently undocumented.
# Encounters randomly generated in this mode are also output in the emacs org-mode format.


import random
from collections import Counter
from math import *
import json
from math import floor
import sys
from encountergenerate import *


SKILLS = """survival
acrobatics
history
investigation
athletics
religion
arcana
persuasion
performance
intimidation
deception
nature
medicine
insight
perception
stealth""".split("\n")


def modi(x):
    return floor((x - 10) / 2)

def mkActions(ds):
    w = ""
    for d in ds:
        w += "**** " + d["name"]
        if "attack_bonus" in d.keys():
            w += ", +" + str(d["attack_bonus"])

        if "damage_dice" in d.keys():
            w += ", " + d["damage_dice"]

        if "damage_bonus" in d.keys():
            w += " +" + str(d["damage_bonus"])
        w += "\n"
        w += d["desc"]
        w += "\n"

    return w


def mkShortStats(d):
    w = " . "
    w += str(d["hit_points"]) + " HP " + str(d["armor_class"]) + " AC "
    acs = d.get("actions", {})
    for d in acs:
        w += " $ " + d["name"]
        if "attack_bonus" in d.keys():
            w += " +" + str(d["attack_bonus"])

        if "damage_dice" in d.keys():
            w += " " + d["damage_dice"]

        if "damage_bonus" in d.keys():
            w += " +" + str(d["damage_bonus"])

    return w

def shortName(name):
    ws = name.split(" ")
    short = ""
    for w in ws:
        if w:
            short += w[0]

    return short
def mkInit(d, n = 1):
    w = ""
    if n > 1:
        countString = str(n) + " "
    else:
        countString = ""


    w += "*** " + countString + d.get("name", "N/A") + " init + " + str(modi(d["dexterity"])) + "\n"

    for i in range(1, n+1):
        w += shortName(d.get("name", "N/A")) + str(i) + " " + str(d["hit_points"]) + " HP " + str(d["armor_class"]) + " AC\n"

    acs = mkShortStats(d).split("$")
    for a in acs[1:]:
        w += a[1:] + "\n"

    return w + "---\n" 
    



def mkEntry(d):
    w = ""
    # name
    w += "** " + d["name"]  + mkShortStats(d) + "\n"
    

    # info line
    w += d["type"]
    if d["subtype"] != "":
        w+= " (" + d["subtype"] + ") "
    w += ", " + d["size"] + " " + d["speed"]
    w += ", " + d["alignment"] + ", CR " + d["challenge_rating"] + "\n"

    # init block for copying
    w += mkInit(d)
    # defense
    w += "*** HP " + str(d["hit_points"]) + " " + d["hit_dice"] + " ; AC " + str(d["armor_class"]) + "\n"

    

    # senses
    w += d["senses"] + "\n"

    # languages
    w += d["languages"] + "\n"


    if d["damage_vulnerabilities"] != "":
        w += "Damage Vulnerabilities: " + d["damage_vulnerabilities"] + "\n"

    if d["damage_resistances"] != "":
        w += "Resistance: " + d["damage_resistances"] + "\n"
        
    immuw = ""
    if d["damage_immunities"] != "":
        immuw += "Damage: " + d["damage_immunities"] + "\n"
    if d["condition_immunities"] != "":
        immuw += "Conditions: " + d["condition_immunities"] +"\n"

    if immuw != "":
            w += "Immunities\n" + immuw

            # offense
            #actions
    w += "*** actions\n"
    w += mkActions(d.get("actions", []))


    # reactions
    reactionsw = mkActions(d.get("reactions", []))
    if reactionsw != "":
        w += "*** reactions\n" + reactionsw 

    # traits
    tw = mkActions(d.get("special_abilities", []))
    if tw != "":
        w += "*** traits\n" + tw



    # legendary
    ww = mkActions(d.get("legendary_actions", []))
    if ww != "":
        w += "*** legendary\n" + ww


    # stats
    w += "*** stats\n"

    # saves
    xs = [("str save", "strength_save"), ("dex save ", "dexterity_save"), ("con save", "constitution_save"), ("int save ", "intelligence_save"), ("wis save", "wisdom_save"), ("cha save", "charisma_save")]
    qs = map(lambda p: (p[0], str(d.get(p[1], ""))), xs)
    for (label, result) in qs:
        if result != "":
            w += label + "+" + result + "\n"

    w += str(modi(d["strength"])) + ", " + str(modi(d["dexterity"])) + ", " + str(modi(d["constitution"])) + "\n"
    w += str(modi(d["intelligence"])) + ", " + str(modi(d["wisdom"])) + ", " + str(modi(d["charisma"])) + "\n"


    # skills
    sks = map(lambda k: (k, str(d.get(k, ""))), SKILLS)
    skillw = ""
    for (sk, value) in sks:
        if value != "":
            skillw += sk + " " + value + "\n"

    if skillw != "":
        w += "*** skills\n" + skillw

    return w





def sortBy(ds, sortKey):
    return sorted(ds, key=lambda k: k.get(sortKey, "N/A"))

def hackFloat(w):
    if type(w) == type(1):
        return float(w)

    if type(w) == type(1.1):
        return w
    w2 = w.split("/")
    if len(w2) == 2:
        a = w2[0]
        b = w2[1]
        return float(a)/ float(b)
    else:
        return float(w2[0])

def sortByCS(ds):
    sortKey = "challenge_rating"
    return sorted(ds, key= lambda k: hackFloat(k.get(sortKey, 100)))

    return result


def printDocument(ds):    
    cs = sortByCS(ds)
    currentCS = ""
    w = ""
    for d in cs:
        if(currentCS != d.get("challenge_rating", "N/A")):
            currentCS = d.get("challenge_rating", "N/A")
            w += "* CR " + currentCS + "\n"

        if("name" in d.keys()):
            w += mkEntry(d)
    #    w += d.get("name", "N/A") + "\n"
    print(w)
                
                      
def main(argv):
    filename = "monsters.json"
    ds = json.loads(open(""+filename).read())


    if len(argv) == 1:
        printDocument(ds)
        return


    if argv[1] == "g":
        generator(ds)
        return




def findByKey(ds, key, value, f = lambda x: x):
    for d in ds:
        if f(d.get(key, "")) == value:
            return d

    return {}

def countDuplicates(xs, key=None):
    if key:
        c = Counter([x.get(key, "") for x in xs])
        return [(findByKey(xs, key, value), count) for (value, count) in c.items()] 

    c = Counter(xs)
    return c.items()


if (__name__ == "__main__"):
    main(sys.argv)


