from typeclasses.characters import Character
from typeclasses.objects import Object
from evennia.utils import search, evmenu
from commands.npccommands import *
import random

class NonPlayerCharacter(Character):
    def at_object_creation(self):
        super().at_object_creation()

    def receive_converse(self, caller):
        convo_tree = {
            "start":self.startconvo,
            "end":self.endconvo
            }
        evmenu.EvMenu(caller, convo_tree,startnode_input=('',{"greeted":False}))

    def startconvo(self, caller, raw_string, **kwargs):
        if not kwargs["greeted"]:
            if self.db.greeting:
                text = self.db.greeting %{"callername":caller.key,"ourname":self.key}                
            else:
                text = '%(ourname)s says "Hello there %(callername)s."' %{"callername":caller.key,"ourname":self.key}
        else:
            if self.db.greetreply:
                text = self.db.greetreply
            else:
                text = '%s says "And hello to you too."' %self.key
        options = (
            {"key":"Greeting",
            "desc":"Say hello to %s."% self.key,
            "goto":self.replygreeting},
            {"key":"Farewell",
            "desc":"End the conversation.",
            "goto":"end"}
            )        
        return text, options

    def replygreeting(self, caller, raw_string, **kwargs):
        return None, {"greeted":True}

    def endconvo(self, caller, raw_string, **kwargs):
        if self.db.farewell:
            text = self.db.farewell %self.key
        else:
            text = '%s says "See you around."' %self.key
        return text