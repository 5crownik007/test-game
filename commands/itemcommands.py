from commands.command import Command
from evennia import CmdSet, utils
from evennia import default_cmds
from evennia.utils.evmenu import get_input
from django.conf import settings

_SEARCH_AT_RESULT = utils.object_from_module(settings.SEARCH_AT_RESULT)

class CmdEatEdible(Command):
    key = "eat"
    aliases = ["eat","consume","ingest","swallow"]
    def func(self):
        self.caller.msg("You eat the %s." % self.obj.key)
        self.obj.delete()

class CmdSetEdible(CmdSet):
    key = "ediblecmdset"
    duplicates = True
    def at_cmdset_creation(self):
        self.add(CmdEatEdible())

class CmdDispense(Command):
    key = "get from"
    aliases = ["use dispenser","dispense from"]
    def func(self):
        if not self.obj.access(self.caller, "get from"):
            if self.obj.db.get_itm_err_msg:
                self.caller.msg(self.obj.db.get_itm_err_msg)
            else:
                self.caller.msg("You're not allowed to get anything from that.")
        else:
            self.obj.get_item(self.caller)

class CmdSetDispenser(CmdSet):
    key = "dispensercmdset"
    duplicates = True
    def at_cmdset_creation(self):
        self.add(CmdDispense())

class CmdLockDoor(Command):
    #This command lets the user lock and unlock complex doors.
    key = "door lock"
    aliases = ["lock door","unlock door","close door","open door"]
    priority = 1
    locks = "cmd:all()"
    def func(self):
        #The actual door handles the method by which it is opened, so we just call the door's locking
        # and unlocking function.
        self.obj.lockingmethod(self.caller)

#class CmdTestInput(Command):
#    key = "test getinput"
#    def func(self):
#        get_input(self.caller, "This is a test: ", self.received)
#    
#    def received(self, caller, prompt, received):
#        caller.msg(f"You sent us: {received}")

class CmdSetComDoor(CmdSet):
    key = "comdoorcmdset"
    duplicates = True
    def at_cmdset_creation(self):
        self.add(CmdLockDoor())
#        self.add(CmdTestInput())

class CmdDoorPressButton(Command):
    key = "press button"
    aliases = ["button","push button","click button"]
    locks = "cmd:all()"
    def func(self):
        targets = utils.search.search_object(self.obj.db.frequency,attribute_name="frequency")
        if len(targets) <1:
            return
        else:
            for target in targets:
                if target.key == self.obj.key:
                    pass
                else:
                    target.lockingmethod(self.obj)
        self.caller.msg("You press the button.")

class CmdSetButton(CmdSet):
    key = "doorbuttoncmdset"
    duplicates = True
    def at_cmdset_creation(self):
        self.add(CmdDoorPressButton())