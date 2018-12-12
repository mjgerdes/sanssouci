#!/usr/bin/python3
#
# monsters.py
#
# Manages a JSON monster database. This program fulfills two main functions:
# 1. When invoked with o or output as argument, tries to open monsters.json
# in order to dump a sorted and formated monster database in the emacs org-mode format to stdout
#
# 2. when invoked with "g" or "generate" goes into monster encounter generation mode, using the monster.json database.
# Encounters randomly generated in this mode are also output in the emacs org-mode format.
#
# Will also print help information when invoked without arguments

from math import *
import json
from math import floor
import sys
from encountergenerate import *

HELPTEXT = """monster.py - Python script to format monster information and geenerate encounters
Usage: monster.py [OPTION] COMMAND

Commands
  g, generate - Enter encounter generation mode, see below for syntax
  o, output - Output monster json database in emacs org-mode format

Options
  --help - Print this help text
"""
HELPTEXT += ENCOUNTERGENERATEHELP

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


    if len(argv) == 1 or argv[1] == "--help":
        print(HELPTEXT)
        return
    if(argv[1] == "o") or (argv[1] == "output"):
        printDocument(ds)
        return


    if (argv[1] == "g") or (argv[1]== "generate"):
        generator(ds)
        return

if (__name__ == "__main__"):
    main(sys.argv)


