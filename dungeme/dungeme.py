#!/usr/bin/python3
#
#  dungeme.py
#
# Command line tool for building and exploring of dungeons for tabletop RPG. Designed to be accessible for the visually impaired!
#

import os.path
from random import randrange
import json
import sys
import copy
from table import *

DEFAULTSKILLDICT = { "str" : "Strength", "dex" : "Dexterity", "con" : "Constitution", "int" : "Intelligence", "wis" : "Wisdom", "cha" : "Charisma" }

directions = "n ne e se s sw w nw up down".split()
opdir = "s sw w nw n ne e se down up".split()

def opposite(direction):
    d = {}
    for i in range(len(directions)):
        d[directions[i]] = opdir[i]

    return d[direction]

def yesnoInput(prompt):
    while True:
        w = input(prompt + " [y/n]:")
        if w == "y":
            return True
        if w == "n":
            return False
        

def multilineInput(prompt):
    w = input(prompt)
    ws = []
    while w:
        ws.append(w)
        w = input("> ")
    return "\n".join(ws)

def loadData(filename, data):
    data = json.load(open(filename))
    data[1] = {int(k) : Table.fromDict(v) for k,v in data[1].items()}
    return data

class State(object):
    def blueprint(skills):
        return '[{"skills" : ' + str(skills).replace("'", '"') + ', "table_map" : {}, "current_room" : "0", "next_id": 1, "rooms" : {"0":{"id":"0", "name":"Entry Point"}}, "edges" : {"0" : {}}}, {}]'
    
    def fromFile(filename):
        data = []
        data = loadData(filename, data)
        return State(data, filename)

    def __init__(self, data, filename):
        self.data = data[0]
        self.filename = filename
        self.tables = data[1]

        if not("next_id" in self.data):
            self.data["next_id"] = 1
        if not("rooms" in self.data):
            self.data["rooms"] = {}
        if not("edges" in self.data):
            self.data["edges"] = {}
        if not("table_map" in self.data):
            self.data["table_map"] = {}
        return

    def save(self):
        # note that json will turn dict keys into strings
        s = [self.data, {k : v.toDict() for k,v in self.tables.items()}]
        f = open(self.filename, "w")
        json.dump(s, f)
        f.flush()
        f.close()
        

    def quit(self):
        self.save()
        exit()

    def create(self, roomName):
        newRoom = { "id": str(self.data["next_id"]), "name" : roomName , 'skill_checks' : []}
        self.data["next_id"] += 1
        self.data["rooms"][newRoom["id"]] = newRoom
        self.data["edges"][newRoom["id"]] = {}

        if not("current_room" in self.data):
            self.data["current_room"] = "1"

        return newRoom

    def currentRoom(self):
        return self.data["rooms"][self.data["current_room"]]


    def _currentExits(self):
        room = self.currentRoom()
        acc = []
        exits = self.data["edges"][room["id"]]
        for (r2, paths) in exits.items():
            for path in paths:
                acc.append(path) 

        result = []
        for d in directions:
            if d in acc:
                result.append(d)

        return result


    def _edges(self, r):
        room = self.data["rooms"][r]
        acc = []
        exits = self.data["edges"][room["id"]]
        for (r2, paths) in exits.items():
            for path in paths:
                acc.append((room["id"], r2, path)) 

        return acc



    def _currentEdges(self):
        return self._edges(self.currentRoom()["id"])

    def exits(self):
        room = self.currentRoom()
        w = ""
        if not( room["id"] in self.data["edges"]):
            return "No room\n"

        exits = self._currentExits()

        if not(exits):
            return "No Exits"

        return ", ".join(exits)

    def shortDescription(self):
        room = self.currentRoom()
        w = room["name"] + " : " + room["id"] + "\n"
        w += self.exits()
        return w
        
    def look(self):
        print(self.shortDescription())

    def move(self, id):
        if not(id in self.data["rooms"]):
            print("Room not found.")
            return
            
        self.data["current_room"] = id


    def _connect(self, r1, r2, path):
        if not(r1 in self.data["edges"]):
            print("Room " + r1 + " does not seem to exist.")
            return

        if not(r2 in self.data["edges"][r1]):
            self.data["edges"][r1][r2] = [path]
        else:
            self.data["edges"][r1][r2].append(path)

    def connect(self, args):
        if len(args) != 3:
            print("Need more arguments to connect")
            return

        room1 = args[0]
        room2 = args[1]
        path = args[2]
        self._connect(room1, room2, path)
        
    def follow(self, direction):
        edges = self._currentEdges()
        for (r1, r2, path) in edges:
            if path == direction:
                self.move(r2)
                self.look()
                return
        print("No path in that direction.")
        return

    def dig(self, direction):
        if direction in self._currentExits():
            print("Path already exists.")
            return

        r1 = self.currentRoom()["id"]
        newname = input("name: ")
        r2 = self.create(newname)["id"]
        self._connect(r1, r2, direction)
        self._connect(r2, r1, opposite(direction))
        self.follow(direction)


    def disconnect(self, args):
        if len(args) != 2:
            print("Incorrect number of arguments to disconnect.")
            return
            
        self._disconnect(args[0], args[1])

    def _disconnect(self, r1, r2):
        if not(r1 in self.data["edges"]):
            print("Room one does not exist.")
            return

        r2d = self.data["edges"][r1]

        if not(r2 in r2d):
            print("Room two does not exist or is not connected.")
            return

        self.data["edges"][r1].pop(r2, None)
            
    def free(self, args):
        if not(args):
            r = self.currentRoom()["id"]
        else:
            r = args[0]

        self._free(r)

    def _free(self, r):
        # first edges going from the room
        if not(r in self.data["edges"]):
            print("Room does not seem to exist!")
            return

        self.data["edges"][r] = {}
        # now edges going to the room
        acc = []
        for(source, rd2) in self.data["edges"].items():
            for target in rd2.keys():
                if target == r:
                    acc.append((source, target))

        for (source, target) in acc:
            self._disconnect(source, target)


    def _deleteRoom(self, r):
        if not(r in self.data["rooms"]):
            print("Room did not exist.")
            return

        self._free(r)
        self._tableDeleteRoom(r)
        del self.data["rooms"][r]

    def deleteRoom(self, args):
        if not(args):
            r = self.currentRoom()["id"]
            exits = self._currentExits()
            if exits:
                self.follow(exits[0])
                self._deleteRoom(r)
                return
            else: # room has no exits
                self._deleteRoom(r)
                # we must be in some legal room so lets pick one
                rooms = self.data["rooms"]
                if rooms:
                    self.move(list(rooms.values())[0]["id"])
                    return
                else:
                    # we create a room since there is no other
                    self.data["next_id"] = 1
                    newRoom = self.create("Saferoom")
                    self.move(newRoom["id"])
                    return

        # otherwise just delete the room that was specified, unless its the current room
        if args[0] == self.currentRoom()["id"]:
            self.deleteRoom([])
            return

        self._deleteRoom(args[0])


    def _note(self, r, w):
        if not(r in self.data["rooms"]):
            print("Room does not exist.")
            return
            
        if not("notes" in self.data["rooms"][r]):
            self.data["rooms"][r]["notes"] = [w]
            return

        self.data["rooms"][r]["notes"].append(w)

    def _getNotes(self, r):
        return self.data["rooms"].get(r, []).get("notes", [])

    def makeNote(self, args):
        r = self.currentRoom()["id"]
        if args:
            self._note(r, " ".join(args))
            return

        inp = input()
        while(inp):
            self._note(r, inp)
            inp = input()                
                
        
    def readNotes(self, args):
        if args:
            r = args[0]
        else:
            r = self.currentRoom()["id"]

        for w in self._getNotes(r):
            print(w)

    def _deleteNote(self, r, n):
        if not(r in self.data["rooms"]):
            print("Room does not exist.")
            return

        if not( "notes" in self.data["rooms"][r]) or not(self.data["rooms"][r]["notes"]):
            print("No notes to delete.")
            return

        if len(self.data["rooms"][r]["notes"]) < n:
            print("Wrong note number.")
            return

        del self.data["rooms"][r]["notes"][n]

    def deleteNote(self, args):
        # we only do this in the current room, otherwise its too confusing with the numbers
        r = self.currentRoom()["id"]
        notes = self._getNotes(r)
        if len(notes) == 0:
            print("No notes to delete.")
            return
            
        if len(notes) == 1: # quick mode
            self._deleteNote(r, 0)
            return

        #otherwise we query for the number
        for i in range(len(notes)):
            print(str(i) + " : " + notes[i])

        inp = input("Delete:")
        if not(inp.isnumeric()):
            print("Wrong choice.")
            return

        choice = int(inp)
        self._deleteNote(r, choice)

    def _setDescription(self, r, w):
        if not(r in self.data["rooms"]):
            print("Room does not seem to exist.")
            return

        self.data["rooms"][r]["description"] = w

    def setDescription(self, args):
        r = self.currentRoom()["id"]
        if args:
            self._setDescription(r, " ".join(args))
            return

        w = ""
        inp = input()
        while(inp):
            w += inp + "\n"
            inp = input()

        self._setDescription(r, w)
                
    def showDescription(self):
        print(self.currentRoom().get("description", "No Description."))
        return
    def _tableNextId(self):
        ks = sorted(self.tables.keys())
        if ks:
            return ks[-1] + 1
        return 1

    def _tableMapToRoom(self, tableId, roomId):
        # map a table to a room, though the dict is the other way around
        if not(tableId in self.tables):
            print("Error: Table with id " + str(tableId) + " not found.")
            return

        if not(roomId in self.data["rooms"]):
            print("Error: Room with id " + str(roomId) + " not found.")
            return
        
        tm = self.data["table_map"]
        if roomId in tm:
            ts = tm[roomId]
            if tableId in ts:
                #no duplicates, but we don't need to advertise this i think
                return
            ts.append(tableId)
        else:
            tm[roomId] = [tableId]
        return

    def _tablesForRoom(self, roomId):
        return self.data["table_map"].get(roomId, [])

    def _tableMapRemoveFromRoom(self, tableId, roomId):
        # remove all mappings to a table from a room
        # sanity check
        if not(roomId in self.data["rooms"]):
            return (False, "Room does not seem to exist.")

        if not(tableId in self.tables):
            return (False, "Table does not seem to exist.")
               
        tm = self.data["table_map"]
        if not(roomId in tm):
            return (False, "Room has no tables, so none were removed.")

        ts = tm[roomId]
        if not(tableId in ts):
            return (False, "Table is not part of room. Nothing removed.")
        tm[roomId] = list(filter(lambda id: id != tableId, ts))
        return (True, "")

    def _tableDeleteRoom(self, roomId):
        # called because a room is being deleted, dropds a room entry from the table mapping
        tm = self.data["table_map"]
        if roomId in tm:
            del tm[roomId]
        return
    
    def tableNew(self, args):
        t = mkTableDialogue()
        id = self._tableNextId()
        self.tables[id] = t
        
        # if no arg, add table to current room
        if len(args) == 0:
            # we map rooms to tables
            self._tableMapToRoom(id, self.currentRoom()["id"])#self.data["table_map"][self.currentRoom()["id"]] = id
        elif args[0].isnumeric():
            # arg given is specific roomid or -1 for don't attach
            n = args[0]
            if int(n) >= 0:
                if not(n in self.data["rooms"]):
                    print("Could not attach table to room " + str(n) + ": Room does not exist.")
                else:
                    self._tableMapToRoom(id, n) #self.data["table_map"][n] = id
                    
        editTableDialogue(t)
        return


    def _tableList(self, tableItems):
        print("Id\tName\tType\tDescription")
        w = ""
        for (id, t) in tableItems:
            w += str(id) + "\t"
            w += t.name() + "\t"
            w += t.type() + "\t"
            w += t.description() + "\n"
        return w
    
    def tableGlobalList(self, args):
        print(self._tableList(self.tables.items()))
        return

    def _tableDelete(self, tableId):
        # deletes a table
     
        # remove all mappings from rooms
        for roomId in self.data["table_map"].keys():
            self._tableMapRemoveFromRoom(tableId, roomId)

        if tableId in self.tables:
            del self.tables[tableId]
        return
    
    def tableDelete(self, args):
        if not(args) or not(args[0].isnumeric()): 
            print("Please specify a valid table id (see tgl command)")
            return

        n = int(args[0])
        if not(n in self.tables):
            print("Table with id " + str(n) + " not found. Check tgl for list of tables and their ids")
            return
                
        # all checks out, remove table and all its mappings
        byeTable = self.tables[n].name()
        self._tableDelete(n)
        print("Goodbye table '" + byeTable + "'.")
        return
    def _tableRoll(self, tableId):
        if not(tableId in self.tables):
            print("Error: Could not roll on table. No table with id " + str(tableId) + ".")
            return ""
        return self.tables[tableId].roll()
        

        
    def tableRoll(self, args):
        # roll on table in room if no arg
        tm = self.data["table_map"]
        if not(args):
            roomId = self.currentRoom()["id"]
            ts = self._tablesForRoom(roomId)
            if not(ts):
                print("Room has no tables. Please specify a table ID (see tgl command) to roll on a table.")
                return
            elif len(ts) > 1:
                # give a selection
                print(self._tableList([(tid, self.tables[tid]) for tid in ts]))
                inp = input("Pick a table to roll on:")
                if not(inp.isnumeric()):
                    print("Please specify a valid table id.")
                    return
                tableId = int(inp)
            else:
                # only one table in room
                tableId = ts[0]
        else: # argument was specified
            if not(args[0].isnumeric()):
                print("Please specify a table id as argument.")
                return
            tableId = int(args[0])
            if not(tableId in self.tables):
                print("No such table with id " + str(tableId) + ".")
                return

        # finally, all checks out
        print(self.tables[tableId].name() + ": " + self._tableRoll(tableId) )
        return
    def _tableEdit(self, tableId):
        if not(tableId in self.tables):
            print("Error: Cannot edit table. Table with id " + str(tableId) + " not found.")
            return
        editTableDialogue(self.tables[tableId])
        return

    def tableEdit(self, args):
        #if no args, try to find a table in the current room
        if not(args):
            ts = self._tablesForRoom(self.currentRoom()["id"])
            if not(ts):
                print("No table to edit. Either go to a room with a table or specify the table id.")
                return
            elif len(ts) > 1:
                # more than 1 table, offer a choice
                self._tableList([(tid, self.tables[tid]) for tid in ts])
                inp = input("More than 1 table in room. Specify id to edit:")
                if not(inp.isnumeric()):
                    print("Not a valid table id.")
                    return
                tableId = int(inp)
                if not(tableId in ts):
                    print("That id is not of a table in this room.")
                    return
            else: # ts is exactly one element
                tableId = ts[0]
        else: # args has elements
            if not(args[0].isnumeric()):
                print("Please specify a valid table id.")
                return
            tableId = int(args[0])

        # all checks out, _tableEdit checks for existence of table
        self._tableEdit(tableId)
        return

    def tableAdd(self, args):
        if not(args):
            print("No table id specified. If you want to create a new table and add it to this room, try using tn.")
            return

        if not(args[0].isnumeric()):
            print("Please specify a valid table id as a first argument.")
            return

        tableId = int(args[0])
        if len(args) == 1:
            # no roomId was specified, try using current room
            roomId = self.currentRoom()["id"]
        else:
            if not(args[1].isnumeric()):
                print("Please specify a valid room id as a second argument, or specify no argument to add the table to the current room.")
                return
            roomId = args[1]
        # all checks out, tableId and roomId will be verified in _tableMapToRoom
        self._tableMapToRoom(tableId, roomId)
        return

    def tableRemove(self, args):
        tableId = False
        #if no args, try to remove the current room's table from the room
        if not(args):
            roomId = self.currentRoom()["id"]
            ts = self._tablesForRoom(roomId)
            if not(ts):
                print("No tables to remove from this room. Specify arguments to remove specific table from specific room")
                return
            elif len(ts) > 1:
                print(self._tableList([(tid, self.tables[tid]) for tid in ts]))
                inp = input("Pick a table to remove from this room:") # is processed later
            else: # ts has exactly one element
                tableId = ts[0]
        elif len(args) == 1: # tableId was specified
            inp = args[0] # processed later
            roomId = self.currentRoom()["id"]
        else: # tableid and roomid were specified
            inp = args[0]
            roomId = args[1]
        # sanitize tableId input from either argument or menu
        if not(tableId):
            if not(inp.isnumeric()):
                print("Please specify a valid table id.")
                return
            else:
                tableId = int(inp)
            
        # all checks out, remove table from room
        (success, msg) = self._tableMapRemoveFromRoom(tableId, roomId)
        if not(success):
            print(msg)
            return
        print("Ok. Table '" + self.tables[tableId].name() + "' removed from room " + roomId + ".")
        return

    def tableList(self, args):
        if not(args):
            roomId = self.currentRoom()["id"]
        else:
            w = args[0]
            if not(w in self.data["rooms"]):
                print("Room " + w + " not found.Please specify a valid room id.")
                return
            roomId = w

        if not(self._tablesForRoom(roomId)):
            print("No tables for " + self.data["rooms"][roomId]["name"] + ".")
            return
        print(self._tableList([(tid, self.tables[tid]) for tid in self._tablesForRoom(roomId)]))
        return

    def _skillAdd(self, roomId, skillCheckList):
#        (skillKey, dc, name, description, success, failure) = tuple(skillCheckList)
        skillKey = skillCheckList[0]
        # add a skillcheck to a room
        if not(roomId in self.data["rooms"]):
            print("Room not found.")
            return

        if not(skillKey in self.data["skills"]):
            print("Not a valid skill identifier.")
            return

        self.data["rooms"][roomId]["skill_checks"].append(skillCheckList)
        return

    def _skillRemove(self, roomId, i):
        if not(roomId in self.data["rooms"]):
            print("Room not found.")
            return
        skillChecks = self._skillsForRoom(roomId)
        if len(skillChecks) <= i:
            print("Could not remove skill: index out of bounds.")
            return

        del skillChecks[i]
        return

    def _skill(self, skillKey):
        return self.data["skills"].get(skillKey, "")

    def _skillsForRoom(self, roomId):
        if not(roomId in self.data["rooms"]):
            print("Room not found.")
            return
        return self.data["rooms"][roomId].get("skill_checks", [])

    def skillAdd(self, args):
        # adds a skill to a room, always uses the current room
        # a skill check is a tuple of skillKey, dc, name, description, success and failure.
        
        room = self.currentRoom()
        #prompt for skill type
        skillkey = ""
        while not(skillkey  in self.data['skills']):
            for (k, s) in self.data['skills'].items():
                print("  " + k + ") " + s)
            skillkey = input("Enter choice of skill:")
            if skillkey == "q":
                print("Aborting.")
                return
                  
        #DC
        dc = ""
        while not(dc.isnumeric()):
            dc = input("Difficulty of skill check:")
            if dc == "q":
                print("Aborting.")
                return

        dc = int(dc)
        #name
        name = input("How to name this skillcheck:")
        #description, success and failure
        description = multilineInput("Enter description (two newlines to submit, empty newline to skip):\n")
        success = multilineInput("Enter success result:\n")
        failure = multilineInput("Enter failure result:\n")

        # all checks out
        self._skillAdd(self.currentRoom()['id'], [skillkey, dc, name, description, success, failure])
        return

    def _skillShow(self, skillCheckList):
        # return a string that can describe a given skillchecks
        (skillKey, dc, name, desc, success, failure) = tuple(skillCheckList)
        w = "\n"
        w += name + "\nDC " + str(dc) + " " + self.data["skills"][skillKey] + " check\n"
        if desc:
            w += desc + "\n"
        if success:
            w += "On success: " + success + "\n"
        if failure:
            w += "On Failure: " + failure + "\n"
        return w

    def skillList(self, args):
        # list skills for current room, no args
        skillChecks = self._skillsForRoom(self.currentRoom()['id'])
        if not(skillChecks):
            print("No skillchecks in this room.")
            return

        # currently we give a longform description for all skillchecks
        for s in skillChecks:
            print(self._skillShow(s))
        return 

    def _skillShort(self, skillCheckList):
        s = skillCheckList
        return s[2] + " (DC " + str(s[1]) + " " + self._skill(s[0]) + " check)"
    
    def skillDelete(self, args):
        # prompts skills of current room for removal
        roomId = self.currentRoom()['id']
        skillchecks = self._skillsForRoom(roomId)
        if not(skillchecks ):
            print("No skill checks in current room.")
            return
        elif len(skillchecks) == 1:
            if yesnoInput("Really remove " + self._skillShort(skillchecks[0]) + "?"):
                self._skillRemove(roomId, 0)
                print("Ok. Skill removed.")
            else:
                return
        else: # there are multiple skillchecks present
            for i in range(0, len(skillchecks)):
                print(str(i) + " : " + self._skillShort(skillchecks[i]))
            w = input("Enter which skill to remove from this room:")
            if not(w.isnumeric()):
                print("Please enter a valid skill check number as above.")
                return

            print("Goodbye skill check " + self._skillShort(skillchecks[int(w)]) + "!")
            self._skillRemove(roomId, int(w))
            return
                

            
            ########
# Some friend functions
#########

def numRooms(s):
    return len(s.data["rooms"])

def transferTables(s1, s2):
    """Adds tables from s1 state S1 to state S2. Does not maintain table mappings, or table Ids. Does not add table from S1 if a table in S2 is present with the same name and type."""
    if not(s2.tables):
        s2.tables = s1.tables
        return

    for (_, t1) in s1.tables.items():
        add = True
        for (_, t2) in s2.tables.items():
            if (t1.name() == t2.name()) and (t1.type() == t2.type()):
                add = False
                break
        if add:
            s2.tables[s2._tableNextId()] = t1
    return 

########
# Commands
#######


commands_full = {
    "help" : (["Print this help"], lambda s, ws: print(mkHelp())),
    "q" : (["Exit dungeme saving all changes."], lambda s, ws: s.quit()),
    "create" : (["ROOMNAME", "Create a new room with name ROOMNAME."], lambda s, ws: s.create(ws[0])),
    "l" : (["Look. Give a short description of the current room."],lambda s, ws: s.look()),
    "move" : (["ROOMID", "Move to another room by number."], lambda s, ws: s.move(ws[0])),
    "connect" : (["ROOMID1", "ROOMID2","PATH","Connects two rooms by a path. Will create a path from room with ROOMID1 to room with ROOMID2. Path can be the usual n,e,s,w,up,down,ne,se,sw,nw etc."], lambda s, ws: s.connect(ws)),
    "disconnect" : (["ROOMID1","ROOMID2","Remove paths between rooms. Will remove all paths going from room with ROOMID1 to room with ROOMID2."], lambda s, ws: s.disconnect(ws)),
    "free" : (["[ROOMID[","Removes all paths going out from a room. If no argument is specified, frees the curren room from paths, otherwise will free room with ROOMID."], lambda s, ws: s.free(ws)),
    "delete" : (["[ROOMID]","Completely erases a room. This removes all the rooms paths, going in and out, as well as all descriptions and other contents. Will delete the current room if no argument is specified, room with ROOMID otherwise."], lambda s, ws: s.deleteRoom(ws)),
    "a" : (["[WORDS]","Adds a note to the current room. If arguments are supplied, they are added as a one liner note, otherwise, with no arguments, will enter a multi-line note input mode. Finish the note with two newlines."], lambda s, ws: s.makeNote(ws)),
    "note" : (["[WORDS]", "Same as 'a'."], lambda s, ws: s.makeNote(ws)),
    "r" : (["[ROOMID]", "Read notes for a room. Specify by ROOMID argument, or no argument for current room."], lambda s, ws: s.readNotes(ws)),
    "dnote" : (["ROOMID", "NOTEID", "Delete a note from a room. First argument specifies the room, the second argument specifies the number of the note in that room. You can see the notenumber/id by using 'r'. You must specify both arguments explicitly."], lambda s, ws: s.deleteNote(ws)),
    "d" : (["Show long description of current room."], lambda s, ws: s.showDescription()),
    "sd" : (["[WORDS]", "Set the description for the current room. If arguments are specified, they are used as a one liner description. Otherwise, a multi line edit mode is entered. Finish the description with two newlines."], lambda s, ws: s.setDescription(ws)),
    "tn" : (["[ROOMID]", "Table new. Create a new table. If no argument is specified, will add that table to the current room. If ROOMID is specified and positive, will connect that table to the room with ROOMID, if negative, will not connect table with any room (it's in the global list, see tgl)"], lambda s, ws: s.tableNew(ws)),
    "tgl" : (["Table global list. List all tables and their id."], lambda s, ws: s.tableGlobalList(ws)),
    "tdelete" : (["TABLEID", "Table delete. Removes a table based on id (see tgl). Removes all contents of the table and all references to the table from rooms."], lambda s, ws: s.tableDelete(ws)),
    "tr" : (["[TABLEID]", "Table roll. Rolls on the table in the current room if TABLEID is not specified. If it is specified, rolls on that table. If the current room has multiple tables you will be given a selection."], lambda s, ws: s.tableRoll(ws)),
    "te" : (["[TABLEID]", "Table edit. If no argument is specified, will pick table from current room. Otherwise, opens edit dialogue for specified TABLEID."], lambda s, ws: s.tableEdit(ws)),
    "ta" : (["TABLEID", "[ROOMID]", "Table add. Adds an existing table, specified by TABLEID, to a room. If ROOMID is specified, add table to that room if it exists, otherwise, adds table to the current room."], lambda s, ws: s.tableAdd(ws)),
    "tremove" : (["[TABLEID | TABLEID ROOMID]", "Table remove. Removes a table from a room, though the table itself remains in the global list. If no arguments are specified, tries to find a table in the current room and remove it. If TABLEID is specified on its own, tries to remove a table with that id from the current room. If both TABLEID and ROOMID are specified, tries to remove the specified table from the specified room."], lambda s, ws: s.tableRemove(ws)),
    "tl" : (["[ROOMID]", "Table list. List tables for a specific room. If ROOMID is not specified, lists tables for the current room. For a global list of tables, see tgl."], lambda s, ws: s.tableList(ws)),
        "sa" : (["Skillcheck Add. Add a skillcheck to the current room. Includes name, dc, description, success and failure states. All parameters acquired via prompt."], lambda s, ws: s.skillAdd(ws)),
            "sl" : (["Skillcheck list. List all skillchecks in current room."], lambda s, ws: s.skillList(ws)),
                "sdelete" : (["Skillcheck delete. Delete a skillcheck from a room. Will prompt for skill check to remove, if any."], lambda s, ws: s.skillDelete(ws))
    }


# we don't want to use the documentation internally
commands = {key : value[1] for (key, value) in commands_full.items()}

for d in directions:
    commands[d] = lambda s, ws, x=d: s.follow(x)
    commands["d" + d] = lambda s, ws, y=d: s.dig(y)

commands_info = {key : value[0] for (key, value) in commands_full.items()}
dirstring = ", ".join(directions)
commands_info[dirstring] = ["Standard movement commands. Will move in that direction if a path exists from current room."]
digstring = ", ".join(["d" + w for w in directions])
commands_info[digstring] = ["Dig in a direction. Exists for all standard movement directions and will 'dig' a path into that direction from the current room."]

def mkHelp():
    out = ""
    for (command, args) in commands_info.items():
        out += "  " + command
        n = len(args)
        if n != 1: # has args and not just description
            for i in range(n-1):
                out += " " + args[i]
                
        #in any case, append description
        out += " - " + args[-1] + "\n"
        
    return out
        

def mkProgramHelp():
    out = "dungeme.py - Dungeon control system\nUsage: dungeme.py [OPTIONS] DUNGEONFILE\n\nOptions\n -c - Create a new empty DUNGEONFILE, do not open an existing one.\n -t, --merge-tables TABLEFILE - Merges all tables found in TABLEFILE into DUNGEONFILE before opening DUNGEONFILE. Does not replace tables or add duplicates. TABLEFILE is a regular dungeon file.\n --help - Print this help.\n\nIf a dungeonfile is specified, dungeme will enter into editor mode with the following commands:\n" + mkHelp()
    return out

def getSkillDictFromFile(skillfile):
    f = open(skillfile, "r")
    ws = f.read().split("\n")
    d = {}
    for line in ws:
        words = line.split("\t")
        if len(words) < 2:
            continue
        d[words[0]] = words[1]
    f.close()
    return d


def createDungeonfile(file, skillfile=None):
    f = open(file, "w")
    if skillfile:
        skills = getSkillDictFromFile(skillfile)
    else:
        skills = DEFAULTSKILLDICT
        
    f.write(State.blueprint(skills))

    f.flush
    

def main(argv):
    if (len(argv) == 1) or ((len(argv) > 1) and (argv[1] == "--help")):
        print(mkProgramHelp())
        return
    file = argv[-1]
    
    # for creating empty dungeonfile
    if (len(argv) > 1) and (argv[1] == "-c"):
        if os.path.isfile(file):
            print("Aborting: Cannot create empty dungeonfile '" + file + "'. File exists.")
            return
        if (len(argv) > 3) and (argv[-1] != argv[-2]):
            skillfile = argv[-2]
            if not(os.path.isfile(skillfile)):
                print("Skillfile not found.")
                return
        else:
            skillfile = ""
            
        createDungeonfile(file, skillfile)

    state = State.fromFile(file)
        
    if (len(argv) > 2) and ((argv[1] == "-t") or (argv[1] == "--merge-tables")):
        tableFile = argv[2]
        if not(os.path.isfile(tableFile)):
            print("Error: Could not find file '" + tableFile + "' to merge tables from.")
            return
        tableState = State.fromFile(tableFile)
        print("Merging tables...")
        transferTables(tableState, state)


    print("Ok. " + str(numRooms(state)) + " room(s) loaded. Enter command. Type 'h' for help.")
    while(True):
        backup = copy.deepcopy(state)
        w = input()
        if w:
            ws = w.split()
            if ws[0] in commands:
                try:
                    commands[ws[0]](state, ws[1:])
                except:
                    backup.save()
                    raise
                    
            else:
                print("Unrecognized command.")
        

if (__name__ == "__main__"):
    main(sys.argv)




def dir2(x):
    for w in dir(x):
        if(w[0] != "_"):
            print(w)
            

