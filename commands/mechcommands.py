from commands.command import Command
from evennia import CmdSet
from evennia import default_cmds

class MechStrike(Command):
    key = "strike"
    aliases = ["hit", "smash", "slam"]
    def func(self):
        caller = self.caller
        location = caller.location
        if not self.args:
            message = "You need a target to strike!"
            location.msg_contents(message)
            return
        
        target = caller.search(self.args.strip())
        if target:
            message = "The mech strikes %s!" % target.key
            location.msg_contents(message)

class MechCmdSet(CmdSet):
    key = "mechcmdset"
    def at_cmdset_creation(self):
        self.add(MechStrike())