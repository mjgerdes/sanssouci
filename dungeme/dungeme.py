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


directions = "n ne e se s sw w nw up down".split()
opdir = "s sw w nw n ne e se down up".split()

def opposite(direction):
    d = {}
    for i in range(len(directions)):
        d[directions[i]] = opdir[i]

    return d[direction]

def loadData(filename, data):
    data = json.load(open(filename))
    data[1] = {int(k) : Table.fromDict(v) for k,v in data[1].items()}
    return data

class State(object):
    blueprint = '[{"table_map" : {}, "current_room" : "0", "next_id": 1, "rooms" : {"0":{"id":"0", "name":"Entry Point"}}, "edges" : {"0" : {}}}, {}]'
    
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
        newRoom = { "id": str(self.data["next_id"]), "name" : roomName }
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
        tm = self.data["table_map"]
        if roomId in tm:
            ts = tm[roomId]
            ts.append(tableId)
        else:
            tm[roomId] = [tableId]
        return

    def _tablesForRoom(self, roomId):
        return self.data["table_map"].get(roomId, [])

    def _tableMapRemoveFromRoom(self, tableId, roomId):
        # remove all mappings to a table from a room
        tm = self.data["table_map"]
        if not(roomId in tm):
            return (False, "Room does not exist or has no tables.")

        ts = tm[roomId]
        if not(tableId in ts):
            return (False, "Table was not part of room.")
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
        if tableId in self.tables:
            del self.tables[tableId]
        
        # remove all mappings from rooms
        for roomId in self.data["table_map"].keys():
            self._tableMapRemoveFromRoom(tableId, roomId)
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
            ts = tm.get(roomId, [])
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
            ts = self.data["table_map"].get(self.currentRoom()["id"], [])
            if not(ts):
                print("No table to edit. Either go to a room with a table or specify the table id.")
                return
            elif len(ts) > 1:
                # more than 1 table, offer a choice
                self._tableList(ts)
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
    
            
            
########
# Some friend functions
#########

def numRooms(s):
    return len(s.data["rooms"])

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
                    "te" : (["[TABLEID]", "Table edit. If no argument is specified, will pick table from current room. Otherwise, opens edit dialogue for specified TABLEID."], lambda s, ws: s.tableEdit(ws))
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
    out = "dungeme.py - Dungeon control system\nUsage: dungeme.py [OPTIONS] DUNGEONFILE\n\nOptions\n -c - Create a new empty DUNGEONFILE, do not open an existing one.\n --help - Print this help.\n\nIf a dungeonfile is specified, dungeme will enter into editor mode with the following commands:\n" + mkHelp()
    return out

def createDungeonfile(file):
    f = open(file, "w")
    f.write(State.blueprint)
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
        createDungeonfile(file)

    state = State.fromFile(file)
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
            
