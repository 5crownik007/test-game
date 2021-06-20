from typeclasses.objects import Object
from commands.mechcommands import MechCmdSet
from evennia import default_cmds

class Mech(Object):
    def at_object_creation(self):
        self.cmdset.add_default(default_cmds.CharacterCmdSet)
        self.cmdset.add(MechCmdSet, permanent=True)
        self.locks.add("puppet:all();call:false()")
        self.db.desc = "This is a mechanical being, also known as a 'mech'."
        self.db.health = 10