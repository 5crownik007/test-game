from typeclasses.objects import Object
from typeclasses.exits import Exit
from evennia.prototypes.spawner import spawn
from evennia.utils import search
from commands.itemcommands import *
from evennia.utils.evmenu import get_input
import random

class Edible(Object):
    def at_object_creation(self):
        self.cmdset.add_default(CmdSetEdible, permanent=True)
        self.tags.add("edible")
        self.locks.add("call:holds(%s)" %self.id)

EDIBLE_PROTOTYPES = {
    "cheese" :{
        "typeclass":"typeclasses.items.Edible",
        "key":"cheese",
        "desc":"A chunk of cheese. It smells delicious."
    }
}

TEST_PROTOTYPES = {
    "testitem":{
        "typeclass":"typeclasses.objects.Object",
        "key":"Test Item",
        "aliases":["testitem","test",],
        "desc":"This is a test item. Its shapeless form bends the mind of any mere mortal |/who gazes upon it. It has no mass, no volume, no surface, yet you can |/observe it. In other words, it hurts your head just to look at this thing."
    }
}

class dispenser(Object):
    def at_object_creation(self):
        self.cmdset.add_default(CmdSetDispenser, permanent=True)
        self.locks.add("get:false()")
        self.db.get_err_msg = "This dispenser cannot be picked up."
        self.db.get_itm_msg = "You get the %s from the dispenser."
        self.db.get_itm_err_msg = "You cannot get anything from the dispenser."
        self.db.available_itm = ["testitem"]
        self.db.prototypes = "TEST_PROTOTYPES"

    def items_unavailable(self):
        if len(self.db.available_itm) > 0:
            return False
        else:
            return True

    def get_item(self, caller):
        if self.items_unavailable():
            caller.msg(self.db.get_itm_err_msg)
        else:
            prototype = random.choice(self.db.available_itm)
            prototypes = eval(self.attributes.get("prototypes"))
            if prototype in prototypes:
                itm = spawn(prototypes[prototype],prototype_parents=prototypes)[0]
                itm.location = caller
                caller.msg(self.db.get_itm_msg % itm.key)
            else:
                caller.msg(self.db.get_itm_err_msg)

class ComplexDoor(Exit):
    def at_object_creation(self):
        #The door must start locked because we assign the actual destination when it's unlocked.
        # While locked it actually has no destination to send anyone to, only a database entry with the
        # name of a search term for an object.
        self.db.locked = True
        self.cmdset.add(CmdSetComDoor, permanent=True)
        self.locks.add("traverse:not objattr(locked)")
        self.db.lock_msg = "You |rlock|n the door."
        self.db.unlock_msg = "You |gunlock|n the door."
        self.db.destination = "#2"
        self.db.desc_locked = "The door is |rlocked|n."
        self.db.desc_unlocked = "The door is |gunlocked|n."
        self.db.traverse_locked = "You try to open the door, but find that it's |rlocked|n."
        self.db.linked_exit = None

    def lockingmethod(self, caller):
        #This function is where the player can lock or unlock the door. It also assigns the destination
        # to the door. You could do some funny magic things here where if the player waves a wand, the
        # door's destination will be someplace else, then when the door closes behind them, the next
        # person to open it will find that it leads to its original, mundane location.
        if not self.db.locked:
            caller.msg(self.db.lock_msg)
            self.db.locked = True
            self.destination = None
        else:
            caller.msg(self.db.unlock_msg)
            self.db.locked = False
            self.destination = search.search_object(self.db.destination)[0]
        self.handle_linked(self.db.linked_exit)

    def handle_linked(self, linked_exit_name):
        if not linked_exit_name:
            return
        else:
            linked_exit = search.search_object(linked_exit_name)[0]
            linked_exit.db.locked = self.db.locked
            if self.destination:
                linked_exit.destination = search.search_object(linked_exit.db.destination)[0]
            else:
                linked_exit.destination = None

    def return_appearance(self, caller):
        #Allows the appearance to change based on whether or not the door is locked.
        if not self.db.locked:
            self.db.desc = self.db.desc_unlocked
        else:
            self.db.desc = self.db.desc_locked
        return super().return_appearance(caller)

    def at_failed_traverse(self, traveller):
        if self.db.locked:
            traveller.msg(self.db.traverse_locked)
        else:
            return super().at_failed_traverse(traveller)

class KeycardDoor(ComplexDoor):
    #Door can be locked/unlocked if the user has a keycard, locks again when traversed.
    def at_object_creation(self):
        super().at_object_creation()
        self.db.cardnumber = random.randint(0,999)
        self.locks.add("door lock:holds(keycard %s)"% self.db.cardnumber)
        self.db.desc_locked = (self.db.desc_locked + " It has %s stencilled on it." %self.db.cardnumber)
        self.db.desc_unlocked = (self.db.desc_unlocked + " It has %s stencilled on it." %self.db.cardnumber)
        self.db.no_card_err_msg = "You don't have any means to lock or unlock this door."

    def lockingmethod(self, caller):
        if not self.access(caller, "door lock"):
            caller.msg(self.db.no_card_err_msg)
        else:
            return super().lockingmethod(caller)
    
    def at_after_traverse(self, traveller, source):
        self.db.locked = True
        self.destination = None
        self.handle_linked(self.db.linked_exit)

class KeypadDoor(ComplexDoor):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.locknumber = random.randint(0,9999)
        self.db.desc_locked = (self.db.desc_locked + " It has a small keypad affixed to it.")
        self.db.desc_unlocked = (self.db.desc_unlocked + " It has a small keypad affixed to it.")
        self.db.lastinput = None
        self.db.bad_input_msg = "You input the code, but the door remains |rlocked|n."

    def lockingmethod(self, caller):
        if self.db.locked:
            get_input(caller, "Please input a 4 digit code.", self.receiveinput)
        else:
            caller.msg(self.db.lock_msg)
            self.db.locked = True
            self.destination = None
            self.handle_linked(self.db.linked_exit)

    def receiveinput(self, caller, prompt, received):
        if not received:
            caller.msg("You enter nothing.")
            self.db.lastinput = None
        elif len(received) < 4:
            caller.msg("That is too short.")
            self.db.lastinput = None
        elif len(received) > 4:
            caller.msg("That is too long.")
            self.db.lastinput = None
        elif not str(received).isdecimal():
            caller.msg("There are only digits 0-9 on the keypad.")
            self.db.lastinput = None
        else:
            caller.msg(f"You input |w{received}|n into the keypad.")
            self.db.lastinput = int(received)
        if not self.db.lastinput:
            return
        elif self.db.lastinput != self.db.locknumber:
            caller.msg(self.db.bad_input_msg)
            self.db.lastinput = None
        else:
            caller.msg(self.db.unlock_msg)
            self.db.locked = False
            self.destination = search.search_object(self.db.destination)[0]
            self.db.lastinput = None
        self.handle_linked(self.db.linked_exit)

class RemoteDoor(ComplexDoor):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.frequency = random.randint(0,999)
        self.locks.add("door lock:attr(frequency, %s)" % self.db.frequency)
        self.db.no_freq_err_msg = "You don't have any means to lock or unlock this door."

    def lockingmethod(self,caller):
        if not self.access(caller, "door lock"):
            caller.msg(self.db.no_freq_err_msg)
        else:
            return super().lockingmethod(caller)

class DoorButton(Object):
    def at_object_creation(self):
        self.cmdset.add(CmdSetButton, permanent=True)
        self.locks.add("get:false()")
        self.db.frequency = None
        self.desc = "There is a small podium sticking out from the ground with a button affixed to the top."