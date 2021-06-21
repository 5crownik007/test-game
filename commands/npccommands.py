from commands.command import Command
from evennia import CmdSet, utils
from django.conf import settings
_SEARCH_AT_RESULT = utils.object_from_module(settings.SEARCH_AT_RESULT)

class CmdConverse(Command):
    key = "converse"
    aliases = ["converse with", "speak with", "talk to"]
    def func(self):
        if not self.args:
            self.caller.msg("Converse with whom?")
            return
        else:
            target = self.caller.search(self.args,candidates=self.caller.location.contents+self.caller.contents,use_nicks=True,quiet=True)
            if len(target) != 1:
                _SEARCH_AT_RESULT(target,self.caller,self.args)
                return
            else:
                target = target[0]
        
        if not hasattr(target, "receive_converse"):
            self.caller.msg("You can't speak with %s" %target.key)
            return
        else:
            target.receive_converse(self.caller)

class PC2NPCCmdSet(CmdSet):
    key = "pc2npc_cmdset"
    priority = 1
    def at_cmdset_creation(self):
        self.add(CmdConverse())