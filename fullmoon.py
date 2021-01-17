"""
#fullmoon - A game by Joe Taylor of Durham University Computing Society

See our wiki for rules - http://compsoc.dur.ac.uk/mediawiki/index.php/Fullmoon

Many thanks to various people, most notably inclement, for the narrative
"""

from time import sleep
import re
import datetime
import random
from narrative import Vote, Narrative
from winbot import Bot, Command, User
from roles import RoleManager, Faction, Roles, Player
from enumeration import Enum

Bot.MOD_PWD = "p3nis?"
Bot.SHELL = True

State = Enum(
    "State",
    "NoGame",
    "Initialising",
    "Night",
    "WitchingHour",
    "Stalking",
    "Day",
    "Discussion",
    "Voting",
    "Revenge",
)


class Config:
    wolves = 1
    witch = False
    hunter = False
    inspector = False
    cupid = 0  # 0 = none; 1 = normal; 2 = passive; 3 = auto
    bacon = False
    recruiting = False
    doublelynch = False
    survival = 0  # %


def cmd_requirement(
    state=None,
    allow_self=True,
    required_role=None,
    require_alive=True,
    require_target_alive=True,
    allow_abstain=False,
):
    "A wrapper function to quickly ensure commands can only be performed by certain players/ghosts"

    def _wrapper(f):
        def _wrapped(self, user, *args, **kwargs):
            if state:
                if state in State.__dict__.values():
                    if self.state != state:
                        self.say("It is not the time for that.", user)
                        return
                else:
                    if self.state not in state:
                        self.say("It is not the time for that.", user)
                        return
            if require_alive and user not in self.alive:
                self.say("You must be alive to do that", user)
                return
            if not allow_self and kwargs.get("target") == user:
                self.say("You cannot do that to yourself", user)
                return
            if (
                require_target_alive
                and kwargs.has_key("target")
                and kwargs.get("target") not in self.alive
            ):
                if not (
                    allow_abstain and " " in kwargs.get("target")
                ):  # abstain targets contain a space (eg. "don't care")
                    self.say("They are not alive", user)
                return
            if required_role and not (
                hasattr(user, "character")
                and issubclass(user.character.role, required_role)
            ):
                self.say(
                    "Only players with the role of %s can do that"
                    % required_role.__name__,
                    user,
                )
                return
            return f(self, user, *args, **kwargs)

        _wrapped.__name__ = f.__name__
        _wrapped.__doc__ = f.__doc__
        _wrapped.role = required_role
        return _wrapped

    return _wrapper

    def getUser(u):
        "Helper function to make sure u is a user, not character"
        if hasattr(u, 'user'):
            return u.user
        else:
            return u


class Narrator(Bot):
    class CopyOver(Exception):
        pass

    class ReBoot(Exception):
        pass

    def shell_env(self):
        return globals()

    def init(self, channel, log, botInterface):
        self.log = log
        self.channel = channel
        self.botSend = botInterface.send
        self.botRegister = botInterface.register
        self.botPath = botInterface.path
        self.waiting = []
        self.alive = []
        self.ghosts = []
        self.start_test = (
            lambda: None
        )  # this is later replaced with a fn that may start the game if enough players
        self.help = False
        self.s.send("JOIN %s\r\n" % self.channel)
        self.state = State.NoGame
        self.conf = Config()
        self.roles = RoleManager(self)

    #                                       ++++++++++ TOPIC VALUES ++++++++++

    def update_topic(self):
        self.botSend(("STATE", self.state,))
        if self.state == State.NoGame:
            self.set_topic(
                "Waiting list for next game: %s (%d)"
                % (self.format_list(self.waiting), len(self.waiting))
            )
        if self.state == State.Initialising:
            self.set_topic("New game. Villagers: %s" % self.format_list(self.alive))
            self.botSend(("PLAYERS", [str(u) for u in self.alive],))
        if self.state in [State.Night, State.WitchingHour, State.Stalking]:
            self.set_topic(
                "Night time. Wolves: %d. Villagers: %s"
                % (len(self.roles.wolves), self.format_list(self.alive))
            )
            self.botSend(("PLAYERS", [str(u) for u in self.alive],))
            self.botSend(("WOLVES", len(self.roles.wolves),))
        if self.state in [State.Day, State.Discussion]:
            self.set_topic(
                "Day time. Wolves: %d. Villagers: %s"
                % (len(self.roles.wolves), self.format_list(self.alive))
            )
            self.botSend(("PLAYERS", [str(u) for u in self.alive],))
            self.botSend(("WOLVES", len(self.roles.wolves),))
        if self.state == State.Voting:
            self.set_topic(
                "Voting to lynch %s. Wolves: %d. Villagers: %s"
                % (self.nominee, len(self.roles.wolves), self.format_list(self.alive))
            )

    def format_list(self, people, just=True):
        if len(people) == 0:
            return "nobody"
        if len(people) == 1:
            return "just " + str(people[0])
        return ", ".join([str(u) for u in people[:-1]]) + " and " + str(people[-1])

    def format_conf(self):
        yn = ["no", "yes"]
        return (
            "wolves: %d; witch: %s; inspector: %s; hunter: %s; cupid: %s; bacon: %s; wolf recruiting: %s; efficient government: %s; survival chance: %d%%"
            % (
                self.conf.wolves,
                yn[self.conf.witch],
                yn[self.conf.inspector],
                yn[self.conf.hunter],
                ["no", "yes", "passive", "auto"][self.conf.cupid],
                yn[self.conf.bacon],
                yn[self.conf.recruiting],
                yn[self.conf.doublelynch],
                self.conf.survival,
            )
        )

    #                                       ++++++++++ PLAYER DEATH ++++++++++

    def death(self, user, msg=""):
        if user not in self.alive:
            return  # killed in multiple ways at once
        # I'm not sure whether this function will be passed a role or character
        # So I shall make sure it is a user with a character
        if not hasattr(user, "character"):
            if hasattr(user, "user"):
                user = user.user  # it has a character
            else:
                return  # it was somethinillagerg else... just ignore it
        if user.character.faction == Faction.Innocent:
            self.ghosts.append(user)
        msgs = [msg]
        msgs.append(
            getattr(Narrative.DeathReveal, user.character.role.__name__.lower())
        )
        for role in user.character.passive_roles:
            msgs.append(getattr(Narrative.DeathReveal, role.__name__.lower()))
        for item in user.character.inventory:
            try:
                msgs.append(getattr(Narrative.DeathReveal.Inventory, item))
            except AttributeError:
                pass
        self.say(" ".join([str(msg).strip() for msg in msgs]))
        self.botSend(("DEATHREVEAL", user.isolate(), user.character))
        self.alive.remove(user)
        self.characters.remove(user)
        if user.character.lover:
            self.botSend(("DEATHREASON", user.character.lover.user.isolate(), "LOVER"))
            self.death(
                user.character.lover,
                str(Narrative.Death.lover)
                % {"victim": user.character.lover, "lover": user},
            )

    def hunter_death(self, callback):
        self.state = State.Revenge

        def revenge(target):
            self.botSend(("DEATHREASON", target.isolate(), "HUNTER"))
            self.death(
                target,
                str(Narrative.Death.hunterAttack)
                % {"hunter": self.roles.hunter, "victim": target},
            )
            self.set_timer(0, callback)

        self.update_topic()
        self.revenge = revenge
        self.say(
            "You have 60 seconds to take revenge and shoot someone with your big gun.",
            self.roles.hunter,
        )
        self.botSend(("HUNTERFIRE",), self.roles.hunter.user)
        self.set_timer(60, callback)

    #                                       ++++++++++ GAME STAGES ++++++++++

    def game_begin(self):
        self.state = State.Initialising
        self.update_topic()

        # check to see if there are enough players
        if len(self.alive) < 3:
            self.say(
                "Not enough players: at least three players are required to avoid instant Game Over"
            )
            self.state = State.NoGame
            return  # just give up
        needed = (
            self.conf.wolves
            + self.conf.witch
            + self.conf.hunter
            + self.conf.inspector
            + (self.conf.cupid == 1)
        )
        if needed > len(self.alive):  # we have a problem
            if self.conf.cupid == 1:
                self.conf.cupid = 2  # change to passive cupid to save on needed players
                needed -= 1
                self.say(
                    "Not enough players: changing cupid rule to Passive Cupid instead"
                )
        if needed > len(self.alive):
            n = min(self.conf.wolves - 1, needed - len(self.alive))
            self.conf.wolves -= n
            needed -= n
            self.say(
                "Not enough players: changing number of wolves to %d" % self.conf.wolves
            )
        if needed > len(self.alive):
            if self.conf.hunter:
                self.conf.hunter = False
                needed -= 1
                self.say("Not enough players: removing the Hunter character")
        if needed > len(self.alive):
            if self.conf.witch:
                self.conf.witch = False
                needed -= 1
                self.say("Not enough players: removing the Witch character")
        if needed > len(self.alive):
            if self.conf.inspector:
                self.conf.inspector = False
                needed -= 1
                self.say("Not enough players: removing the Inspector character")
        if needed > len(self.alive):
            self.say("Not enough players: giving up")
            self.state = State.NoGame
            return  # just give up
        if len(self.alive) < self.conf.wolves * 2 + 1:
            self.conf.wolves = max(1, len(self.alive) / 2 - 1)
            self.say(
                "Too many wolves: changing number of wolves to %d" % self.conf.wolves
            )

        self.characters = []  # this will be filled with all the roles to be assigned

        # +++++ wolves +++++
        for n in xrange(self.conf.wolves):
            self.characters.append(Player(Roles.Wolf))

        self.recruit = self.conf.recruiting  # wolf recruiting

        # +++++ witch +++++
        if self.conf.witch:
            self.characters.append(Player(Roles.Witch))

        # +++++ hunter +++++
        if self.conf.hunter:
            self.characters.append(Player(Roles.Hunter))

        # +++++ inspector +++++
        if self.conf.inspector:
            self.characters.append(Player(Roles.Inspector))

        # +++++ cupid +++++
        if self.conf.cupid == 1:
            self.characters.append(Player(Roles.Cupid))

        # +++++ villagers +++++
        # top up the remaining needed characters as Villager
        for n in xrange(len(self.characters), len(self.alive)):
            self.characters.append(Player(Roles.Villager))

        # All roles now defined, self.roles and self.characters will give meaningful info

        # +++++ passive cupid +++++
        if self.conf.cupid == 2:
            random.choice(self.roles.villagers).add_passive_role(Roles.Cupid)

        # +++++ cheese +++++
        if True:
            random.choice(self.characters).give_item("cheese")

        # +++++ bacon +++++
        if self.conf.bacon:
            random.choice(self.roles.not_wolves).give_item("bacon")

        # Assign the players to the roles
        random.shuffle(self.alive)
        for role, user in zip(self.characters, self.alive):
            role.set_user(user)
            user.character = role

        # Tell them who they are
        for player in self.characters:
            self.botSend(("YOURROLE", player), player.user)
            self.say(
                getattr(Narrative.RoleAssignment, player.role.__name__.lower()), player
            )
            for role in player.passive_roles:
                self.say(
                    getattr(Narrative.RoleAssignment, role.__name__.lower()), player
                )
            for item in player.inventory:
                try:
                    self.say(getattr(Narrative.RoleAssignment.Inventory, item), player)
                except AttributeError:
                    pass
            sleep(1)

        # Tell the wolves about the other wolves
        self.say_list(
            "The wolf pack contains: %s" % self.format_list(self.roles.wolves),
            self.roles.wolves,
        )
        self.botSend(
            ("YOURFACTION", [p.user.isolate() for p in self.roles.wolves]),
            [p.user for p in self.roles.wolves],
        )

        # Print the config of the game

        self.say("All roles have now been assigned. [%s]" % self.format_conf())
        self.botSend(("CONF", self.conf))
        self.botSend(("ROLESASSIGNED",))

        # if needed, give cupid a chance to choose the lovers, then inform them
        if self.conf.cupid in [1, 2]:
            self.set_timer(60, self.game_make_lover)
        else:
            self.game_make_lover()

        # make sure the order of characters doesn't give the game away
        random.shuffle(self.characters)
        random.shuffle(self.alive)

    def game_make_lover(self):
        if self.conf.cupid > 0:  # if there should be lovers
            if (
                not self.roles.lovers
            ):  # this could be auto cupid, or if cupid was too slow/lazy
                lovers = random.sample(self.characters, 2)
                lovers[0].lover = lovers[1]
                lovers[1].lover = lovers[0]
                if self.conf.cupid < 3:  # not auto cupid
                    self.say(
                        "You did not choose the lovers in time, so %s and %s have been chosen automatically"
                        % lovers,
                        self.roles.cupid,
                    )
            self.say(
                "You are one of the Lovers. You are madly in love with %s." % lovers[0],
                lovers[1],
            )
            self.say(
                "You are one of the Lovers. You are madly in love with %s." % lovers[1],
                lovers[0],
            )
            self.botSend(("YOULOVE", lovers[0].user.isolate()), lovers[1].user)
            self.botSend(("YOULOVE", lovers[1].user.isolate()), lovers[0].user)
        self.game_night()  # yeah, baby!

    def game_night(self):
        self.state = State.Night
        self.say(str(Narrative.Events.sunset))
        self.stalked = False  # has the inspector acted yet
        self.votes = {}  # votes of the wolves
        self.beer = False
        self.cider = None
        if self.recruit:
            self.say_list(
                "You have 2 mins to make your attack. You may still recruit another Wolf with '!scratch'.",
                self.roles.wolves,
            )
        else:
            self.say_list(
                "You have 2 mins to make your attack. Don't forget you must not attack different targets.",
                self.roles.wolves,
            )
        self.botSend(("WOLFCHOOSE", self.recruit,), [p.user for p in self.roles.wolves])
        self.set_timer(90, self.game_wolf_warning)
        self.update_topic()

    def game_wolf_warning(self):
        for wolf in self.roles.wolves:
            if wolf not in self.votes.keys():
                self.say("You have 30 seconds to decide on who to attack", wolf)
            self.botSend(("WOLFHURRY",), [p.user for p in self.roles.wolves])
        self.set_timer(30, self.game_wolf_attack)

    def game_wolf_attack(self):
        target = None
        recruit = False
        bite = False
        fight = False
        for vote in self.votes.values():
            if vote == "abstain":
                continue
            elif vote[0] == "bite":
                if target is None or target == vote[1]:
                    target = vote[1]
                    bite = True
                else:
                    fight = True
            elif vote[0] == "scratch":
                if target is None or target == vote[1]:
                    target = vote[1]
                    if self.recruit:
                        recruit = True
                    else:
                        fight = True
                else:
                    fight = True
        if bite:
            recruit = False
        if fight:
            recruit = False
            target = None

        if target and target.character.has_item("bacon"):
            self.roles.bacon = None
            self.say(str(Narrative.Notify.Target.baconEscape), target)
            self.say_list(
                str(Narrative.Notify.Wolves.baconEscape) % {"target": target},
                self.roles.wolves,
            )
            self.botSend(
                ("NWESCAPE", target.isolate(), "BACON"),
                [p.user for p in self.roles.wolves],
            )
            self.botSend(("NTESCAPE", "BACON"), target)
            target = None

        if target and random.uniform(0, 100) < self.conf.survival:
            self.say(str(Narrative.Notify.Target.survivalEscape), target)
            self.say_list(
                str(Narrative.Notify.Wolves.survivalEscape) % {"target": target},
                self.roles.wolves,
            )
            self.botSend(
                ("NWESCAPE", target.isolate(), "SURVIVAL"),
                [p.user for p in self.roles.wolves],
            )
            self.botSend(("NTESCAPE", "SURVIVAL"), target)
            target = None

        self.wolf_attack = (target, recruit)

        witch = self.roles.witch
        if target and not recruit and witch:
            self.state = State.WitchingHour
            if target == witch:
                if witch.has_item("beer"):
                    self.say(
                        "You have a vision... the wolves are going to attack YOU! You have 2 mins to save yourself with beer%s."
                        % ("" or witch.has_item("cider") and " or attack with cider'"),
                        witch,
                    )
                elif witch.has_item("cider"):
                    self.say(
                        "You have a vision... the wolves are going to attack YOU! You have 2 mins to save yourself but, OH NOES! You already used your beer! You have one last chance to strike back with cider.",
                        witch,
                    )
                else:
                    self.say(
                        "You have a vision... the wolves are going to attack YOU! You have 2 mins to save yourself but, OH NOES! You already used your beer! Nothing to do but use sleep and hope you don't wake up again to feel it. Sweet dreams!",
                        witch,
                    )
                self.set_timer(90, self.game_witch_warning)
            else:
                if witch.has_item("beer") or witch.has_item("cider"):
                    options = []
                    if witch.has_item("beer"):
                        options.append("save them with beer")
                    if witch.has_item("cider"):
                        options.append("poison someone with cider")
                    self.say(
                        "You have a vision... the wolves are going to attack %s! You have 2 mins to %s."
                        % (target, " or ".join(options)),
                        witch,
                    )
                    self.set_timer(90, self.game_witch_warning)
                else:
                    self.say(
                        "You have a vision... the wolves are going to attack %s! There is nothing you can do though as you have used all your potions."
                        % target,
                        witch,
                    )
                    self.set_timer(0, self.game_wolf_kill)
            self.botSend(
                (
                    "WITCHSEE",
                    User(target).isolate(),
                    witch.has_item("beer"),
                    witch.has_item("cider"),
                ),
                witch.user,
            )
        elif witch:
            self.say(
                "You wake up in the night, but for once there are no bad dreams. It looks like the wolves won't be killing tonight. ",
                self.roles.witch,
            )
            if witch.has_item("cider"):
                self.state = State.WitchingHour
                self.say(
                    "You still have cider you can use to poison somebody. You have 2 mins. ",
                    self.roles.witch,
                )
                self.set_timer(90, self.game_witch_warning)
                self.botSend(
                    ("WITCHSEE", None, witch.has_item("beer"), witch.has_item("cider")),
                    witch.user,
                )
            else:
                self.set_timer(0, self.game_wolf_kill)
        else:
            self.set_timer(0, self.game_wolf_kill)

    def game_witch_warning(self):
        self.say("You have 30 seconds to decide on what to do.", self.roles.witch)
        self.botSend(("WITCHHURRY",), self.roles.witch.user)
        self.set_timer(30, self.game_witch_attack)

    def game_witch_attack(self):
        if self.cider:
            if self.cider.character.role == Roles.Hunter:
                self.say(str(Narrative.Notify.Hunter.witchAttack), self.roles.hunter)
                self.botSend(
                    ("DEATHREASON", self.roles.hunter.user.isolate(), "WITCH"),
                    self.roles.hunter.user,
                )
                return self.hunter_death(self.game_wolf_kill)
            else:
                self.say(str(Narrative.Notify.Target.witchAttack), self.cider)
        return self.set_timer(0, self.game_wolf_kill)

    def game_wolf_kill(self):
        if self.wolf_attack[0] and not self.beer:
            if (
                self.wolf_attack[0].character == Roles.Hunter
                and not self.wolf_attack[1]
            ):
                self.say(str(Narrative.Notify.Hunter.wolfAttack), self.roles.hunter)
                self.botSend(
                    ("DEATHREASON", self.roles.hunter.user.isolate(), "WOLF"),
                    self.roles.hunter.user,
                )
                return self.hunter_death(self.game_inspector)
        self.set_timer(0, self.game_inspector)

    def game_inspector(self):
        self.state = State.Stalking
        if self.roles.inspector and not self.stalked:
            self.set_timer(60, self.game_dawn)
            self.say(
                "You have 60 seconds left to choose who to stalk.", self.roles.inspector
            )
            self.botSend(("INSPECTORHURRY",), self.roles.inspector.user)
        else:
            self.set_timer(0, self.game_dawn)

    def game_dawn(self):
        self.state = State.Discussion
        self.say(str(Narrative.Events.sunrise))
        if self.cider:
            self.botSend(("DEATHREASON", self.cider.isolate(), "WITCH"))
            self.death(
                self.cider, str(Narrative.Death.witchAttack) % {"victim": self.cider}
            )
        if not self.wolf_attack[0]:
            self.say(str(Narrative.Notify.All.wolfFail))
        else:
            if self.wolf_attack[1]:
                self.say(
                    str(Narrative.Notify.Target.wolfScratch)
                    % {"wolves": self.format_list(self.roles.wolves)},
                    self.wolf_attack[0],
                )
                self.say(str(Narrative.Notify.All.wolfScratch))
                self.botSend(
                    ("NWWOLFRECRUIT", self.wolf_attack[0].isolate()),
                    [p.user for p in self.roles.wolves],
                )
                self.botSend(
                    ("NTWOLFRECRUIT", [p.user.isolate() for p in self.roles.wolves]),
                    self.wolf_attack[0],
                )
                self.botSend(("WOLFRECRUIT",))
                self.roles.wolves.append(self.wolf_attack[0])
                self.recruit = False
            elif self.beer:
                self.say_list(
                    str(Narrative.Notify.Wolves.beerEscape)
                    % {"target": self.wolf_attack[0]},
                    self.roles.wolves,
                )
                self.botSend(
                    ("NWESCAPE", self.wolf_attack[0].isolate(), "BEER"),
                    [p.user for p in self.roles.wolves],
                )
                self.botSend(("NTESCAPE", "BEER"), self.wolf_attack[0])
                if self.wolf_attack[0] != self.roles.witch:
                    self.say(
                        str(Narrative.Notify.Target.beerEscape), self.wolf_attack[0]
                    )
            else:
                self.botSend(("DEATHREASON", self.wolf_attack[0].isolate(), "WOLF"))
                self.death(
                    self.wolf_attack[0],
                    str(Narrative.Death.wolfAttack) % {"victim": self.wolf_attack[0]},
                )
        self.lynchings = 1 + self.conf.doublelynch
        self.set_timer(30, self.game_proposals)
        self.update_topic()
        if not self.test_victory():
            self.say(str(Narrative.Events.mobForm))

    def game_proposals(self):
        self.state = State.Day
        self.update_topic()
        self.say(str(Narrative.Events.mobPropose))
        self.proposals = {}
        self.last = None
        self.nominee = None
        self.proposer = None
        self.seconder = None
        self.passCount = 0
        if len(self.alive) == len(self.roles.wolves) * 2:
            self.say(
                "In this situation, to avoid stalemate, if 50% of villagers use '!pass' then no lynching will take place."
            )
            self.botSend(("STALEMATE",))

    def game_nominate(self):
        self.state = State.Discussion
        self.nominee = self.proposals[self.proposer]
        self.proposals[self.proposer] = None
        self.say(str(Narrative.Events.mobChoose) % {"nominee": self.nominee})
        self.set_timer(30, self.game_vote)

    def game_vote(self):
        self.state = State.Voting
        self.say(str(Narrative.Events.mobVote) % {"nominee": self.nominee})
        self.update_topic()
        self.votes = {}
        if len(self.alive) > 3:
            self.votes[self.proposer] = 1
            self.votes[self.seconder] = 1
            self.botSend(("VOTE", self.proposer.isolate(), "AYE"))
            self.botSend(("VOTE", self.seconder.isolate(), "AYE"))
        self.votes[self.nominee] = -1
        self.botSend(("VOTE", self.nominee.isolate(), "NAY"))
        self.set_timer(90, self.game_vote_warning)

    def game_vote_warning(self):
        unvoted = list(set(self.alive) - set(self.votes.keys()))
        self.say(
            "Waiting for %s to vote. You have 30 seconds left. "
            % self.format_list(unvoted)
        )
        self.botSend(("VOTEHURRY",), unvoted)
        self.set_timer(30, self.game_count_votes)

    def game_count_votes(self):
        total = 0
        for player in self.alive:
            total += self.votes.get(player, -1)
        if total <= 0:
            self.say(str(Narrative.Events.mobFail) % {"nominee": self.nominee})
            self.state = State.Day
            self.last = datetime.datetime.now()
            return
        if self.nominee.character == Roles.Hunter:
            self.botSend(
                ("DEATHREASON", self.roles.hunter.user.isolate(), "LYNCH"),
                self.roles.hunter.user,
            )
            self.hunter_death(self.game_lynch)
        else:
            self.set_timer(0, self.game_lynch)

    def game_lynch(self):
        self.state = State.Discussion
        self.botSend(("DEATHREASON", self.nominee.isolate(), "LYNCH"))
        self.death(
            self.nominee, str(Narrative.Death.lynched) % {"victim": self.nominee}
        )
        self.lynchings -= 1
        if self.lynchings:
            self.say(str(Narrative.Events.mobContinue) % {"victim": self.nominee})
            self.set_timer(30, self.game_proposals)
        else:
            self.set_timer(30, self.game_night)
        self.test_victory()
        self.update_topic()

    def game_pass(self):
        self.say(str(Narrative.Events.mobDismissed))
        self.state = State.Discussion
        self.set_timer(0, self.game_night)

    def game_over(self):
        self.state = State.NoGame
        self.update_topic()

    #                                       ++++++++++ VICTORY CONDITIONS ++++++++++

    def test_victory(self):
        if self.characters == self.roles.lovers:
            return self.victory_lovers()
        if self.characters == self.roles.villagers:
            return self.victory_innocent()
        if self.characters == self.roles.wolves:
            return self.victory_wolves()
        if self.characters == self.roles.vampires:
            return self.victory_vampires()
        if self.characters == self.roles.zombies:
            return self.victory_zombies()
        # This was the old win condition for wolves - it assumes that if the wolves outnumber everyone else, they win
        # It probably doesn't hold with other rules or factions
        # if len(self.alive) <= len(self.roles.wolves) * 2 - (self.roles.witch.has_item("cider")): return self.victory_wolves()
        return False

    def victory_innocent(self):
        self.say(
            str(Narrative.Victory.innocent)
            % {"villagers": self.format_list(self.alive)}
        )
        self.botSend(("VICTORY", "Innocent"))
        self.set_timer(10, self.game_over)
        return True

    def victory_wolves(self):
        self.say(
            str(Narrative.Victory.wolves)
            % {"wolves": self.format_list(self.roles.wolves)}
        )
        self.botSend(("VICTORY", "Wolves"))
        self.set_timer(10, self.game_over)
        return True

    def victory_vampires(self):
        self.say(
            str(Narrative.Victory.vampires)
            % {"vampires": self.format_list(self.roles.vampires)}
        )
        self.botSend(("VICTORY", "Vampires"))
        self.set_timer(10, self.game_over)
        return True

    def victory_zombies(self):
        self.say(
            str(Narrative.Victory.zombies)
            % {"zombies": self.format_list(self.roles.zombies)}
        )
        self.botSend(("VICTORY", "Zombies"))
        self.set_timer(10, self.game_over)
        return True

    def victory_lovers(self):
        self.botSend(("VICTORY", "Lovers"))
        self.say(
            str(Narrative.Victory.lovers)
            % {"lover1": self.roles.lovers[0], "lover2": self.roles.lovers[1]}
        )
        self.set_timer(10, self.game_over)
        return True

    #                                       ++++++++++ GLOBAL COMMANDS ++++++++++

    def cmd_join(self, user):
        "Usage: '!join'. Add yourself to the waiting list for the next game. When the game starts, you will then be involved. You can do this at any point."
        if user not in self.waiting:
            self.waiting.append(user)
            self.say(
                "You will be included in the next game. To leave this waiting list, use '!leave'.",
                user,
            )
            self.update_topic()
            self.start_test()
        else:
            self.say("You are already on the waiting list for the next game", user)

    def cmd_leave(self, user):
        "Usage: '!leave'. Remove yourself from the waiting list for a game."
        try:
            self.waiting.remove(user)
            self.say(
                "You will no longer be included in the next game. To re-enter the waiting list, use '!join'.",
                user,
            )
            self.update_topic()
        except ValueError:
            self.say(
                "You are not in the waiting list. To leave a game that is running, use '!suicide'.",
                user,
            )

    def cmd_clear(self, user):
        "Usage: '!clear'. Removes everybody from the waiting list for a game."
        self.say(
            "The waiting list has been cleared by %s. The waiting list contained %s. Use '!join' to enter the new waiting list."
            % (user, self.format_list(self.waiting))
        )
        self.waiting = []
        self.update_topic()

    def cmd_kick(self, user, target):
        "Usage: '!kick <target>'. Remove somebody from the waiting list for a game."
        try:
            self.waiting.remove(target)
            self.say(
                "%s has been kicked from the waiting list by %s. To re-join the next game, use '!join'."
                % (target, user)
            )
            self.update_topic()
        except ValueError:
            self.say(
                "They are not in the waiting list. You may not kick someone from an active game.",
                user,
            )

    def cmd_set_start(self, user, num):
        "Usage: '!start now' or '!start <num>'. Starts a new game immediately, or when a certain number of players join the waiting list."
        num = int(num)
        if self.state == State.NoGame:

            def start_test():
                if len(self.waiting) >= num:
                    self.cmd_start(user)

            self.start_test = start_test
            self.say("The game will start automatically after %d people join." % num)

    def cmd_start(self, user):
        "Usage: '!start now' or '!start <num>'. Starts a new game immediately, or when a certain number of players join the waiting list."
        self.start_test = lambda: None
        if self.state == State.NoGame:
            self.alive, self.ghosts, self.waiting = self.waiting, [], []
            self.say(
                "Game started by %s. Villagers are: %s. Please wait while roles are assigned."
                % (user, self.format_list(self.alive))
            )
            self.game_begin()

    def cmd_stop(self, user):
        "Usage: '!stop'. Used to terminate a game that is running. A warning and time to abort this will be given."
        if self.state == State.NoGame:
            self.say("Game is not running.", user)
            return

        def stop_timer():
            self.state = State.NoGame
            self.alive = []
            self.say("Game stopped by %s." % user)
            self.update_topic()

        self.set_timer(20, stop_timer, tag="stop timer")
        self.say(
            "Game will stopped by %s in 20 seconds. Use '!abort' to override this and continue the game."
            % user
        )

    def cmd_abort(self, user):
        "Usage: '!abort'. Used to cancel an attempt to stop the game."
        try:
            if self.check_timer("stop timer"):
                self.clear_timer("stop timer")
                self.say(
                    "Game stop sequence aborted by %s. The game will now continue."
                    % user
                )
        except (TypeError, AttributeError):
            self.say("Nobody is trying to stop the game", user)
            pass

    def cmd_conf_default(self, user):
        self.conf = Config()
        self.say(
            "Configuration has been restored to default values... %s"
            % self.format_conf(),
            user,
        )

    def cmd_conf_print(self, user):
        self.say("Current configuration... %s" % self.format_conf())

    def cmd_conf_set(self, user, option, value):
        "Usage: complicated. Used to set the rules. See the wiki."
        if option == "wolves":
            self.conf.wolves = max(1, int(value))
        elif option == "witch":
            self.conf.witch = value == "yes"
        elif option == "hunter":
            self.conf.hunter = value == "yes"
        elif option == "inspector":
            self.conf.inspector = value == "yes"
        elif option == "cupid":
            self.conf.cupid = ["no", "yes", "passive", "auto"].index(value)
        elif option == "bacon":
            self.conf.bacon = value == "yes"
        elif option == "recruiting":
            self.conf.recruiting = value == "yes"
        elif option == "EG":
            self.conf.doublelynch = value == "yes"
        elif option == "survival":
            self.conf.survival = min(100, max(0, int(value)))
        self.say("New configuration... %s" % self.format_conf(), user)

    def cmd_crash_test(self, user):
        "Usage: '!ping': Used to see if the narrator is functioning."
        if self.check_timer():
            self.say("A timer is running. Crash highly unlikely. ")
        elif self.state == State.NoGame:
            self.say("There isn't a game running ")
        elif self.state == State.Day:
            self.say("Waiting for people to propose a candidate for lynching. ")
        else:
            self.say(
                "Something seems to have gone wrong. State is State.%s"
                % self.state.__name__
            )
            self.say("This may be the time to use '!crash recovery'", user)

    def cmd_crash_fix(self, user, state=None):
        "Usage: '!crash recovery' or '!crash recovery @<state>'. Used to cause the game to restart at a sensible, or chosen point. Do not fiddle."
        if self.check_timer():
            self.say("Be patient. A timer is running.")
        else:
            self.say("Crash recovery initiated by %s." % user)
            if state:
                try:
                    self.state = getattr(State, state)
                    self.say("Setting state to State.%s" % state)
                except AttributeError:
                    self.say("State unknown, left unchanged")
            self.set_timer(0, self.game_continue)

    def cmd_copyover(self, user):
        "Usage: '!copyover'. Causes the narrator to reload almost all of its code. Used to updgrade. Do not do mid-game without good reason."
        self.say("CopyOver initiated by %s." % user)
        raise self.CopyOver

    def cmd_reboot(self, user):
        "Usage: '!reboot'. Causes the narrator to disconnect and restart. Used during serious game crashes."
        self.say("ReBoot initiated by %s." % user)
        raise self.ReBoot

    def cmd_say(self, user, msg, delay):
        "Usage: '!say <message> in <delay>s'. Say something after a certain time interval. This is a debug function."

        def say():
            self.say("[%s] %s" % (user, msg))
            self.botSend(("Message", user, msg))

        self.add_timer(delay, say)

    def cmd_bot_say(self, user, target, msg):
        "Usage: '!botsay <message>' or '!botsay ><target> <message>'. Send a message to a bot. This is a debug function."
        self.botSend(("BOTSAY", user.isolate(), msg), target and User(target))

    def cmd_ask_sock(self, user):
        "Usage: '!sock'. Request the path to the socket used for bot connections. The path is sent by private message."
        self.say(self.botPath, user)

    #                                       ++++++++++ PUBLIC COMMANDS ++++++++++

    def cmd_choose(self, user, q):
        "Usage: '!choose <something>, <something>, ... or <something>'. Randomly chooses an option from a list of any size."
        options = [o.strip() for o in re.compile(",| or ").split(q) if not o.isspace()]
        self.say(random.choice(options))

    @cmd_requirement()
    def cmd_suicide(self, user):
        "Usage: '!suicide': Used at any point to commit suicide and leave the game. Not recommended due to many bugs ;)"
        self.botSend(("DEATHREASON", user.isolate(), "SUICIDE"))
        self.death(user, str(Narrative.Death.suicide) % {"victim": user})
        self.test_victory()
        self.update_topic()

    @cmd_requirement([State.Voting, State.Discussion, State.Day], allow_self=False)
    def cmd_propose(self, user, target):
        "Usage: '!propose <target>'. Used during the day to propose somebody to by lynched. The proposal must also be seconded and is then voted on."
        if self.state == State.Voting:
            self.say("Please wait until voting is over.", user)
        if self.state == State.Discussion:
            self.say("Please wait. ", user)
        if target == self.nominee and self.last:
            delay = (datetime.datetime.now() - self.last).seconds
            if delay < 15:
                self.say(
                    "Please wait %d seconds before proposing %s again"
                    % (15 - delay, target),
                    user,
                )
                return
        if target in self.proposals.values():
            return self.cmd_second(user, target)
        self.proposals[user] = User(target)
        self.say("%s has proposed %s." % (user, self.proposals[user]))
        self.botSend(("PROPOSED", user.isolate(), User(target).isolate()))

    @cmd_requirement(State.Day, allow_self=False)
    def cmd_second(self, user, target):
        "Usage: '!second <target>'. Used to second a proposal that a player should be lynched."
        if target not in self.proposals.values():
            self.say("They have not been proposed yet.", user)
            return
        if self.proposals.get(user, None) == target:
            self.say("You may not both second and propose.", user)
            return
        self.proposer = [
            player
            for player in self.proposals.keys()
            if self.proposals[player] == target
        ][0]
        self.seconder = user
        self.say("%s has seconded %s's proposal." % (self.seconder, self.proposer))
        self.botSend(("SECONDED", user.isolate(), User(target).isolate()))
        self.set_timer(0, self.game_nominate)

    @cmd_requirement([State.Voting, State.Discussion])
    def cmd_vote(self, user, vote):
        "Usage: '!vote <vote>'. Used when voting if a player should be lynched. A vote may be 'aye', 'abstain' or 'nay', although variations on these words can be used with the same meanings."
        if self.state == State.Discussion:
            self.say("Please wait. ", user)
        if vote.lower() in Vote.aye:
            self.votes[user] = 1
            self.say("You have voted 'aye'.", user)
            self.botSend(("VOTE", user.isolate(), "AYE"))
        elif vote.lower() in Vote.abstain:
            self.votes[user] = 0
            self.say("You have voted 'abstain'.", user)
            self.botSend(("VOTE", user.isolate(), "ABSTAIN"))
        elif vote.lower() in Vote.nay:
            self.votes[user] = -1
            self.say("You have voted 'nay'.", user)
            self.botSend(("VOTE", user.isolate(), "NAY"))
        else:
            self.say("That is not a valid voting option.", user)
        if len(self.votes) == len(self.alive):
            self.set_timer(10, self.game_count_votes)

    @cmd_requirement(State.Day)
    def cmd_pass(self, user):
        "Usage: '!pass'. In the situation that a stalemate could occur, the pass command may be used to choose not to lynch anybody, and instead rely on a character such as the witch to recitify the situation at night."
        if len(self.alive) == len(self.roles.wolves) * 2:
            self.passCount += 1
            self.say("%s wishes not to lynch anybody" % user)
            self.botSend(("PASS", user.isolate()))
            if self.passCount == len(self.alive) / 2:
                self.set_timer(0, self.game_pass)
        else:
            self.say("There is no likelihood of a stalemate here")

    #                                       ++++++++++ PRIVATE COMMANDS ++++++++++

    def cmd_placeholder(self, user, **kwargs):
        "This command is a placeholder."
        self.say("Placeholder was used")

    def cmd_help(self, user, topic=""):
        "Usage: '!help <topic>'. Gives information about commands, roles and factions."
        from help import help

        self.say(help(topic), user)

    @cmd_requirement(required_role=Roles.Cupid)
    def cmd_fire(self, user, loverA, loverB):
        "Usage: '!fire <loverA> <loverB>'. Used by cupid at the start of the game to choose the lovers."
        if loverA == user or loverB == user:
            self.say("You may not fire an arrow at yourself", user)
        elif loverA not in self.alive:
            self.say("%s is not involved in the current game." % loverA, user)
        elif loverB not in self.alive:
            self.say("%s is not involved in the current game." % loverB, user)
        elif loverB == loverA:
            self.say("There must be two lovers, not one.", user)
        elif self.roles.lovers:
            self.say("The lovers have already been chosen", user)
        else:
            lovers = (
                self.characters[self.characters.index(loverA)],
                self.characters[self.characters.index(loverB)],
            )
            lovers[0].lover = lovers[1]
            lovers[1].lover = lovers[0]
            self.say(
                "Hit by your arrows, %s and %s fall madly in love." % self.roles.lovers,
                user,
            )
            self.set_timer(3, self.game_make_lover)

    @cmd_requirement(
        State.Night, required_role=Roles.Wolf, allow_self=False, allow_abstain=True
    )
    def cmd_bite(self, user, target):
        "Usage: '!bite <target>'. Used by wolves at night to kill other players. Other wolves are informed of the attack and must agree to it by either abstaing (!bite don't care) or also biting this target."
        if " " in target:
            self.votes[user] = "abstain"
            self.say("You have abstained from the attack.", user)
            for wolf in self.roles.wolves:
                if wolf != user:
                    self.say("%s does not care who is attacked." % user, wolf)
        else:
            if target in self.roles.wolves:
                self.say("They are a Wolf.", user)
                return
            self.votes[user] = ("bite", User(target))
            self.say("You have chosen to attack %s." % self.votes[user][1], user)
            for wolf in self.roles.wolves:
                if wolf != user:
                    self.say("%s plans to attack %s." % (user, target), wolf)
                    self.botSend(
                        (
                            "OTHERWOLFPICKED",
                            user.isolate(),
                            User(target).isolate(),
                            False,
                        ),
                        wolf.user,
                    )
        if len(self.votes) == len(self.roles.wolves):
            self.set_timer(10, self.game_wolf_attack)

    @cmd_requirement(
        State.Night, required_role=Roles.Wolf, allow_self=False, allow_abstain=True
    )
    def cmd_recruit(self, user, target):
        "Usage: '!scratch <target>'. Used by wolves at night to recruit new wolves. Part of the recruiting rule."
        if not self.recruit:
            self.say("You cannot recruit any more wolves.", user)
            return
        if " " in target:
            self.votes[user] = "abstain"
            self.say("You have abstained from the attack.", user)
            for wolf in self.roles.wolves:
                if wolf != user:
                    self.say("%s does not care who is attacked." % user, wolf)
        else:
            if target in self.roles.wolves:
                self.say("They are a Wolf.", user)
                return
            self.votes[user] = ("scratch", User(target))
            self.say("You have chosen to recruit %s." % self.votes[user][1], user)
            for wolf in self.roles.wolves:
                if wolf != user:
                    self.say("%s plans to recruit %s." % (user, target), wolf)
                    self.botSend(
                        (
                            "OTHERWOLFPICKED",
                            user.isolate(),
                            User(target).isolate(),
                            True,
                        ),
                        wolf.user,
                    )
        if len(self.votes) == len(self.roles.wolves):
            self.set_timer(10, self.game_wolf_attack)

    @cmd_requirement(State.WitchingHour, required_role=Roles.Witch)
    def cmd_beer(self, user):
        "Usage: '!beer'. Used at night by the with to save the life of the person due to die. Can only be done once."
        if not user.character.has_item("beer"):
            self.say("You don't have any beer left", user)
            return
        if not self.wolf_attack[0]:
            self.say("There is noone to save", user)
            return
        user.character.take_item("beer")
        self.beer = True
        self.say("You use your beer to avert the wolf attack.", user)
        if not user.character.has_item("cider"):
            self.cmd_sleep(user)

    @cmd_requirement(State.WitchingHour, required_role=Roles.Witch)
    def cmd_cider(self, user, target):
        "Usage: '!cider <target>'. Used by the witch to kill somebody at night with cider. Can only be done once."
        if not user.character.has_item("cider"):
            self.say("You don't have any cider left", user)
            return
        if target == user:
            self.say("I wouldn't drink that foul stuff yourself!", user)
            return
        if target == self.wolf_attack[0] and not self.wolf_attack[1]:
            self.say(
                "The wolves are already after %s. Stop being silly." % target, user
            )
            return
        user.character.take_item("cider")
        self.cider = User(target)
        self.say("You poison %s with a pint of deadly cider." % self.cider, user)
        if not user.character.has_item("beer"):
            self.cmd_sleep(user)

    @cmd_requirement(State.WitchingHour, required_role=Roles.Witch)
    def cmd_sleep(self, user):
        "Usage: '!sleep'. Used by the witch when they do not wish to use a potion that night."
        self.say("You go back to sleep.", user)
        self.set_timer(0, self.game_witch_attack)

    @cmd_requirement([State.Night, State.WitchingHour, State.Stalking])
    def cmd_cuddle(self, user, target):
        "Usage: '!cuddle <target>'. Used by lonely players to give another player a cuddle at night"
        if target == user:
            self.say("It just doesn't feel the same cuddling yourself...", user)
            return
        self.say("You cuddle up to %s." % target, user)
        self.say("%s cuddles up to you." % user, target)

    @cmd_requirement(
        [State.Night, State.WitchingHour, State.Stalking], require_alive=False
    )
    def cmd_spook(self, user, target):
        "Usage: '!spook <target>'. Used by ghosts to scare people at night"
        if self.state not in [State.Night, State.WitchingHour, State.Stalking]:
            return
        if user not in self.ghosts:
            self.say("They would see you", user)
            return
        self.say("You haunt %s in the night." % target, user)
        self.say("WooOOOOooooo! %s spooks you!" % user, target)

    @cmd_requirement(
        [State.Night, State.WitchingHour, State.Stalking], required_role=Roles.Inspector
    )
    def cmd_stalk(self, user, target):
        "Usage: '!stalk <target>'. Used by the inspector each night to discover somebodies role."
        if self.stalked:
            self.say("You can only stalk one person each night", user)
            return
        if target == user:
            self.say(
                "You are the Inspector. Perhaps you want to stalk someone else tonight...",
                user,
            )
            return
        self.stalked = True
        if target in self.roles.wolves:
            self.say(str(Narrative.InspectorReveal.wolf) % {"target": target}, user)
            self.botSend(("INSPECTED", User(target).isolate, Roles.Wolf), user)
        elif target == self.roles.witch:
            self.say(str(Narrative.InspectorReveal.witch) % {"target": target}, user)
            self.botSend(("INSPECTED", User(target).isolate, Roles.Witch), user)
        elif target == self.roles.hunter:
            self.say(str(Narrative.InspectorReveal.hunter) % {"target": target}, user)
            self.botSend(("INSPECTED", User(target).isolate, Roles.Hunter), user)
        elif target == self.roles.cupid:
            self.say(str(Narrative.InspectorReveal.cupid) % {"target": target}, user)
            self.botSend(("INSPECTED", User(target).isolate, Roles.Cupid), user)
        else:
            self.say(str(Narrative.InspectorReveal.innocent) % {"target": target}, user)
            self.botSend(("INSPECTED", User(target).isolate, Roles.Villager), user)
        if self.state == State.Stalking:
            self.set_timer(5, self.game_dawn)

    @cmd_requirement(State.Revenge, required_role=Roles.Hunter, allow_self=False)
    def cmd_shoot(self, user, target):
        "Usage: '!shoot <target>'. When the hunter is killed, they use this command to choose who to take down with them."
        self.revenge(self.alive[self.alive.index(target)])

    def cmd_bot_register(self, user, name):
        "Usage: '!bot <socket name>'. Used by bots to register for structured event updates via UNIX socket."
        user.isBot = True
        if self.botRegister(user, name):
            self.say("Socket registration complete", user)
        else:
            self.say("Error: Could not find a socket with this name", user)

    #                                       ++++++++++ COMMAND LISTINGS ++++++++++

    cmds_global = [
        Command("^!join$", cmd_join),
        Command("^!leave$", cmd_leave),
        Command("^!clear$", cmd_clear),
        Command(r"^!kick (?P<target>\S+)$", cmd_kick),
        Command("^!start now$", cmd_start),
        Command(r"^!start (?P<num>\d+)$", cmd_set_start),
        Command("^!stop$", cmd_stop),
        Command("^!abort$", cmd_abort),
        Command("^!conf print$", cmd_conf_print),
        Command("^!conf default$", cmd_conf_default),
        Command(
            "^!conf (?P<option>witch|hunter|inspector|bacon|recruiting|EG) (?P<value>yes|no)$",
            cmd_conf_set,
        ),
        Command(r"^!conf (?P<option>wolves) (?P<value>\d+)$", cmd_conf_set),
        Command(
            "^!conf (?P<option>cupid) (?P<value>no|yes|passive|auto)$", cmd_conf_set
        ),
        Command(r"^!conf (?P<option>survival) (?P<value>\d+)%$", cmd_conf_set),
        Command("^!ping$", cmd_crash_test),
        Command("^!crash recovery$", cmd_crash_fix, name="crash recovery"),
        Command(
            r"^!crash recovery @State\.(?P<state>\w+)$",
            cmd_crash_fix,
            name="crash recovery",
        ),
        Command("^!copyover$", cmd_copyover),
        Command("^!reboot$", cmd_reboot),
        Command(r"^!botsay (>(?P<target>\S+) )?(?P<msg>.+)$", cmd_bot_say),
        Command("^!sock$", cmd_ask_sock),
    ]

    cmds_private = [
        Command(r"^!help (?P<topic>.+)$", cmd_help),
        Command(r"^!fire (?P<loverA>\S+) (?P<loverB>\S+)$", cmd_fire),
        Command(r"^!(bite|kill|attack) (?P<target>\S+|don'?t care)$", cmd_bite, "bite"),
        Command(r"^!(scratch|recruit) (?P<target>\S+)$", cmd_recruit, "scratch"),
        Command(r"^!stalk (?P<target>\S+)$", cmd_stalk),
        Command(r"^!cuddle (?P<target>\S+)$", cmd_cuddle),
        Command(r"^!spook (?P<target>\S+)$", cmd_spook),
        Command("^!beer$", cmd_beer),
        Command(r"^!cider (?P<target>\S+)$", cmd_cider),
        Command("^!sleep$", cmd_sleep),
        Command(r"^!shoot (?P<target>\S+)$", cmd_shoot),
        Command(r"^!bot (?P<name>\S+)$", cmd_bot_register),
        Command(r"^!mod (?P<pwd>\S+)$", Bot.cmd_mod_login),
        Command("^!shell$", Bot.cmd_shell),
    ]

    cmds_public = [
        Command("^!help$", cmd_help),
        Command(r"^!say (?P<msg>.+) in (?P<delay>\d+)s$", cmd_say),
        Command(r"^!choose (?P<q>.+?)\??$", cmd_choose),
        Command("^!suicide$", cmd_suicide),
        Command(r"^!propose (?P<target>\S+)$", cmd_propose),
        Command(r"^!second (?P<target>\S+)$", cmd_second),
        Command("^!vote (?P<vote>[^!]+)!*$", cmd_vote),
        Command("^!pass$", cmd_pass),
    ]

    #                                       ++++++++++ CRASH RECOVERY ++++++++++

    def game_continue(self):
        if self.state == State.NoGame:
            self.say("Game is not running. ")
        elif self.state == State.Initialising:
            self.say("Game has not fully begun. Reassigning roles.")
            return self.game_begin()
        elif self.state == State.Night:
            self.say("Was waiting for wolves to attack. Restarting at sunset.")
            return self.game_night()
        elif self.state == State.WitchingHour:
            self.say(
                "Was waiting for witch to respond. Witch will be given 30 seconds to respond. "
            )
            return self.game_witch_warning()
        elif self.state == State.Stalking:
            self.say(
                "Was waiting for investigator to respond. Investigator will be given 60 seconds to respond. "
            )
            return self.game_investigator()
        elif self.state == State.Day:
            self.say("Waiting for proposals. Restarting at proposals. ")
            return self.game_proposals()
        elif self.state == State.Discussion:
            self.say("In discussion time. Restarting at proposals. ")
            return self.game_proposals()
        elif self.state == State.Voting:
            self.say("Voting on a nominee for lynching. Restarting at proposals. ")
            return self.game_proposals()
        elif self.state == State.Revenge:
            self.say(
                "Waiting for hunter to take revenge. Not sure where to restart. Trying dawn. "
            )
            return self.game_dawn()


#                   +++++ +++++ MAIN LOOP +++++ +++++

if __name__ == "__main__":

    import bootstrap

    bootstrap.main(
        nick="Mayonaise",
        host="localhost",
        channel="#failmoon",
        socket="fullmoon.sock",
    )
