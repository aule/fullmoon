"""
Create help messages for commands, roles and factions using docstrings

Author: Joe Taylor
Date: 2nd June 2010
"""

from roles import Roles, Faction
from fullmoon import Narrator

help_topics = {}


def help_topic(topic):  # wrapper function to quickly add help topics
    help_topics[topic.__name__.replace("_", " ").lower()] = topic.__doc__
    return topic


def help(topic):
    if not topic:
        topic = "help"  # default topic

    topic_c = topic.capitalize()
    topic_l = topic.lower()
    if topic_l.startswith("!"):
        topic_l = topic_l[1:]  # remove the '!' from commands

    if topic_l in help_topics:
        return help_topics[topic_l]

    if topic_c in Roles.roles():
        role = getattr(Roles, topic_c)
        return "Role: %s. Faction: %s. Commands: %s. %s" % (
            role.__name__,
            role.faction.__name__,
            ", ".join(commands(role)) or "none",
            role.__doc__,
        )

    if topic_l in Faction.groups():
        return help(
            [f for f in Faction.factions() if getattr(Faction, f).group == topic_l][0]
        )

    if topic_c in Faction.factions():
        faction = getattr(Faction, topic_c)
        return "Faction: %s (the %s). %s" % (
            faction.__name__,
            faction.group,
            faction.__doc__,
        )

    cmds_global = dict(
        [
            (c.name.lower(), c.cmd.__doc__ or "Command lacks help.")
            for c in Narrator.cmds_global
        ]
    )
    if topic_l in cmds_global:
        return "Global command: %s. %s" % (topic_l, cmds_global[topic_l])

    cmds_private = dict(
        [
            (c.name.lower(), c.cmd.__doc__ or "Command lacks help.")
            for c in Narrator.cmds_private
        ]
    )
    if topic_l in cmds_private:
        return "Private command: %s. %s" % (topic_l, cmds_private[topic_l])

    cmds_public = dict(
        [
            (c.name.lower(), c.cmd.__doc__ or "Command lacks help.")
            for c in Narrator.cmds_public
        ]
    )
    if topic_l in cmds_public:
        return "Public command: %s. %s" % (topic_l, cmds_public[topic_l])

    return "There is no help on that topic"


def commands(role):
    cmds = []
    for cmd in Narrator.cmds_private:
        if hasattr(cmd.cmd, "role") and cmd.cmd.role == role:
            cmds.append(cmd.name)
    return cmds


@help_topic
def global_command():
    "A command that can be used publicly or privately"


@help_topic
def public_command():
    "A command which must be used publicly (in the channel)"


@help_topic
def private_command():
    "A command which must be made privately (in a private message to the narrator)"


@help_topic
def narrator():
    "The bot running the game, usually called Mayor"


@help_topic
def Mayor():
    "The usual nick of the narrator"


@help_topic
def lovers():
    "The lovers are bound together throughout the game, and if one of them is killed, the other will surely die too. The cupid rule affects whether or not lovers are present in a particular game. When lovers are present, a new win condition is created for if only the lovers remain: lovers' victory."


@help_topic
def squirrel():
    "You don't want to know..."


@help_topic
def bacon():
    "This can be used once and will protect from a wolf attack."


@help_topic
def garlic():
    "This will thwart any vampire attacks made against its owner."


@help_topic
def cheese():
    "I like cheese. I wish I had some right now..."


@help_topic
def Andrew():
    "He is the wolf. He is *always* the wolf"


@help_topic
def Aule():
    "He probably isn't the wolf, but kill him anyway. He also made this thing."


@help_topic
def About():
    "Fullmoon is an online game based on Tigger's version of Werewolf, a derivative of Mafia. It was coded by Aule some time around 2009."
