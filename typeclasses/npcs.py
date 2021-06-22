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
            {"key":"Example","desc":"This is an example topic.","goto":"topic","topic_text":"This is the text of the topic.","locktag":None,"topictag":None}
        ]

    def add_convo_topic(self,caller,new_topic):
        #Adds a conversation topic to the database.
        for topic in self.db.convo_topics:
            if topic["key"].lower() == new_topic["key"].lower():
                #Trying to avoid duplicates if possible
                caller.msg("Topic with key %s already exists."%new_topic["key"])
                return
        self.db.convo_topics.append(new_topic)
        caller.msg("Topic with key %s successfully added for %s."%(new_topic["key"],self.key))
        
    def list_convo_topic(self,caller):
        #Messages a list of all topics to the caller.
        topic_list = []
        for topic in self.db.convo_topics:
            topic_list.append(str(topic))
        return_str = "\n".join(topic_list)
        return_str = ''.join(["List of topics for %s.\n"%self.key,return_str,"\n%s topics found."%len(topic_list)])
        caller.msg(return_str)

    def view_convo_topic(self,caller,topic_key):
        #Messages a specified topic to the caller.
        view_topic = {}
        view_topic_list = []
        for topic in self.db.convo_topics:
            if topic["key"].lower() == topic_key.lower():
                view_topic = topic
        if view_topic:
            for keyword in view_topic:
                    line = "|w%s|n: %s"%(keyword,view_topic[keyword])
                    view_topic_list.append(line)
            return_str = "\n".join(view_topic_list)
            return_str = ''.join(["Found topic with key |w%s|n for %s.\n"%(topic_key,self.key),return_str])
            caller.msg(return_str)
        else:
            caller.msg("Topic with key %s not found for %s"%(topic_key,self.key))

    def remove_convo_topic(self,caller,topic_key):
        #Removes a specified topic.
        topic_found = False
        for topic in self.db.convo_topics:
            if topic["key"].lower() == topic_key.lower():
                topic_found = True
                self.db.convo_topics.remove(topic)
                caller.msg("Topic %s successfully removed from %s."%(topic_key,self.key))
        if not topic_found:
            caller.msg("Topic with key %s not found for %s"%(topic_key,self.key))

    def edit_convo_topic(self,caller,topic_key,received):
        #Finds a specified topic and then replaces it with a new one OR finds a specified keyword on a
        # topic and replaces it with a new one.
        topic_list = self.db.convo_topics
        old_topic_index = False
        new_topic_key = False
        new_topic_indices = []
        if isinstance(received, dict):
            new_topic_key = received["key"].lower()
        elif received[0] == 'key':
            new_topic_key == received[1].lower()
        if new_topic_key:
            for topic_index in range(len(topic_list)):
                #Get indices which match our old topic key and our new topic key
                if topic_list[topic_index]["key"].lower() == topic_key.lower():
                    old_topic_index = topic_index
                elif topic_list[topic_index]["key"].lower() == new_topic_key:
                    new_topic_indices.append(topic_index)
            if not old_topic_index:
                caller.msg("Topic with key %s not found for %s"%(topic_key,self.key))
                return
            elif len(new_topic_indices) != 0:
                if old_topic_index == new_topic_indices[0]:
                    if isinstance(received, dict):
                        topic_list[old_topic_index] = received
                    else:
                        topic_list[old_topic_index]["key"] = received[1]
                else:
                    caller.msg("Topic with key %s is already assigned for %s."%(new_topic_key,self.key))
                    return            
            else:
                if isinstance(received, dict):
                    topic_list[old_topic_index] = received
                else:
                    topic_list[old_topic_index]["key"] = received[1]
        else:
            topic_found = False
            for topic in topic_list:
                if topic["key"].lower() == topic_key.lower():
                    topic[received[0]] = received[1]
                    topic_found = True
            if not topic_found:
                caller.msg("Topic with key %s not found for %s"%(topic_key,self.key))
        self.db.convo_topics = topic_list
        if isinstance(received,dict):
            caller.msg("Topic with key %s successfully edited for %s."%(topic_key,self.key))
        else:
            caller.msg("Topic with key %s successfully had keyword %s edited for %s."%(topic_key,received[0],self.key))

    def receive_converse(self, caller):
        #Called when someone converses with us, initiates the conversation menu.
        convo_tree = {
            "start":self.startconvo,
            "topic":self.topicconvo,
            "end":self.endconvo
            }
        evmenu.EvMenu(caller, convo_tree,startnode_input=('',{"greeted":False}))

    def generate_options(self, caller, mode=0):
        #when mode = 0
        #needs to return a list of dictionaries like so:
        # convo_options = [
        #     {"key":"Greeting","desc":"Say hello to %s."% self.key,"goto":self.replychoice},
        #     {"key":"Topic1","desc":"Topic1desc","goto":"Topic1goto"},
        #     {"key":"Topic2","desc":"Topic2desc","goto":"Topic2goto"},
        #     {"key":"Topic3",...
        #     {"key":"Farewell","desc":"End the conversation.","goto":"end"}
        #     ]
        #when mode = 1
        #needs to return a list of dictionaries like so:
        # convo_options = [
        #     {"key":"Back","desc":"Select another conversation topic.","goto":self.replychoice},
        #     {"key":"Topic1Sub1","Desc":"Subtopic 1 of Topic 1 ","goto":"Topic1Sub1goto",
        #     {"key":"Topic1Sub2","Desc":"Subtopic 2 of Topic 1 ","goto":"Topic1Sub2goto",
        #     {"key":"Topic1Sub3",...
        convo_options = []
        if mode == 0:
            convo_options.append({"key":"Greeting","desc":"Say hello to %s."% self.key,"goto":self.replychoice})
            if len(self.db.convo_topics) > 0:
                for topic in self.db.convo_topics:
                    if not topic["locktag"]:
                        convo_options.append({"key":topic["key"],"desc":topic["desc"],"goto":topic["goto"]})
                    else:
                        has_locktags = True
                        locktags = topic["locktag"]
                        if not isinstance(locktags, list):
                            locktags = [locktags]
                        for locktag in locktags:
                            if locktag not in caller.tags.all():
                                has_locktags = False
                        if has_locktags:
                            convo_options.append({"key":topic["key"],"desc":topic["desc"],"goto":topic["goto"]})
            convo_options.append({"key":"Farewell","desc":"End the conversation.","goto":"end"})
        else: 
            convo_options.append({"key":"Back","desc":"Select another conversation topic.","goto":self.replychoice})
            if len(self.db.convo_topics) > 0:
                for topic in self.db.convo_topics:
                    if topic["locktag"]:
                        has_locktags = True
                        locktags = topic["locktag"]
                        if not isinstance(locktags, list):
                            locktags = [locktags]
                        for locktag in locktags:
                            if locktag not in caller.tags.all():
                                has_locktags = False
                        if has_locktags:
                            try:
                                topic_goto = eval(topic["goto"])
                            except:
                                topic_goto = topic["goto"]
                            convo_options.append({"key":topic["key"],"desc":topic["desc"],"goto":topic_goto})
        return convo_options

    def startconvo(self, caller, raw_string, **kwargs):
        #This node is the "start" node for the whole conversation.
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

    def replychoice(self, caller, raw_string, **kwargs):
        #This function very simply facilitates branching conversation construction by either sending the
        # menu back to the "start" node, or re-running the "topic" node with new kwargs
        #
        if raw_string.lower() == 'back' or raw_string.lower() == 'greeting':
            return "start", {"greeted":True}
        else:
            caller.tags.clear(category="%s_convo"%self.key)
            return None, kwargs

    def topicconvo(self, caller, raw_string, **kwargs):
        current_topic = {}
        for topic in self.db.convo_topics:
            if topic["key"].lower() == raw_string.lower():
                current_topic = topic
        if current_topic["topictag"]:
            caller.tags.add(current_topic["topictag"],category="%s_convo"%self.key)
        text = current_topic["topic_text"]
        options = self.generate_options(caller,mode=1)
        return text, options
        
    def endconvo(self, caller, raw_string, **kwargs):
        if self.db.farewell:
            text = self.db.farewell %self.key
        else:
            text = '%s says "See you around."' %self.key
        return text