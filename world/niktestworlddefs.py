import random
from evennia import CmdSet, Command, DefaultRoom, DefaultObject
from evennia import utils, create_object, search_object
from evennia import syscmdkeys, default_cmds
from django.conf import settings
_SEARCH_AT_RESULT = utils.object_from_module(settings.SEARCH_AT_RESULT)

#This file will contain typeclasses and commands for the whole testworld, just to keep everything in one place.
#Also, I'm ripping a lot of this out of the tutorial world, but I'm not just copypasting. I'm reading and writing it myself with my own comments so I actually
# (hopefully) understand what's going on here.

#####COMMANDS#####

#This command is the "detail" command, which essentially lets us add little individual details to rooms without having to give them actual database objects
# to be tracked with. EG: you might have a room that is a cabin, with a table and chair. When [l]ooking, you get the desc of the cabin, but you can also
# [l]ook at the table or chair. Their descriptions are stored as details in a dictionary that is part of the room, rather than on a chair object and a table
# object. Useful for describing things that don't need their own object but should be separate from each other.
class CmdNikDetail(default_cmds.MuxCommand):
    key = "@detail"
    locks = "cmd:perm(builder)"
    help_category = "NikTestWorld"
    
    def func(self):
        if not self.args or not self.rhs:
            self.caller.msg("|rUsage: @detail key = details|n")
            return
        if not hasattr(self.obj, "set_detail"):
            self.caller.msg("Details cannot be set on %s." % self.obj)
            return
        for key in self.lhs.split(";"):
            self.obj.set_detail(key, self.rhs)
        self.caller.msg("Detail set: '%s':'%s'" % (self.lhs,self.rhs))

#This is a copy of the look code, except with the ability to see details spliced into the process. 
class CmdNikLook(default_cmds.CmdLook):
    caller = self.caller
    args = self.args
    if args:
        #Creates a list of things which we could possibly be wanting to look at
        looking_at_obj = caller.search(args,candidates=caller.location+caller.contents,use_nicks=True,quiet=True)
        #If there's more than one thing in the list, we have a multimatch and will need to handle it
        #If there's less than one thing in the list(zero), we have no matches. Both cases are handled below.
        if len(looking_at_obj) != 1:
            detail = self.obj.return_detail(args)
            if detail:
                self.caller.msg(detail)
                return
            else:
                _SEARCH_AT_RESULT(looking_at_obj, caller, args)
                return
        else:
            #Since there's only one match, that's the thing we're looking at.
            looking_at_obj = looking_at_obj[0]
    else:
        #If we just typed "look" with no arguments, it tries to look at our location. If we don't have one, it lets us know.
        looking_at_obj = caller.location
        if not looking_at_obj:
            caller.msg("You have no location to look at!")
    #If the thing we're looking at doesn't have the "return_appearance" function, then it's probably an account, so let's look at that account's character
    if not hasattr(looking_at_obj, "return_appearance"):
        looking_at_obj = looking_at_obj.character
    #If we're not allowed to view the thing, then we're not gonna find it.
    if not looking_at_obj.access(caller, "view"):
        caller.msg("Could not find '%s'." % args)
        return
    #Find its appearance and send it to us.
    caller.msg(looking_at_obj.return_appearance(caller))
    #at_desc is a function that the object runs if it gets looked at. Normally just passes, but an example where this could be used is Gorgon. If you
    # look at it, then it will turn you to stone.
    looking_at_obj.at_desc(looker=caller)
    return

class NikTestCmdSet(CmdSet):
    key = "niktest_cmdset"
    priority = 1
    def at_cmdset_creation(self):
        self.add(CmdNikLook())
        self.add(CmdNikDetail())

#STUB
class CmdMeleeWeaponAttack(Command):
    key = "hit"
    alises = ["strike","smash","bash","crush","batter","beat"]

    args = self.args


#####ROOMS#####

#First, I'll be getting the detail code from the tutorial world, but I also plan to have a few extra properties, namely: A) hazards and B) combat status
#Hazards will be the things in the room that will kill things inside the room, or things entering the room, unless they have certain qualities. For
# example, if you enter a room in vacuum without a vacuum suit, you will die.
#Combat status will mean tracking 1) if the room is in a combat, 2) whose turn is when and 3) what the level of engagement the combat is at(stealth, alarmed, fight)
#I don't want to do a real time combat system because I dislike making people scramble to type when they're trying to read text. It's incredibly aggravating.
#Hence, I want to do a turn based system. This might be a little ambitious, but I'm sure I can pull it off.
class NikRoom(DefaultRoom):
    #Adds commands & some attributes that will come in handy later ;)
    def at_object_creation(self):
        #Technically, the commands you have while inside the rooms are actually tied to the rooms, and not your character. Very nice.
        self.cmdset.add_default(NikTestCmdSet)

        self.db.hazards = []
        self.db.combatstatus = 0
        self.db.turnorder = []
        self.db.turn = 0
    #This will tell other things in the room when something arrives in that room.
    def at_object_receive(self, new_arrival, source_location):
        if new_arrival.has_account and not new_arrival.is_superuser:
            for obj in self.contents_get(exclude=new_arrival):
                if hasattr(obj, "at_new_arrival"):
                    obj.at_new_arrival(new_arrival)
    #When someone asks for our details, send 'em back.
    def return_detail(self, detailkey):
        details = self.db.details
        if details:
            return details.get(detailket.lower(), None)
    #When someone writes our details, take 'em in.
    def set_detail(self, detailkey, details):
        if self.db.details:
            self.db.details[detailkey.lower()] = details
        else:
            self.db.details = {detailkey.lower(): details}

#The intro room. This will give our character certain properties that will be needed later.
SUPERUSER_WARNING = (
    "\nWARNING: You are playing as a superuser ({name}). Use the {quell} command to\n"
    "play without superuser privileges (many functions and puzzles ignore the \n"
    "presence of a superuser, making this mode useful for exploring things behind \n"
    "the scenes later).\n"
)

class NIntroRoom(NikRoom):
    def at_object_receive(self, character, source_location):
        health = 5
        if character.has_account:
            character.db.health = health
            character.db.maxhealth = health
            character.db.wounds = []
        if character.is_superuser:
            string = "-" * 78 + SUPERUSER_WARNING + "-" * 78
            character.msg("|r%s|n" % string.format(name=character.key, quell="|wquell|r"))
        else:
            if character.account:
                character.account.execute_cmd("quell")
                character.msg("(Auto-quelling for this game.)")

#Clears the user of any properties the Intro room or other rooms gave them, as well as any inventory items.
class NOutroRoom(NikRoom):
    def at_object_receive(self, character, source_location):
        if character.has_account:
            del character.db.health
            del character.db.maxhealth
            del character.db.wounds
            for obj in character.contents:
                if "niktestworlddefs" in obj.typeclass_path:
                    obj.delete()
            character.tags.clear(category="nik_world")
        if self.db.autoexit && not character.is_superuser:
            character.move_to(self.db.autoexit,quiet=True)
            
    def at_object_leave(self, character, destination):
        if character.account:
            character.account.execute_cmd("unquell")

#####OBJECTS#####
class NikObject(DefaultObject):
    #This object can be sent back to where its home is, which should be where it was created.
    def reset(self):
        self.location = self.home

#STUB
class Melee(NikObject):
    def at_object_creation(self):
        self.db.damagemin = 0
        self.db.damagemax = 0

#STUB
class Ranged(NikObject):
    def at_object_creation(self):
        self.db.damagemin = 0
        self.db.damagemax = 0
        self.db.range = 0
        self.db.ammunition = 0

#STUB
class Wrench(Melee):
    def at_object_creation(self):
        super().at_object_creation()

#STUB
class Apparel(NikObject):
    def at_object_creation(self):
        self.db.hazardprot = []
        self.db.armour = 0

#STUB
class Spacesuit(Apparel):
    def at_object_creation(self):
        super().at_object_creation()

#STUB
class Keycard(NikObject):
    def at_object_creation(self):
        self.db.access = none