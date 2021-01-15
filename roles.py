"""
Handles player roles and factions. Hopefully more extensible than the last
system and a whole load more magical.
An instance of Player is created for each role in the game, initialised by
a subclass of Role and then updated to add passive roles (additional roles
such as with the passive cupid mode) and additional items. The RoleManager
magic class is used to identify players by their role.
"""

class Faction:

    @classmethod
    def groups( cls ):
        return [x.group for x in cls.__dict__.values() if type(x) == type(cls)]

    @classmethod
    def factions( cls ):
        return [x.__name__ for x in cls.__dict__.values() if type(x) == type(cls)]

    @classmethod
    def add( cls, faction ):
        setattr( cls, faction.__name__, faction )
        return faction

@Faction.add
class Innocent:
    "The innocent villagers must try and not to be killed or being mistaken for a wolf and lynched. They do not know anybody else's role."
    group= "villagers"
@Faction.add
class Werewolf:
    "Wolves hunt in packs at night, killing only one person. The wolves know who the other wolves are."
    group = "wolves"
@Faction.add
class Vampire:
    "Vampires attack at night independantly. Each vampire may attack a different target, but does not know anything about the other vampires."
    group = "vampires"
@Faction.add
class Zombie:
    "Brains..."
    group = "zombies"
@Faction.add
class Hamster:
    "Sooo cute!!"
    group = "hamsters"

class Roles:
    "Roles should be defined in here to create a tree structure"

    @classmethod
    def roles( cls ):
        return [x.__name__ for x in cls.__dict__.values() if type(x) == type(cls) and x.__name__!="Role" ]

    @classmethod
    def add( cls, role ):
        setattr( cls, role.__name__, role )
        return role

class Role:
    "The base role. All faction roles should be a subclass of this. This role is not playable."
    inventory = []

@Roles.add
class Villager(Role):
    #"The base villager role. All villagers should be a subclass of this."
    "This role is the simplest: there is nothing to do at night but hope to survive."
    faction = Faction.Innocent

@Roles.add
class Witch(Villager):
    "This role gives the player an advantage in knowing who will die each night, as well as two potions, each can only be used once. One potion saves the life of a player due to die, the other allows them to kill somebody of their choice."
    inventory = ["beer","cider"]

@Roles.add
class Inspector(Villager):
    "This role allows the player to inspect a character every night and discover their role."

@Roles.add
class Hunter(Villager):
    "This role gives the player a bargaining chip as, when they are due to die, they will kill somebody else as well."

@Roles.add
class Cupid(Villager):
    "This role causes the player to know who the lovers are. At the start of the game they may also choose the lovers."

@Roles.add
class Wolf(Role):
    "This role gives the player the oppurtinity to make kills each night, as part of a pack."
    faction = Faction.Werewolf

@Roles.add
class Vampire(Role):
    "This role gives the player the oppurtunity to kill every night, independant of other vampires"
    faction = Faction.Vampire

class Player( object ):
    def __init__( self, role, lives=1 ):
        self.role = role
        self.faction = role.faction
        self.passive_roles = []
        self.lives = lives
        self.user = None
        self.inventory = [] + role.inventory # eg, witch has cider and beer
        self.lover = None

    def __cmp__( self, other ):
        return cmp( self.user, other )

    def __str__( self ):
        return str( self.user )

    def give_item( self, item ):
        self.inventory.append( item )

    def has_item( self, item ):
        return item in self.inventory

    def take_item( self, item ):
        if self.has_item( item ):
            self.inventory.remove( item )

    def set_user( self, user ):
        self.user = user

    def change_role( self, role ):
        self.role = role.name
        self.faction = role.faction
        self.inventory.extend( role.inventory )

    def add_passive_role( self, role ):
        self.passive_roles.append( role )
        self.inventory.extend( role.inventory )


class RoleManager(object):
    """
    Magic class to select certain roles and factions from the alive list
    If self.roles in an instance of this class:
     roles.factionname will obtain a list of that faction
     roles.rolename will return the player with that role
     roles.not_roleorfaction will give a list of everyone not selected
    """
    def __init__(self, narrator ):
        self.narrator = narrator
    def __getattribute__( self, role ):
        if role == "narrator":
            return object.__getattribute__( self, "narrator" )
        role = role.lower()
        if role.startswith("not_"):
            role = role[4:]
            invert = True
        else:
            invert = False
        if role == "lovers": # done a little differently, filter out to save time
            result = [ p for p in self.narrator.characters if p.lover ]
        elif role in Faction.groups():
            result = [ p for p in self.narrator.characters if p.faction.group.lower() == role ]
        elif role.capitalize() in Roles.roles():
            result = (
                  [ p for p in self.narrator.characters if p.role.__name__.lower() == role ]
                + [ p for p in self.narrator.characters if role in [r.__name__.lower() for r in p.passive_roles ] ]
                 )
            result = result and result[0] or None # roles and passive roles are assumed to be unique here
        else:
            raise AttributeError
        if invert:
            result = list( set( self.narrator.characters ) - set( result ) )
        return result
