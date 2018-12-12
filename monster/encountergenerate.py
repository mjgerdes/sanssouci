#!/bin/python
# encountergenerate.py
#
# This is a library used by monsters.py

from collections import Counter
import random
from math import *
from copy import deepcopy


ENCOUNTERGENERATEHELP = """
Encounter Generator Command syntax
After setup, the generator enters a REPL where you can enter the following

<newline> - (i.e. no input) Generate another encounter randomly, observing the current filter and xp threshold parameters
clear - Clear the current filter and generate another encounter
pick NAME1:N1[,NAME2:N2...] - Enter a new filter, generating only encounters that include the specified number (N) of monsters named NAME

Examples:
pick kobold:1
pick priest:1,cultist:5
"""





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


def modi(x):
    return floor((x - 10) / 2)


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
    




def findByKey(ds, key, value, f = lambda x: x):
    for d in ds:
        if f(d.get(key, "")) == value:
            return d

    return {}


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


def countDuplicates(xs, key=None):
    if key:
        c = Counter([x.get(key, "") for x in xs])
        return [(findByKey(xs, key, value), count) for (value, count) in c.items()] 

    c = Counter(xs)
    return c.items()


    
### generator stuff

def xpPerCR(cr):
    if type(cr) == type(""):
        cr = hackFloat(cr)

    if type(cr) == type(1):
        cr = float(cr)

    d = {
        0.0 : 10,
        0.125 : 25,
        0.25 : 50,
        0.5 : 100,
        1.0 : 200,
        2.0 : 450,
        3.0 : 700,
        4.0 : 1100,
        5.0 : 1800,
        6.0 : 2600,
        7.0 : 2900,
        8.0 : 3900,
        9.0 : 5000,
        10.0 : 5900,
        11.0 : 7200,
        12.0 : 8400,
        13.0 : 10000,
        14.0 : 11500,
        15.0 : 13000,
        16.0 : 15000,
        17.0 : 18000,
        18.0 : 20000,
        19.0 : 22000,
        20.0 : 25000,
        21.0 : 33000,
        22.0 : 41000,
        23.0 : 50000,
        24.0 : 62000,
        25.0 : 75000,
        26.0 : 90000,
        27.0 : 105000,
        28.0 : 120000,
        29.0 : 135000,
        30.0 : 155000}
    return d.get(cr, 0)
        

def xpPerCharacter(difficulty, level):
    table = """25
50
75
125
250
300
350
450
550
600
800
1000
1100
1250
1400
1600
2000
2100
2400
2800

50
100
150
250
500
600
750
900
1100
1200
1600
2000
2200
2500
2800
3200
3900
4200
4900
5700

75
150
225
375
750
900
1100
1400
1600
1900
2400
3000
3400
3800
4300
4800
5900
6300
7300
8500

100
200
400
500
1100
1400
1700
2100
2400
2800
3600
4500
5100
5700
6400
7200
8800
9500
10900
12700""".split("\n\n")
    table = [w.split("\n") for w in table]
    return int(table[difficulty - 1][level])
    
def groupMultiplier(n):
    t = [((1,1), 1.0),
         ((2,2), 1.5),
         ((3, 6), 2.0),
         ((7,10), 2.5),
         ((11,14), 3.0),
         ((15, 1000), 4.0)]
    for ((low, high), multiplier) in t:
        if n <= high and n >= low:
            return multiplier
    return 4.0



def encounterXP(encounter):
    return sum([xpPerCR(hackFloat(d.get("challenge_rating", 0.0))) for d in encounter])
        
def generateOne(candidates, difficulty, xpThresholds, origEncounter=[]):
    if not(candidates):
        return []

    encounter = deepcopy(origEncounter)
# FIXME: what to do for xpthreshold 4??
    (lbound, ubound) = (xpThresholds[difficulty],xpThresholds[difficulty+1])
    ok = False
    origXP =encounterXP(origEncounter) * groupMultiplier(len(origEncounter))
    if origXP  >= ubound:
        print("Too hard by " + str(ubound - origXP) + " XP")
        return []
    
    while(not(ok)):
        current = random.choice(candidates)
        currentXP = xpPerCR(hackFloat(current.get("challenge_rating", 0.0)))
        xp = encounterXP(encounter)

        amount = random.choice(list(filter(lambda n: (encounterXP(encounter) + (n * currentXP)) * groupMultiplier(len(encounter) + n) <= ubound, range(21))))
        encounter += [current for i in range(amount)]
        xp = encounterXP(encounter) * groupMultiplier(len(encounter))
        if xp <= ubound and xp >= lbound:
            ok = True

        if xp > ubound:
            encounter = origEncounter

    return encounter

            

        
        


def unroll(xs):
    acc = []
    for (x, n) in xs:
        acc += [x for i in range(n)]

    return acc


def generator(ds):
    players = int(input("How many players: "))
    levels = [int(input("Level of player " + str(i) + ":")) for i in range(1, players + 1)]
    difficulty = int(input("How difficult?\n 1 - Easy\n 2 - Medium\n 3 - Hard\n 4 - Deadly\n"))
    xpThresholds = {diff : sum([xpPerCharacter(diff, level) for level in levels]) for diff in range(1, 5)}
    print("Threshold is " + str(xpThresholds[difficulty]) + "/" + str(xpThresholds[min(4, difficulty+1)]))
    averageLevel = ceil(sum(levels) / float(len(levels)))
    crThreshold = 2 * (averageLevel + 1)
    candidates = list(filter(lambda d: hackFloat(d.get("challenge_rating", "30")) <= crThreshold and hackFloat(d.get("challenge_rating", 30)) >= max(0.125, (averageLevel - 8.0)), ds))
    inp = ""
    filt = [""]
    picks = []
    while(True):
        narrowCandidates = list(filter(lambda d: any(map(lambda w: w in d.get("name", "").lower(), filt)), candidates))
        choice = generateOne(narrowCandidates, difficulty, xpThresholds, picks)
        for (name, count) in countDuplicates([d.get("name", "") for d in choice]):
            print(str(count) + " " + name)
        print(str(encounterXP(choice)*groupMultiplier(len(choice)))) 
        inp = input()
        if inp == "y":

            print("####")
            for (d, count) in countDuplicates(choice, "name"):
                print(mkInit(d, count))

            # we wait for an enter
            input()
        elif inp and inp[:4] == "pick":
            ws = inp[5:].split(",")
            try:
                picks = [(findByKey(candidates, "name", value, str.lower), int(n)) for (value, n) in [w.split(":") for w in ws]]
                picks = unroll(picks)
            except:
                print("Monster not found or incorrect format.")
                wait = input()
        elif inp == "clear":
            filt = [""]
            picks = []
        elif inp:
            filt = inp.split(",")
        else:
            filt = [""]
                
            

