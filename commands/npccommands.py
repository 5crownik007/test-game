from commands.command import Command
from evennia import CmdSet, utils
from evennia import syscmdkeys, default_cmds
from evennia.commands.default.building import ObjManipCommand
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

# class CmdConvoTopic(ObjManipCommand):
#     """
#     View, add, remove and edit conversation topics on an NPC.
#     Usage:
#       convotopic <obj>
#       convotopic <obj>/<key>
#       convotopic <obj> = <dict> 
#       convotopic/remove <obj>/<key>
#       convotopic/edit <obj>/<key> = <dict>
#     First form lists all topics on an object
#     Second form views a specific topic on an object
#     Third form adds a topic to an object
#     Fourth form removes a topic from an object
#     Fifth edits a topic on an object

#     Remember, a conversation topic is always a dictionary with the following keywords:
#         key(str): evmenu key for the option in the startconvo node
#         desc(str): evmenu description shown with the option in startconvo node
#         goto(str or callable or tuple(callable, kwargs)): node or goto-callable for the option in the startconvo node
#         topic_text(str): text shown in the topicconvo node. irrelevant if not going to that node
#         locktag(str or None): key of the tag required for this topic to be displayed. If set to None, no tag is required.
#     """
#     key = "convotopic"
#     locks = "cmd:perm(builder)"
#     help_category = "Building"

#     def 

class CmdConvoTopic(default_cmds.MuxCommand):
    """
    Placeholder command to ADD conversation topics only
    Usage:
       convotopic <obj> = <dict>
    """
    key = "convotopic"
    locks = "cmd:perm(builder)"
    help_category = "Building"
    def func(self):
        if not self.args or not self.rhs:
            self.caller.msg("|rUsage: convotopic <obj> = <dict>|n")
            return
        else:
            target = self.caller.search(self.lhs,candidates=self.caller.location.contents,use_nicks=True,quiet=True)
            if len(target) != 1:
                _SEARCH_AT_RESULT(target,self.caller,self.args)
                return
            else:
                target = target[0]
        
        if not hasattr(target, "add_convo_topic"):
            self.caller.msg("You cannot set conversation topics on %s." %target.key)
            return
        elif not self.rhs["key"]:
            self.caller.msg("Missing key from dictionary")
            return
        else:
            target.add_convo_topic(eval(self.rhs))
            self.caller.msg("Topic added to %s: %s" %(self.lhs, self.rhs["key"]))
        
class PC2NPCCmdSet(CmdSet):
    key = "pc2npc_cmdset"
    priority = 1
    def at_cmdset_creation(self):
        self.add(CmdConverse())
        self.add(CmdConvoTopic())