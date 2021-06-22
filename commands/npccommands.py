from commands.command import Command
from evennia import CmdSet, utils
from evennia import syscmdkeys, default_cmds
from evennia.utils import dedent
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
            target = self.caller.search(self.args.strip(),candidates=self.caller.location.contents+self.caller.contents,use_nicks=True,quiet=True)
            if len(target) != 1:
                _SEARCH_AT_RESULT(target,self.caller,self.args.strip())
                return
            else:
                target = target[0]
        
        if not hasattr(target, "receive_converse"):
            self.caller.msg("You can't speak with %s" %target.key)
            return
        else:
            target.receive_converse(self.caller)

class CmdConvoTopic(default_cmds.MuxCommand):
    """
    List, view, remove, add and edit conversation topics on an NPC.
    Usage:
      convotopic <obj>
      convotopic <obj>/<key>
      convotopic/remove <obj>/<key>
      convotopic <obj> = <dict> 
      convotopic/edit <obj>/<key> = <dict>
      convotopic/edit <obj>/<key>/<keyword> = <arg>
    First form lists all topics on <obj>,
    Second form views <key> on <obj>,
    Third form removes <key> from <obj>,
    Fourth form adds <dict> to <obj>,
    Fifth form replaces <key> on <obj> with <dict>,
    Sixth form replaces <keyword> on <key> on <obj> with <arg>

    Remember, a conversation topic is always a dictionary with the following keywords:
        key(str): evmenu key for the option in the startconvo node
        desc(str): evmenu description shown with the option in startconvo node
        goto(str or callable or tuple(callable, **kwargs)): node or goto-callable for the option in the startconvo node
        topic_text(str): text shown in the topicconvo node. irrelevant if not going to that node
        locktag(str or list[**str] None): key or keys of the tag required for this topic to be displayed. If set to None, no tag is required.
        topictag(str or None): key of the tag given when on this this topic node. If set to None, no tag is given.
    Here's an easy template you can paste into your input line:
    {'key': ,'desc': ,'goto':,'topic_text': ,'locktag': ,'topictag': }

    You can also add additional keywords beyond those above, and they will be passed in properly.
    """
    key = "convotopic"
    locks = "cmd:perm(builder)"
    help_category = "Building"
    switch_options = ('remove','edit')

    def checkusage(self):
        #Checks which usage of the command is being sent to us and sets our self.usage variable
        # accordingly.
        if self.args:
            if self.switches:
                self.usage = self.switches[0]
            elif self.rhs:
                self.usage = 'add'
            elif len(self.lhs.split('/')) > 1:
                self.usage = 'view'
            else:
                self.usage = 'list'

    def parse(self):
        super().parse()
        self.checkusage()          

    def func(self):
        if not self.args:
            #If we don't have args, go back to the user and ask for some.
            self.caller.msg(dedent(
                """
                |wUsage:|n
                convotopic <obj>
                convotopic <obj>/<key>
                convotopic/remove <obj>/<key>
                convotopic <obj> = <dict> 
                convotopic/edit <obj>/<key> = <dict>
                convotopic/edit <obj>/<key>/<keyword> = <arg>
                """
            ))
            return
        target = self.caller.search(self.lhs.split('/')[0],candidates=self.caller.location.contents,use_nicks=True,quiet=True)
        if len(target) != 1:
            #Can't find the target, this is invalid. Search error handling will take it from here.
            _SEARCH_AT_RESULT(target,self.caller,self.args)
            return
        #Found a target. Does this thing even have the ability to handle conversation topics? Let's check.
        target = target[0]
        if not hasattr(target, "add_convo_topic"):
            #Technically, add_convo_topic is only one of the functions we use to interact with the
            # conversations on NPCs, but if it's absent, then the other ones are likely absent as well.
            self.caller.msg("%s has no handler for conversations." %target.key)
            return
        if self.usage == 'list':
            #For list, all that is needed is a valid target, which we've just confirmed. We can call the
            # relevant function now.
            target.list_convo_topic(self.caller)
            return
        if self.usage == 'add' or self.usage == 'edit':
            #For add and edit, we'll need a valid dictionary or keyword as one of the arguments. Let's
            # test to see if we received either.
            if not self.rhs:
                self.caller.msg(dedent(
                    """
                    |wUsage:|n
                    convotopic <obj>
                    convotopic <obj>/<key>
                    convotopic/remove <obj>/<key>
                    convotopic <obj> = <dict> 
                    convotopic/edit <obj>/<key> = <dict>
                    convotopic/edit <obj>/<key>/<keyword> = <arg>
                    """
                ))
                return
            if len(self.lhs.split('/')) < 3:
                try:
                    received = eval(self.rhs)
                except:
                    received = self.rhs
                if not isinstance(received, dict):
                    self.caller.msg("Received input was not a dictionary.")
                    return
                else:
                    keywords = ["key","desc","goto","topic_text","locktag","topictag"]
                    for keyword in keywords:
                        if keyword not in received:
                            self.caller.msg(dedent(
                                """
                                |rInput topic dictionary was missing one or more keywords.|n
                                |wRequired Keywords:|n
                                |wkey(str):|n evmenu key for the option in the startconvo node
                                |wdesc(str):|n evmenu description shown with the option in startconvo node
                                |wgoto(str or str(callable) or tuple(str(callable), **kwargs)):|n node or goto-callable for the option. Callables must he put into strings for proper function.
                                |wtopic_text(str):|n text shown in the topicconvo node. irrelevant if not going to that node
                                |wlocktag(str or list[**str] None):|n key or keys of the tag required for this topic to be displayed. If set to None, no tag is required.
                                |wtopictag(str or None):|n key of the tag given when on this this topic node. If set to None, no tag is given.
                                """
                            ))
                            return
                if self.usage == 'add':
                    #Since we have a valid target and valid dictionary, we can add.
                    target.add_convo_topic(self.caller,received)
                    return
            else:
                received = [self.lhs.split('/')[2],self.rhs]

        if self.usage == 'view' or self.usage == 'remove' or self.usage == 'edit':
            #For cases where a valid key is necessary, let's see if it's there.
            if not len(self.lhs.split('/')) > 1:
                self.caller.msg("Key needed for %s."%self.usage)
            else:
                topic_key = self.lhs.split('/')[1]
                if self.usage == 'view':
                    #With a valid target and key, we can view and remove.
                    target.view_convo_topic(self.caller,topic_key)
                elif self.usage == 'remove':
                    target.remove_convo_topic(self.caller,topic_key)
                else:
                    #With a valid target, key and dictionary/keyword+arg, we can edit.
                    target.edit_convo_topic(self.caller,topic_key,received)

class PC2NPCCmdSet(CmdSet):
    key = "pc2npc_cmdset"
    priority = 1
    def at_cmdset_creation(self):
        self.add(CmdConverse())
        self.add(CmdConvoTopic())