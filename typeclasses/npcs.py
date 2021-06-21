from typeclasses.characters import Character
from typeclasses.objects import Object
from evennia.utils import search, evmenu
from commands.npccommands import *
import random

class NonPlayerCharacter(Character):
    def at_object_creation(self):
        super().at_object_creation()
        #keywords for a convo_topics dictionary
        #  key(str): evmenu key for the option in the startconvo node
        #  desc(str): evmenu description shown with the option in startconvo node
        #  goto(str or callable or tuple(callable, kwargs)): node or goto-callable for the option in the startconvo node
        #  topic_text(str): text shown in the topicconvo node. irrelevant if not going to that node
        #  locktag(str or None): key of the tag required for this topic to be displayed. If set to None, no tag is required.
        self.db.convo_topics = [
            {"key":"Example","desc":"This is an example topic.","goto":"topic","topic_text":"This is the text of the topic.","locktag":None}
        ]

    def add_convo_topic(self,new_topic):
        #adds a conversation topic to the list
        self.db.convo_topics.append(new_topic)

    def receive_converse(self, caller):
        #Called when someone converses with us, initiates the conversation menu.
        convo_tree = {
            "start":self.startconvo,
            "topic":self.topicconvo,
            "end":self.endconvo
            }
        evmenu.EvMenu(caller, convo_tree,startnode_input=('',{"greeted":False}))

    def generate_options(self, caller):
        #needs to return a list of dictionaries like so:
        # convo_options = [
        #     {"key":"Greeting","desc":"Say hello to %s."% self.key,"goto":self.replygreeting},
        #     {"key":"Topic1","desc":"Topic1desc","goto":"topic1goto"},
        #     {"key":"Topic2","desc":"Topic2desc","goto":"Topic2goto"},
        #     {"key":"Topic3",...
        #     {"key":"Farewell","desc":"End the conversation.","goto":"end"}
        #     ]
        convo_options = []
        convo_options.append({"key":"Greeting","desc":"Say hello to %s."% self.key,"goto":self.replygreeting})
        if len(self.db.convo_topics) > 0:
            for topic in self.db.convo_topics:
                if not topic["locktag"] or caller.tags.get(topic["locktag"]):
                    convo_options.append({"key":topic["key"],"desc":topic["desc"],"goto":topic["goto"]})
        convo_options.append({"key":"Farewell","desc":"End the conversation.","goto":"end"})
        return convo_options

    def startconvo(self, caller, raw_string, **kwargs):
        #This node is the "core" node for the whole conversation.
        if not kwargs["greeted"]:
            if self.db.greeting:
                text = self.db.greeting %{"callername":caller.key,"ourname":self.key}                
            else:
                text = '%(ourname)s says "Hello there %(callername)s."' %{"callername":caller.key,"ourname":self.key}
        else:
            if self.db.greetreply:
                text = self.db.greetreply
            else:
                text = '%s asks "How can I help you?"' %self.key
        options = self.generate_options(caller)
        return text, options

    def replygreeting(self, caller, raw_string, **kwargs):
        #This callable will return us to the startconvo node, but with greeted as True
        return "start", {"greeted":True}

    def topicconvo(self, caller, raw_string, **kwargs):
        our_topic = {}
        for topic in self.db.convo_topics:
            if topic["key"].lower() == raw_string.lower():
                our_topic = topic
        text = our_topic["topic_text"]
        options = [
            {"key":"Back","desc":"Select another conversation topic.","goto":self.replygreeting}
        ]
        return text, options
        
    def endconvo(self, caller, raw_string, **kwargs):
        if self.db.farewell:
            text = self.db.farewell %self.key
        else:
            text = '%s says "See you around."' %self.key
        return text