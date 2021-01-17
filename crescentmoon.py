#!/usr/bin/python
"""
#bots - A game by Joe Taylor of Durham University Computing Society

See our wiki for rules - http://compsoc.dur.ac.uk/mediawiki/index.php/Fullmoon

Many thanks to various people, most notably inclement, for the narrative
"""

from time import sleep
import lolbot, re, datetime, random, traceback, base64, pickle
import Sheep3

MOD_PWD = "h1ccup"
SHELL = False


class User(object):
    def __init__(self, nick):
        self.nick = str(nick)

    def __cmp__(self, nick):
        return cmp(self.nick.lower(), str(nick).lower())

    def __str__(self):
        return self.nick

    def __add__(self, other):
        return self.nick + str(other)

    def __radd__(self, other):
        return str(other) + self.nick

    def __repr__(self):
        return str(self)

    def change(self, nick):
        self.nick = nick


class Command(object):
    def __init__(self, regex, cmd):
        if regex[-1] == "$":
            regex = regex[:-1] + "\s*(\#.*)?$"
        self.regex = re.compile(regex)
        self.cmd = cmd
        self.match = None

    def __call__(self, s, user):
        try:
            return self.cmd(s, user, **self.match.groupdict())
        except Exception, e:
            print e
            raise
            return None

    def __cmp__(self, cmd):
        self.match = self.regex.match(cmd)
        if self.match:
            return 0
        return -1


class State:
    class NoGame:
        pass

    class Initialising:
        pass

    class Night:
        pass

    class WitchingHour:
        pass

    class Stalking:
        pass

    class Day:
        pass

    class Discussion:
        pass

    class Voting:
        pass

    class Revenge:
        pass


class Config:
    wolves = 1
    witch = False
    hunter = False
    inspector = False
    cupid = 0  # 0 = none; 1 = normal; 2 = passive; 3 = auto
    bacon = False
    recruiting = False
    doublelynch = False
    survival = 0  #%


class Roles:
    wolves = []
    witch = None
    hunter = None
    inspector = None
    cupid = None
    lovers = []
    bacon = None
    cheese = None

    def kill(self, user):
        role = []
        if self.witch == user:
            self.witch = None
            role.append("witch")
        if self.hunter == user:
            self.hunter = None
            role.append("hunter")
        if self.inspector == user:
            self.inspector = None
            role.append("inspector")
        if self.cupid == user:
            self.cupid = None
            role.append("cupid")
        if self.bacon == user:
            self.bacon = None
            role.append("bacon")
        if self.cheese == user:
            self.cheese = None
            role.append("cheese")
        if user in self.wolves:
            self.wolves.remove(user)
            role.append("wolf")
        if user in self.lovers:
            self.lovers = list(self.lovers)
            self.lovers.remove(user)
            role.append("lover")
        return role


class Vote:
    aye = ["aye", "yes", "yup", "lynch", "kill", "taken", "squee", "die"]
    abstain = ["abstain", "pass", "none", "meh", "don't care"]
    nay = [
        "nay",
        "no",
        "never",
        "nope",
        "save",
        "release",
        "spare",
        "avast",
        "noooo",
        "nooo",
    ]


class RandLine(object):
    def __init__(self, *lines):
        self.lines = lines

    def __str__(self):
        return random.choice(self.lines)


class Narrative:
    class DeathReveal:  # must end in ". "
        wolf = RandLine(
            "According to their will they were a werewolf all along. Hoorah! And how very helpful... ",
            "The cellar full of all those missing body parts is a dead giveaway. They were a werewolf all along! ",
            "With that much hair, they *must* have been a werewolf. ",
            "Such sharp teeth they had. And such a long tail! ",
            "They must have been a werewolf all along. Allergic reactions to silver don't usually extend to spontaneous combustion. ",
            "What an interesting collection of dismembered body parts they have in their fridge. Only a WOLF would eat that! ",
        )
        witch = RandLine(
            "The big bubbling pot of potion is a dead giveaway. ",
            "They try to fly away on a broomstick, but luckily such a device doesn't actually have a means of propulsion. Anyway, THEY'RE A WITCH. ",
            "Washing off their makeup reveals green skin (which all witches have). Witch! ",
            "Only a witch would have needed all of those spellbooks. ",
        )
        inspector = RandLine(
            "Their collection of magnifying glasses is incredible. They must have been an inspector! ",
            "A search of body reveals their official papers. They were an inspector all along. Oops, this might have been a *real* crime... ",
            "After tearing apart the body, you find their diary. You read it and...oops, you just killed the inspector! ",
        )
        hunter = RandLine(
            "You've grossly underestimated them, as they bring out a gun and manage to fire a shot off before being ripped to pieces. ",
            "Their cunningly hidden pump action shotgun claims a victim before they are overwhelmed! ",
            "They are only brought down after a difficult chase, and shots are fired before the end! ",
        )
        cupid = RandLine(
            "They were cupid. Oops. ",
            "A quick search of their house reveals a funny bow and list of happy couples. This person was cupid! ",
            "Oh no, you just killed cupid! And weddings are so *fun* :( ",
        )
        innocent = RandLine(
            "A search of their house and property doesn't find anything incriminating. It looks like they weren't a werewolf after all. ",
            "The howling as night falls is undiminished. Looks like they weren't a werewolf after all. ",
            "Their necklace is real silver, but they've often been seen wearing it. Not a werewolf! ",
            "Their relatives testify that they were at home all night. Not a wolf after all! ",
            "That wasn't a real tail, this is a furry, not a werewolf! ",
        )
        bacon = RandLine(
            "They have BACON. Everything else is put on hold to allow OM NOM NOM. ",
            "OM NOM NOM. They has bacon. ",
        )
        cheese = RandLine(
            "For some reason they had cheese in their pockets. ",
            "They were carrying around a small block of cheddar. ",
            "It appears they have a pet cheese. ",
            "Why are they carrying a block of cheese around? ",
            "What a fine looking Bree they have stashed in their slacks. ",
            "They are hiding a delightful blue cheese under their hat. ",
        )

    class InspectorReveal:
        wolf = RandLine(
            "You follow %(target)s into the woods and see them change into a snarling beast! ",
            "You sneak into the house of your stalkee. There are bloody remains - clearly, you have stalked a wolf!",
            "There is wolf hair all over their house and the floor is littered with squeeky toys.",
        )
        witch = RandLine(
            "You sneak into %(target)s's house and find all manner of potions and spell books. Witch!",
            "Sneaking into %(target)s's house, you find a number of jars of potion. They're a witch!",
            "You try to sneak into house, but are chased away by a flying broomstick. Never mind, this is probably enough evidence on its own",
        )
        hunter = RandLine(
            "You sneak into %(target)s's bedroom and find a shotgun hidden under the bed. Seems this person could be dangerous!",
            "They're always polishing their guns, and have more hidden than most of the villagers have realised. This person is the hunter!",
        )
        cupid = RandLine(
            "You search through %(target)s's belongings and find a bizarre bow and arrow. Weirdo - and probably also cupid.",
            "You check the records and observe an unusually high attendance at weddings. In fullmoonland this is enough to declare CUPID!",
        )
        innocent = RandLine(
            "You follow %(target)s home at night but they do nothing but have a cup of tea and head to bed.",
            "Nothing suspicious, this person seems perfectly normal.",
            "They seem to have a fetish for LaTeX, but other than that they are rather normal",
            "You find several animal costumes and a large collection of stuffed animals. This just makes them an innocent furry though. ",
        )

    class Death:  # must end in ". "
        wolfAttack = RandLine(
            "%(victim)s is missing a head. "
            "%(victim)s's mauled body was found in the woods. ",
            "%(victim)s's severed head was found lying in the market square. ",
            "Blood splatter was found on the walls of %(victim)s's house and a bloody trail led to the woods. ",
            "%(victim)s disappeared during the night, leaving no trace. The hours of screaming is your only clue as to their fate. ",
            "Bloody letters on the wall say that %(victim)s tasted like chicken. ",
            "Only a bloody handprint on the door to %(victim)s's house remains of them. ",
            "%(victim)s's headless body was found at the bottom of the village well. ",
            "You're fairly sure that arm belongs to %(victim)s. Probably don't want to know where the rest of them went. ",
            "Something ate %(victim)s; nobody could be *that* bad at shaving. ",
            "Either there's been a wolf attack, or %(victim)s tripped and gored themselves all over. ",
            "The remains of an unfortunate squirrel were found by %(victim)s bloody corpse. ",
            "%(victim)s doesn't appear to be moving. They are also missing their spleen. ",
        )
        hunterAttack = RandLine(
            "%(hunter)s shoots %(victim)s dead with his hunting rifle. ",
            "%(hunter)s shoots %(victim)s dead with his shotgun. ",
            "%(hunter)s shoots %(victim)s dead with his bow and arrow. ",
            "%(hunter)s shoots %(victim)s dead with his pistol. ",
            "%(hunter)s shoots %(victim)s dead with his ion cannon. ",
            "%(hunter)s shoots %(victim)s dead with his phaser. ",
            "%(hunter)s shoots %(victim)s dead with his bolter. ",
        )
        witchAttack = RandLine(
            "%(victim)s was found frothing at the mouth. Looks like they angered a witch! ",
            "%(victim)s seems to have choked whilst drinking some bizarre blue liquid... ",
        )
        lover = RandLine(
            "%(victim)s dies of a broken heart mouring their %(lover)s. ",
            "%(victim)s explodes at the very moment their %(lover)s dies. ",
            "%(victim)s has been reading too much Romeo and Juliet. They're found dead soon after their lover, %(lover)s, dies. ",
        )
        lynched = RandLine(
            "%(victim)s becomes the target of the mob's hatred, and is torn apart! ",
            "The rabid mob attacks %(victim)s. ",
            "The lynch mob has spoken! %(victim)s is attacked and quickly beaten to death. ",
            "%(victim)s is taken up to the gallows and the whole village plays hangman. ",
        )
        suicide = RandLine(
            "%(victim)s couldn't take the pressure. They hung themselves in their bedroom. ",
            "Fearing the worst, %(victim)s commits suicide with a paperclip and a small bottle of Salad Cream. ",
            "Unable to cope, %(victim)s took their own life with some duct tape and a pair of trousers. ",
            "Perhaps %(victim)s thought they could fly. Maybe they just couldn't take it anymore. Either way, %(victim)s probably shouldn't have jumped off that cliff if they wanted to live. ",
        )

    class Notify:
        class Target:
            witchAttack = "This looks like a tasty pint of cider... *GLUG GLUG GLUG* - ACK! Green foam is coming from your mouth. Oh, and you're dead."
            baconEscape = "The wolves have come to attack you! You throw them your BACON and run off safely."
            survivalEscape = "You're woken in your bed by something crashing through the window, but somehow manage to fend it off and escape through the front door. You've got lucky, and managed to survive another night!"
            beerEscape = "You were attacked, but saved by an unknown saviour with a pint of beer."
            wolfScratch = "You're woken in your bed by something crashing through the window and biting you. You manage to fend it off, but it's too late - you have joined the werewolves! The culprits: %(wolves)s."

        class Hunter:
            witchAttack = "This looks like a tasty pint of cider... *GLUG GLUG GLUG* - ACK! Green foam is coming from your mouth. You won't go down this easily, REVENGE!"
            wolfAttack = "The wolves have come to attack you but you're waiting with your gun ready. They're fast, but there's time for a shot before they reach you."

        class Wolves:
            baconEscape = RandLine(
                "You leap, the scent of blood in your OMGBACON. OM NOM NOM. Never mind.",
                "You can see %(target)s... so vunerable... so easy to kill... wait, is that BACON? OM NOM NOM! ",
            )
            survivalEscape = "You crash through your %(target)s's window, entering their house, but in the melee they manage to escape."
            beerEscape = RandLine(
                "Your target was saved by the witch. Stupid witch :(",
                "That pesky witch saved %(target)s from your attack! ",
            )

        class All:
            wolfScratch = "The wolves made quite a kerfuffle, but noone seems to have been harmed. Unless...could there be another wolf!?"
            wolfFail = RandLine(
                "The wolves have not attacked tonight. Hooray for beurocracy.",
                "Despite all that howling, nobody was killed at all. Hurrah!",
                "It seems the wolves lived off squirrels alone last night...",
            )

    class Events:
        sunset = RandLine(
            "Sunset has arrived again and the rising moon is greeted by howling. The villagers huddle in their houses, hoping desperately to be allowed to survive the night.",
            "With the setting of the sun, a chorus of howls greet the rising moon.",
            "The villages huddle in their houses, watching fearfully as the sun slips below the horizon",
        )
        sunrise = RandLine(
            "Sunrise.",
            "A cock crows.",
            "The sun rises, the sky turning a delightful blood red as it does.",
            "The villagers wake up to another sunny day.",
        )
        mobForm = RandLine(
            "A fearful mob gathers, looking for someone to blame for the nightly howling. It's only a matter of time before they're angry and drunk enough to suggest a target. ",
            "With the sun high in the sky, the villagers grow bold and prepare to fight back. Before long this could turn pretty nasty! ",
            "Safe in the sunlight, the villagers leave the safety of their homes and gather in the market square. Full of fear and anger, they discuss who they suspect to be behind the killing. For now voices are raised but fists are not. For now anyway... ",
        )
        mobPropose = "The mob's ferocity has reached killing point. They have begun to suggest targets for their anger!"
        mobChoose = "The mob is angry! %(nominee)s is suspected of being a werewolf! What do they have to say for themselves?"
        mobVote = "The time has come. Should %(nominee)s be lynched? You have up to 2 minutes to decide, cast your votes now!"
        mobFail = "A so %(nominee)s is spared by the mob, but the people are still scared and angry. Who will be suspected now?"
        mobDismissed = "Seeing the futility of their plans, the mob departs home hoping not to be the next victim."
        mobContinue = "Not satisfied with killing %(victim)s the mob remains, still bloodthirsty and willing to attack another victim. Other candidates may be suggested."

    class Victory:
        innocent = RandLine(
            "The innocents win (though only by tearing apart their friends until the ones that happen to be evil are dead)! Remaining villagers: %(villagers)s",
            "The peasants rejoice! The werewolves that plagued this village have been eradicated! Remaining villagers: %(villagers)s",
            "Xenophobia prevails! Long live the superior race! Remaining villagers: %(villagers)s",
        )
        wolves = RandLine(
            "Wolves win! Remaining wolves: %(wolves)s",
            "Wolves win! Remaining wolves: %(wolves)s",
            "Wolves win! Remaining wolves: %(wolves)s. Help! I'm stuck in a #bots writing factory!",
        )
        lovers = RandLine(
            "Oh baby! %(lover1)s and %(lover2)s get it on! inclement: Bad Aule! But I won't delete this for some reason",
            "The two lovers remain, and live happily ever after. UNTIL NEXT TIME...",
        )


class Narrator(lolbot.Bot):
    class CopyOver(Exception):
        pass

    class ReBoot(Exception):
        pass

    def BotCmd(self, command, target="#bots"):
        if target == "#bots":
            for bot in self.sheepdata.values():
                bot.BotCommandCall(*command)
        elif str(target) in self.sheepdata:
            self.sheepdata[str(target)].BotCommandCall(*command)
        else:
            print "unknown target!"

    def BotCmd_list(self, command, targetlist):
        for target in targetlist:
            self.BotCmd(command, target)

    def init(self, log):
        self.mayorname = "MunicipalMayor"
        self.log = log
        self.mod = None
        self.waiting = []
        self.alive = []
        self.ghosts = []
        self.start_test = lambda: None
        self.timer = None
        self.topic = ""
        self.help = False
        self.s.send("JOIN #bots\r\n")
        self.state = State.NoGame
        self.conf = Config()
        self.throttle_data = []
        self.shell = None
        self.sheepdata = {}
        self.sheepremove = []

    def loop(self):
        if self.timer:
            if datetime.datetime.now() > self.timer[0]:
                fn = self.timer[1]
                self.timer = None
                fn()

    def set_timer(self, delay, fn):
        self.timer = (datetime.datetime.now() + datetime.timedelta(0, float(delay)), fn)

    def NICK(self, tail, user, **spare):
        if user in self.alive and tail not in self.alive:
            self.alive[self.alive.index(user)] = tail
        if user in self.waiting and tail not in self.waiting:
            self.waiting[self.waiting.index(user)] = tail
        if user in self.ghosts and tail not in self.ghosts:
            self.ghosts[self.ghosts.index(user)] = tail
        if user == self.mod:
            self.mod = tail

    def PRIVMSG(self, params, tail, user, **spare):
        if self.shell != None and user == self.mod:
            if params[0][0] != "#":
                return self.Shell(tail)
        if tail[0] != "!":
            return

        def runcmd(cmds):
            try:
                cmds[cmds.index(tail)](self, User(user))
            except ValueError:
                pass  # not a command

        runcmd(self.cmds_global)
        if params[0][0] != "#":
            runcmd(self.cmds_private)
        elif params[0] == "#bots":
            runcmd(self.cmds_public)

    def Shell(self, code):
        if not SHELL:
            self.shell = None
            return
        if code in ["?", "??"]:
            self.log(
                "*** SHELL-QUERY: %s\nby %s\n%s\n"
                % (datetime.datetime.now(), self.mod, self.shell)
            )
            try:
                r = eval(self.shell, globals(), {"self": self})
                for line in str(r).splitlines():
                    self.say("> %s" % line, self.mod)
            except Exception, e:
                self.say("Error: %s" % e, self.mod)
                self.log(
                    "*** PEBKAC: %s\n%s\n"
                    % (datetime.datetime.now(), traceback.format_exc())
                )
        if code in ["!", "!!"]:
            self.log(
                "*** SHELL-EXEC: %s\nby %s\n%s\n"
                % (datetime.datetime.now(), self.mod, self.shell)
            )
            try:
                exec self.shell in globals(), {"self": self}
                self.say("Done", self.mod)
            except Exception, e:
                self.say("Error: %s" % e, self.mod)
                self.log(
                    "*** PEBKAC: %s\n%s\n"
                    % (datetime.datetime.now(), traceback.format_exc())
                )
        if code in ["!!", "??", ".."]:
            self.shell = ""
            self.say("Ready for new input", self.mod)
        elif code in ["!", "?", "."]:
            self.shell = None
        else:
            self.shell += code + "\n"

    def TOPIC(self, tail, **spare):
        self.topic = tail

    def throttle(self, msg):
        size = len(msg)
        self.throttle_data.append(
            (
                size,
                datetime.datetime.now()
                + datetime.timedelta(0, 2 * len(self.throttle_data)),
            )
        )
        while True:
            while (
                self.throttle_data
                and self.throttle_data[0][1] < datetime.datetime.now()
            ):
                self.throttle_data = self.throttle_data[1:]
            if sum([d[0] for d in self.throttle_data]) < 150:
                return
            sleep(0.3)

    def say(self, message, target="#bots"):
        self.throttle(message)
        self.s.send("NOTICE %s :%s\r\n" % (target, message))

    def say_list(self, message, l):
        for target in l:
            self.say(message, target)

    def help(self, message):
        if self.help:
            self.say(message)

    def set_topic(self, topic):
        if self.topic != topic:
            self.s.send("TOPIC #bots :%s\r\n" % topic)

    #                                       ++++++++++ TOPIC VALUES ++++++++++

    def update_topic(self):
        if self.state == State.NoGame:
            self.set_topic(
                "Waiting list for next game: %s (%d)"
                % (self.format_list(self.waiting), len(self.waiting))
            )
        if self.state == State.Initialising:
            self.set_topic("New game. Villagers: %s" % self.format_list(self.alive))
        if self.state in [State.Night, State.WitchingHour, State.Stalking]:
            self.set_topic(
                "Night time. Wolves: %d. Villagers: %s"
                % (len(self.roles.wolves), self.format_list(self.alive))
            )
        if self.state in [State.Day, State.Discussion]:
            self.set_topic(
                "Day time. Wolves: %d. Villagers: %s"
                % (len(self.roles.wolves), self.format_list(self.alive))
            )
        if self.state == State.Voting:
            self.set_topic(
                "Voting to lynch %s. Wolves: %d. Villagers: %s"
                % (self.lynch, len(self.roles.wolves), self.format_list(self.alive))
            )

    def format_list(self, l, just=True):
        if len(l) == 0:
            return "nobody"
        if len(l) == 1:
            return "just " + l[0]
        return ", ".join([str(u) for u in l[:-1]]) + " and " + l[-1]

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
        self.alive.remove(user)
        roles = self.roles.kill(user)
        if "wolf" not in roles:
            self.ghosts.append(user)
        if msg and msg[:-1] != " ":
            msg += " "
        if "wolf" in roles:
            msg += str(Narrative.DeathReveal.wolf)
        if "witch" in roles:
            msg += str(Narrative.DeathReveal.witch)
        elif "inspector" in roles:
            msg += str(Narrative.DeathReveal.inspector)
        elif "hunter" in roles:
            msg += str(Narrative.DeathReveal.hunter)
        elif "wolf" not in roles:
            msg += str(Narrative.DeathReveal.innocent)
        if "cupid" in roles:
            msg += str(Narrative.DeathReveal.cupid)
        if "bacon" in roles:
            msg += str(Narrative.DeathReveal.bacon)
        if "cheese" in roles:
            msg += str(Narrative.DeathReveal.cheese)
        self.say(msg)
        self.BotCmd(["ISDEAD", str(user), "dead"])
        self.BotCmd(["DEATHREVEAL", str(user), roles])
        if "lover" in roles:
            self.roles.lovers, lover = [], self.roles.lovers[0]
            self.death(
                lover, str(Narrative.Death.lover) % {"victim": lover, "lover": user}
            )

    def hunter_death(self, callback):
        self.state = State.Revenge

        def revenge(target):
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
        self.BotCmd(["HUNTERFIRE"], str(self.roles.hunter))
        self.set_timer(60, callback)

    #                                       ++++++++++ GAME STAGES ++++++++++

    def game_begin(self):
        self.state = State.Initialising
        self.update_topic()

        self.roles = Roles()

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

        pool = self.alive[:]

        # +++++ wolves +++++
        self.roles.wolves = random.sample(self.alive, self.conf.wolves)
        for wolf in self.roles.wolves:
            self.say(
                "You are a werewolf. The wolves are: %s"
                % self.format_list(self.roles.wolves),
                wolf,
            )
            self.BotCmd(["YOURROLE", "wolf", self.roles.wolves], wolf)
            pool.remove(wolf)
            sleep(1)
        self.recruit = self.conf.recruiting

        innocents = pool[:]  # pool at this time contains all innocents

        # +++++ cheese +++++
        if True:
            self.roles.cheese = random.choice(self.alive)
            self.say(
                "You appear to own some cheese. It also appears to be of absolutely no use to you. ",
                self.roles.cheese,
            )
            self.BotCmd(["YOURROLE", "cheese"], self.roles.cheese)
            sleep(1)

        # +++++ bacon +++++
        if self.conf.bacon:
            self.roles.bacon = random.choice(innocents)
            self.say(
                "You have found a massive rasher of bacon in your larder. If wolves attack, you may use it to distract the wolves so that you can get away",
                self.roles.bacon,
            )
            self.BotCmd(["YOURROLE", "bacon"], self.roles.bacon)
            sleep(1)

        # +++++ cupid +++++
        if self.conf.cupid == 2:
            self.roles.cupid = random.choice(innocents)
            self.say(
                "As well as your main role, you will act as Cupid. Please use '!fire $nick1 $nick2' in the next 60 seconds to fire your bow and arrow and select these players as lovers.",
                self.roles.cupid,
            )
            self.BotCmd(["YOURROLE", "cupid"], self.roles.cupid)
            sleep(1)
        elif self.conf.cupid == 1:
            self.roles.cupid = random.choice(pool)
            pool.remove(self.roles.cupid)
            self.say(
                "Your role is Cupid. Please use '!fire $nick1 $nick2' in the next 60 seconds to fire your bow and arrow and select the lovers.",
                self.roles.cupid,
            )
            self.BotCmd(["YOURROLE", "cupid"], self.roles.cupid)
            sleep(1)

        # +++++ witch +++++
        if self.conf.witch:
            self.roles.witch = random.choice(pool)
            self.potions = ["beer", "cider"]
            pool.remove(self.roles.witch)
            self.say("Your role is the Witch.", self.roles.witch)
            self.BotCmd(["YOURROLE", "witch"], self.roles.witch)
            sleep(1)
        else:
            self.potions = []

        # +++++ hunter +++++
        if self.conf.hunter:
            self.roles.hunter = random.choice(pool)
            pool.remove(self.roles.hunter)
            self.say("Your role is the Hunter.", self.roles.hunter)
            self.BotCmd(["YOURROLE", "hunter"], self.roles.hunter)
            sleep(1)

        # +++++ inspector +++++
        if self.conf.inspector:
            self.roles.inspector = random.choice(pool)
            pool.remove(self.roles.inspector)
            self.say("Your role is the Inspector.", self.roles.inspector)
            self.BotCmd(["YOURROLE", "inspector"], self.roles.inspector)
            sleep(1)

        # +++++ villagers +++++
        for villager in pool:
            self.say("You are an ordinary villager.", villager)
            self.BotCmd(["YOURROLE", "villager"], villager)
            sleep(1)

        # +++++ auto lovers +++++
        if self.conf.cupid == 3:
            self.roles.lovers = random.sample(self.alive, 2)
            sleep(2)
            self.say(
                "You are one of the Lovers. You are madly in love with %s."
                % self.roles.lovers[0],
                self.roles.lovers[1],
            )
            self.say(
                "You are one of the Lovers. You are madly in love with %s."
                % self.roles.lovers[1],
                self.roles.lovers[0],
            )
            self.BotCmd(["YOULOVE", str(self.roles.lovers[0])], self.roles.lovers[1])
            self.BotCmd(["YOULOVE", str(self.roles.lovers[1])], self.roles.lovers[0])

        self.say("All roles have now been assigned. [%s]" % self.format_conf())
        self.BotCmd(["ROLESASSIGNED"])

        # timers for cupid or skip to game start
        if self.conf.cupid in [1, 2]:
            self.set_timer(60, self.game_night)
        else:
            self.game_night()

    def game_night(self):
        self.state = State.Night
        self.say(str(Narrative.Events.sunset))
        self.BotCmd(["NIGHTTIME"])
        self.stalked = False  # has the inspector acted yet
        self.votes = {}  # votes of the wolves
        self.beer = False
        self.cider = None
        if self.recruit:
            self.say_list(
                "You have 2 mins to make your attack. You may still recruit another Wolf with '!scratch'.",
                self.roles.wolves,
            )
            self.BotCmd_list(["CHOOSEVICTIM", True], self.roles.wolves)
        else:
            self.say_list(
                "You have 2 mins to make your attack. Don't forget you must not attack different targets.",
                self.roles.wolves,
            )
            self.BotCmd_list(["CHOOSEVICTIM", False], self.roles.wolves)
        self.set_timer(90, self.game_wolf_warning)
        self.update_topic()

    def game_wolf_warning(self):
        for wolf in self.roles.wolves:
            if wolf not in self.votes.keys():
                self.say("You have 30 seconds to decide on who to attack", wolf)
                self.BotCmd(["HURRYCHOOSE"], wolf)
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
                if target == None or target == vote[1]:
                    target = vote[1]
                    bite = True
                else:
                    fight = True
            elif vote[0] == "scratch":
                if target == None or target == vote[1]:
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

        if target and target == self.roles.bacon:
            self.roles.bacon = None
            self.say(str(Narrative.Notify.Target.baconEscape), target)
            self.say_list(
                str(Narrative.Notify.Wolves.baconEscape) % {"target": target},
                self.roles.wolves,
            )
            self.BotCmd(["NTBACONESCAPE"], target)
            self.BotCmd_list(["NWBACONESCAPE"], self.roles.wolves)
            target = None

        if target and random.uniform(0, 100) < self.conf.survival:
            self.say(str(Narrative.Notify.Target.survivalEscape), target)
            self.say_list(
                str(Narrative.Notify.Wolves.survivalEscape) % {"target": target},
                self.roles.wolves,
            )
            self.BotCmd(["NTSURVIVALESCAPE"], target)
            self.BotCmd_list(["NWSURVIVALESCAPE"], self.roles.wolves)
            target = None

        self.wolf_attack = (target, recruit)

        if target and not recruit and self.roles.witch:
            self.state = State.WitchingHour
            if target == self.roles.witch:
                if "beer" in self.potions:
                    self.say(
                        "You have a vision... the wolves are going to attack YOU! You have 2 mins to save yourself with '!beer'%s."
                        % (
                            ""
                            or "cider" in self.potions
                            and " or attack with '!cider $target'"
                        ),
                        self.roles.witch,
                    )
                    self.BotCmd(
                        ["WITCHSEE", "yourself", True, ("cider" in self.potions)],
                        self.roles.witch,
                    )
                elif "cider" in self.potions:
                    self.say(
                        "You have a vision... the wolves are going to attack YOU! You have 2 mins to save yourself but, OH NOES! You already used your beer! You have one last chance to strike back with '!cider $target'.",
                        self.roles.witch,
                    )
                    self.BotCmd(["WITCHSEE", "yourself", False, True], self.roles.witch)
                else:
                    self.say(
                        "You have a vision... the wolves are going to attack YOU! You have 2 mins to save yourself but, OH NOES! You already used your beer! Nothing to do but use '!sleep' and hope you don't wake up again to feel it. Sweet dreams!",
                        self.roles.witch,
                    )
                    self.BotCmd(
                        ["WITCHSEE", "yourself", False, False], self.roles.witch
                    )
                self.set_timer(90, self.game_witch_warning)
            else:
                if self.potions:
                    options = []
                    if "beer" in self.potions:
                        options.append("save them with '!beer'")
                    if "cider" in self.potions:
                        options.append("poison someone with '!cider $target'")
                    self.say(
                        "You have a vision... the wolves are going to attack %s! You have 2 mins to %s."
                        % (target, " or ".join(options)),
                        self.roles.witch,
                    )
                    self.BotCmd(
                        [
                            "WITCHSEE",
                            str(target),
                            ("beer" in self.potions),
                            ("cider" in self.potions),
                        ],
                        self.roles.witch,
                    )
                    self.set_timer(90, self.game_witch_warning)
                else:
                    self.say(
                        "You have a vision... the wolves are going to attack %s! There is nothing you can do though as you have used all your potions."
                        % target,
                        self.roles.witch,
                    )
                    self.BotCmd(
                        ["WITCHSEE", str(target), False, False], self.roles.witch
                    )
                    self.set_timer(0, self.game_wolf_kill)
        elif self.roles.witch:
            self.say(
                "You wake up in the night, but for once there are no bad dreams. It looks like the wolves won't be killing tonight. ",
                self.roles.witch,
            )
            if "cider" in self.potions:
                self.state = State.WitchingHour
                self.say(
                    "You still have cider you can use to poison somebody. You have 2 mins. ",
                    self.roles.witch,
                )
                self.BotCmd(
                    ["WITCHSEE", False, False, ("cider" in self.potions)],
                    self.roles.witch,
                )
                self.set_timer(90, self.game_witch_warning)
            else:
                self.set_timer(0, self.game_wolf_kill)
        else:
            self.set_timer(0, self.game_wolf_kill)

    def game_witch_warning(self):
        self.say("You have 30 seconds to decide on what to do.", self.roles.witch)
        self.BotCmd(["HURRYWITCH"], self.roles.witch)
        self.set_timer(30, self.game_witch_attack)

    def game_witch_attack(self):
        if self.cider:
            if self.cider == self.roles.hunter:
                self.say(str(Narrative.Notify.Hunter.witchAttack), self.roles.hunter)
                self.BotCmd(["NHWITCHATTACK"], self.roles.hunter)
                return self.hunter_death(self.game_wolf_kill)
            else:
                self.say(str(Narrative.Notify.Target.witchAttack), self.cider)
                self.BotCmd(["NTWITCHATTACK"], self.cider)
        return self.set_timer(0, self.game_wolf_kill)

    def game_wolf_kill(self):
        if self.wolf_attack[0] and not self.beer:
            if self.wolf_attack[0] == self.roles.hunter and not self.wolf_attack[1]:
                self.say(str(Narrative.Notify.Hunter.wolfAttack), self.roles.hunter)
                self.BotCmd(["NHWOLFATTACK"], self.roles.hunter)
                return self.hunter_death(self.game_inspector)
        self.set_timer(0, self.game_inspector)

    def game_inspector(self):
        self.state = State.Stalking
        if self.roles.inspector and not self.stalked:
            self.set_timer(60, self.game_dawn)
            self.say(
                "You have 60 seconds left to choose who to stalk.", self.roles.inspector
            )
            self.BotCmd(["CHOOSEINSPECT"], self.roles.inspector)
        else:
            self.set_timer(0, self.game_dawn)

    def game_dawn(self):
        self.state = State.Discussion
        self.say(str(Narrative.Events.sunrise))
        self.BotCmd(["WAKEUP"])
        if self.cider:
            self.death(
                self.cider, str(Narrative.Death.witchAttack) % {"victim": self.cider}
            )
        if not self.wolf_attack[0]:
            self.say(str(Narrative.Notify.All.wolfFail))
            self.BotCmd(["WOLFFAIL"])
        else:
            if self.wolf_attack[1]:
                self.say(
                    str(Narrative.Notify.Target.wolfScratch)
                    % {"wolves": self.format_list(self.roles.wolves)},
                    self.wolf_attack[0],
                )
                self.BotCmd(["NTWOLFSCRATCH", self.roles.wolves], self.wolf_attack[0])
                self.say(str(Narrative.Notify.All.wolfScratch))
                self.BotCmd(["WOLFSCRATCH"])
                self.roles.wolves.append(self.wolf_attack[0])
                self.recruit = False
            elif self.beer:
                self.say_list(
                    str(Narrative.Notify.Wolves.beerEscape)
                    % {"target": self.wolf_attack[0]},
                    self.roles.wolves,
                )
                self.BotCmd_list(["NWBEERESCAPE"], self.roles.wolves)
                if self.wolf_attack[0] != self.roles.witch:
                    self.say(
                        str(Narrative.Notify.Target.beerEscape), self.wolf_attack[0]
                    )
                    self.BotCmd(["NTBEERESCAPE"], self.wolf_attack[0])
            else:
                self.death(
                    self.wolf_attack[0],
                    str(Narrative.Death.wolfAttack) % {"victim": self.wolf_attack[0]},
                )
        self.lynchings = 1 + self.conf.doublelynch
        self.set_timer(30, self.game_proposals)
        self.update_topic()
        if not self.test_victory():
            self.say(str(Narrative.Events.mobForm))
            self.BotCmd(["MOBGATHERS"])

    def game_proposals(self):
        self.update_topic()
        self.say(str(Narrative.Events.mobPropose))
        self.BotCmd(["MOBANGRY"])
        self.state = State.Day
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
            self.BotCmd(["STALEMATE"])

    def game_nominate(self):
        self.state = State.Discussion
        self.nominee = self.proposals[self.proposer]
        self.proposals[self.proposer] = None
        self.say(str(Narrative.Events.mobChoose) % {"nominee": self.nominee})
        self.BotCmd(["SUSPECTED", self.nominee])
        self.set_timer(30, self.game_vote)

    def game_vote(self):
        self.state = State.Voting
        self.say(str(Narrative.Events.mobVote) % {"nominee": self.nominee})
        self.BotCmd(["VOTINGFOR", str(self.nominee)])
        self.votes = {}
        if len(self.alive) > 3:
            self.votes[self.proposer] = 1
            self.votes[self.seconder] = 1
        self.votes[self.nominee] = -1
        self.set_timer(90, self.game_vote_warning)

    def game_vote_warning(self):
        unvoted = list(set(self.alive) - set(self.votes.keys()))
        self.say(
            "Waiting for %s to vote. You have 30 seconds left. "
            % self.format_list(unvoted)
        )
        self.BotCmd_list(["VOTEHURRY"], unvoted)
        self.set_timer(30, self.game_count_votes)

    def game_count_votes(self):
        total = 0
        for player in self.alive:
            total += self.votes.get(player, -1)
        if total <= 0:
            self.say(str(Narrative.Events.mobFail) % {"nominee": self.nominee})
            self.BotCmd(["NOLYNCH"], self.nominee)
            self.BotCmd(["MOBANGRY"])
            self.state = State.Day
            self.last = datetime.datetime.now()
            return
        if self.nominee == self.roles.hunter:
            self.hunter_death(self.game_lynch)
        else:
            self.set_timer(0, self.game_lynch)

    def game_lynch(self):
        self.state = State.Discussion
        self.death(
            self.nominee, str(Narrative.Death.lynched) % {"victim": self.nominee}
        )
        self.lynchings -= 1
        if self.lynchings:
            self.say(str(Narrative.Events.mobContinue) % {"victim": self.nominee})
            self.BotCmd(["LYNCHED", self.nominee])
            self.set_timer(30, self.game_proposals)
        else:
            self.set_timer(30, self.game_night)
        self.test_victory()

    def game_pass(self):
        self.say(str(Narrative.Events.mobDismissed))
        self.BotCmd(["NIGHTTIME"])
        self.state = State.Discussion
        self.set_timer(0, self.game_night)

    def game_over(self):
        self.state = State.NoGame
        self.update_topic()

    #                                       ++++++++++ VICTORY CONDITIONS ++++++++++

    def test_victory(self):
        if self.alive == list(self.roles.lovers):
            return self.victory_lovers()
        if len(self.roles.wolves) == 0:
            return self.victory_innocent()
        if len(self.alive) <= len(self.roles.wolves) * 2 - ("cider" in self.potions):
            return self.victory_wolves()
        return False

    def victory_innocent(self):
        self.say(
            str(Narrative.Victory.innocent)
            % {"villagers": self.format_list(self.alive)}
        )
        self.BotCmd(["VICTORY", "villagers"])
        self.set_timer(10, self.game_over)
        self.cmd_botkill(self.mayorname)
        return True

    def victory_wolves(self):
        self.say(
            str(Narrative.Victory.wolves)
            % {"wolves": self.format_list(self.roles.wolves)}
        )
        self.BotCmd(["VICTORY", "wolves"])
        self.set_timer(10, self.game_over)
        self.cmd_botkill(self.mayorname)
        return True

    def victory_lovers(self):
        self.say(
            str(Narrative.Victory.lovers)
            % {"lover1": self.roles.lovers[0], "lover2": self.roles.lovers[1]}
        )
        self.BotCmd(["VICTORY", "lovers"])
        self.set_timer(10, self.game_over)
        self.cmd_botkill(self.mayorname)
        return True

    #                                       ++++++++++ GLOBAL COMMANDS ++++++++++

    def cmd_join(self, user):
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
        self.say(
            "The waiting list has been cleared by %s. The waiting list contained %s. Use '!join' to enter the new waiting list."
            % (user, self.format_list(self.waiting))
        )
        self.waiting = []
        self.update_topic()
        self.cmd_botkill(user)

    def cmd_kick(self, user, target):
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
        num = int(num)
        if self.state == State.NoGame:

            def start_test():
                if len(self.waiting) >= num:
                    self.cmd_start(user)

            self.start_test = start_test
            self.say("The game will start automatically after %d people join." % num)

    def cmd_start(self, user):
        self.start_test = lambda: None
        if self.state == State.NoGame:
            self.alive, self.ghosts, self.waiting = self.waiting, [], []
            self.say(
                "Game started by %s. Villagers are: %s. Please wait while roles are assigned."
                % (user, self.format_list(self.alive))
            )
            print "Sending gamestarted."
            self.BotCmd(["GAMESTARTED", self.alive])
            print "Finished sending gamestarted."
            self.game_begin()

    def cmd_stop(self, user):
        if self.state == State.NoGame:
            self.say("Game is not running.", user)
            return

        def stop_timer():
            self.state = State.NoGame
            self.alive = []
            self.say("Game stopped by %s." % user)
            self.cmd_botkill(user)
            self.update_topic()

        stop_timer.old_timer = self.timer
        stop_timer.isStopTimer = True
        self.set_timer(20, stop_timer)
        self.say(
            "Game will be stopped by %s in 20 seconds. Use '!abort' to override this and continue the game."
            % user
        )

    def cmd_abort(self, user):
        try:
            if self.timer[1].isStopTimer:
                self.timer = self.timer[1].old_timer
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
        if self.timer:
            self.say("A timer is running. Crash highly unlikely. ")
        elif self.state == State.NoGame:
            self.say("There isn't a game running ")
        elif self.state == State.Day:
            self.say("Waiting for people to propose a candidate for lynching. ")
        else:
            self.say("Something seems to have gone wrong.")
            self.say("This may be the time to use '!crash recovery'", user)

    def cmd_crash_fix(self, user, state=None):
        if self.timer:
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
        self.say("CopyOver initiated by %s." % user)
        raise self.CopyOver

    def cmd_reboot(self, user):
        self.say("ReBoot initiated by %s." % user)
        raise self.ReBoot

    #                                       ++++++++++ PUBLIC COMMANDS ++++++++++

    def cmd_say(self, user, msg, delay):
        def say():
            self.s.send("PRIVMSG #bots :%s\r\n" % msg)

        self.set_timer(delay, say)

    def cmd_choose(self, user, q):
        options = [o.strip() for o in re.compile(",| or ").split(q) if not o.isspace()]
        self.s.send("PRIVMSG #bots :%s\r\n" % random.choice(options))

    def cmd_suicide(self, user):
        if user not in self.alive:
            self.say("You are not alive", user)
            return
        self.death(user, str(Narrative.Death.suicide) % {"victim": user})
        self.update_topic()
        self.test_victory()

    def cmd_propose(self, user, target):
        if self.state == State.Voting:
            self.say("Please wait until voting is over.", user)
        if self.state == State.Discussion:
            self.say("Please wait. ", user)
        if self.state != State.Day:
            return
        if user not in self.alive:
            self.say("You are not alive", user)
            return
        if target not in self.alive:
            self.say("They are not alive", user)
            return
        if target == user:
            self.say("You cannot propose yourself.", user)
            return
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
        user = self.alive[self.alive.index(user)]
        self.proposals[user] = self.alive[self.alive.index(target)]
        self.say("%s has proposed %s." % (user, self.proposals[user]))

    def cmd_second(self, user, target):
        if self.state != State.Day:
            return
        if user not in self.alive:
            self.say("You are not alive", user)
            return
        if target not in self.alive:
            self.say("They are not alive", user)
            return
        if target == user:
            self.say("You cannot second yourself.", user)
            return
        if target not in self.proposals.values():
            self.say("They have not been proposed yet.", user)
            return
        user = self.alive[self.alive.index(user)]
        if self.proposals.get(user, None) == target:
            self.say("You may not both second and propose.", user)
            return
        self.proposer = [
            player
            for player in self.proposals.keys()
            if self.proposals[player] == target
        ][0]
        self.seconder = self.alive[self.alive.index(user)]
        self.say("%s has seconded %s's proposal." % (self.seconder, self.proposer))
        self.set_timer(0, self.game_nominate)

    def cmd_vote(self, user, vote):
        if self.state == State.Discussion:
            self.say("Please wait. ", user)
        if self.state != State.Voting:
            return
        if user not in self.alive:
            self.say("You are not alive", user)
            return
        user = self.alive[self.alive.index(user)]
        if vote.lower() in Vote.aye:
            self.votes[user] = 1
            self.say("You have voted 'aye'.", user)
        elif vote.lower() in Vote.abstain:
            self.votes[user] = 0
            self.say("You have voted 'abstain'.", user)
        elif vote.lower() in Vote.nay:
            self.votes[user] = -1
            self.say("You have voted 'nay'.", user)
        else:
            self.say("That is not a valid voting option.", user)
        if len(self.votes) == len(self.alive):
            self.set_timer(10, self.game_count_votes)

    def cmd_pass(self, user):
        if self.state != State.Day:
            return
        if user not in self.alive:
            self.say("You are not alive", user)
            return
        if len(self.alive) == len(self.roles.wolves) * 2:
            self.passCount += 1
            self.say("%s wishes not to lynch anybody" % user)
            if self.passCount == len(self.alive) / 2:
                self.set_timer(0, self.game_pass)
        else:
            self.say("There is no likelihood of a stalemate here")

    def cmd_botinit(self, user, bottype, botname):
        print "Botinit!"
        if len(self.sheepdata) < 10:
            try:
                if bottype == "sheep":
                    #                    self.sheepdata.append(Sheep3.SheepBot(botname))
                    self.sheepdata[botname] = Sheep3.SheepBot(
                        botname, votes=Vote, mayorname=self.mayorname
                    )
                else:
                    self.say("We don't have any " + bottype)
            except Exception:
                print "BotInit BadBot"
                self.say("Connection Error.")
        else:
            self.say("You can't have more than 10 sheep at once! That's a bad idea.")

    def cmd_botkill(self, user):
        print "Botkill"
        for bot in self.sheepdata.values():
            bot.s.send("QUIT\n")
        print self.sheepdata
        self.sheepdata = {}
        print self.sheepdata

    #                                       ++++++++++ PRIVATE COMMANDS ++++++++++

    def cmd_placeholder(self, user, **kwargs):
        self.say("Placeholder was used")

    def cmd_fire(self, user, loverA, loverB):
        if loverA == user or loverB == user:
            self.say("You may not fire an arrow at yourself", user)
        elif loverA not in self.alive:
            self.say("%s is not involved in the current game." % loverA, user)
        elif loverB not in self.alive:
            self.say("%s is not involved in the current game." % loverB, user)
        elif loverB == loverA:
            self.say("There must be two lovers, not one.", user)
        else:
            self.roles.lovers = (
                self.alive[self.alive.index(loverA)],
                self.alive[self.alive.index(loverB)],
            )
            self.say(
                "Hit by your arrows, %s and %s fall madly in love." % self.roles.lovers,
                user,
            )
            self.say(
                "You are one of the Lovers. You are madly in love with %s."
                % self.roles.lovers[0],
                self.roles.lovers[1],
            )
            self.say(
                "You are one of the Lovers. You are madly in love with %s."
                % self.roles.lovers[1],
                self.roles.lovers[0],
            )
            self.set_timer(1, self.game_night)

    def cmd_bite(self, user, target):
        if self.state != State.Night:
            return
        if user not in self.alive or user not in self.roles.wolves:
            self.say("You are not a Wolf.", user)
            return
        user = self.alive[self.alive.index(user)]
        if " " in target:
            self.votes[user] = "abstain"
            self.say("You have abstained from the attack.", user)
            for wolf in self.roles.wolves:
                if wolf != user:
                    self.say("%s does not care who is attacked." % user, wolf)
        else:
            if target not in self.alive:
                self.say("They are not alive.", user)
                return
            if target in self.roles.wolves:
                self.say("They are a Wolf.", user)
                return
            self.votes[user] = ("bite", self.alive[self.alive.index(target)])
            self.say("You have chosen to attack %s." % self.votes[user][1], user)
            for wolf in self.roles.wolves:
                if wolf != user:
                    self.say("%s plans to attack %s." % (user, target), wolf)
                    self.BotCmd(["OTHERWOLFPICKED", target], wolf)
        if len(self.votes) == len(self.roles.wolves):
            self.set_timer(10, self.game_wolf_attack)

    def cmd_recruit(self, user, target):
        if self.state != State.Night:
            return
        if user not in self.alive or user not in self.roles.wolves:
            self.say("You are not a Wolf.", user)
            return
        user = self.alive[self.alive.index(user)]
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
            if target not in self.alive:
                self.say("They are not alive.", user)
                return
            if target in self.roles.wolves:
                self.say("They are a Wolf.", user)
                return
            self.votes[user] = ("scratch", self.alive[self.alive.index(target)])
            self.say("You have chosen to recruit %s." % self.votes[user][1], user)
            for wolf in self.roles.wolves:
                if wolf != user:
                    self.say("%s plans to recruit %s." % (user, target), wolf)
        if len(self.votes) == len(self.roles.wolves):
            self.set_timer(10, self.game_wolf_attack)

    def cmd_beer(self, user):
        if self.state != State.WitchingHour:
            return
        if user not in self.alive or user != self.roles.witch:
            self.say("You are not the Witch.", user)
            return
        if "beer" not in self.potions:
            self.say("You don't have any beer left", user)
            return
        if not self.wolf_attack[0]:
            self.say("There is noone to save", user)
            return
        self.potions.remove("beer")
        self.beer = True
        self.say("You use your beer to avert the wolf attack.", user)
        if not self.potions:
            self.cmd_sleep(user)

    def cmd_cider(self, user, target):
        if self.state != State.WitchingHour:
            return
        if user not in self.alive or user != self.roles.witch:
            self.say("You are not the Witch.", user)
            return
        if "cider" not in self.potions:
            self.say("You don't have any cider left", user)
            return
        if target not in self.alive:
            self.say("They are not alive.", user)
            return
        if target == user:
            self.say("I wouldn't drink that foul stuff yourself!", user)
            return
        if target == self.wolf_attack[0] and not self.wolf_attack[1]:
            self.say(
                "The wolves are already after %s. Stop being silly." % target, user
            )
            return
        self.potions.remove("cider")
        self.cider = self.alive[self.alive.index(target)]
        self.say("You poison %s with a pint of deadly cider." % self.cider, user)
        if not self.potions:
            self.cmd_sleep(user)

    def cmd_sleep(self, user):
        if self.state != State.WitchingHour:
            return
        if user not in self.alive or user != self.roles.witch:
            self.say("You are not the Witch.", user)
            return
        self.say("You go back to sleep.", user)
        self.set_timer(0, self.game_witch_attack)

    def cmd_cuddle(self, user, target):
        if self.state not in [State.Night, State.WitchingHour, State.Stalking]:
            return
        if user not in self.alive:
            self.say("You are not alive", user)
            return
        if target == user:
            self.say("It just doesn't feel the same cuddling yourself...", user)
            return
        if target not in self.alive:
            self.say("They are not alive", user)
            return
        self.say("You cuddle up to %s." % target, user)
        self.say("%s cuddles up to you." % user, target)

    def cmd_spook(self, user, target):
        if self.state not in [State.Night, State.WitchingHour, State.Stalking]:
            return
        if user not in self.ghosts:
            self.say("They would see you", user)
            return
        if target not in self.alive:
            self.say("They are not alive", user)
            return
        self.say("You haunt %s in the night." % target, user)
        self.say("WooOOOOooooo! %s spooks you!" % user, target)

    def cmd_stalk(self, user, target):
        if self.state not in [State.Night, State.WitchingHour, State.Stalking]:
            return
        if user not in self.alive or user != self.roles.inspector:
            self.say("You are not the Inspector.", user)
            return
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
            self.BotCmd(["INSPECTED", target, "wolf"], user)
        elif target == self.roles.witch:
            self.say(str(Narrative.InspectorReveal.witch) % {"target": target}, user)
            self.BotCmd(["INSPECTED", target, "witch"], user)
        elif target == self.roles.hunter:
            self.say(str(Narrative.InspectorReveal.hunter) % {"target": target}, user)
            self.BotCmd(["INSPECTED", target, "hunter"], user)
        elif target == self.roles.cupid:
            self.say(str(Narrative.InspectorReveal.cupid) % {"target": target}, user)
            self.BotCmd(["INSPECTED", target, "cupid"], user)
        else:
            self.say(str(Narrative.InspectorReveal.innocent) % {"target": target}, user)
            self.BotCmd(["INSPECTED", target, "villager"], user)
        if self.state == State.Stalking:
            self.set_timer(5, self.game_dawn)

    def cmd_shoot(self, user, target):
        if self.state != State.Revenge:
            return
        if user not in self.alive or user != self.roles.hunter:
            self.say("You are not the Hunter.", user)
            return
        if target == user:
            self.say("There is no point in shooting yourself now.", user)
            return
        if target not in self.alive:
            self.say("They are not alive", user)
            return
        self.revenge(self.alive[self.alive.index(target)])

    def cmd_mod_login(self, user, pwd):
        if pwd == MOD_PWD:
            if self.mod:
                self.say("Mod has switched to %s" % user, self.mod)
            self.mod = user
            self.say("You are now the mod", user)

    def cmd_shell(self, user):
        if user == self.mod:
            if not SHELL:
                self.say("Shell is disabled.", user)
                return
            self.shell = ""
            self.say(
                "Shell mode started. Enter ! or ? on a new line to terminate, !! or ?? to terminate then repeat. Period to abort.",
                user,
            )

    #                                       ++++++++++ COMMAND LISTINGS ++++++++++

    cmds_global = [
        Command("^!join$", cmd_join),
        Command("^!leave$", cmd_leave),
        Command("^!clear$", cmd_clear),
        Command("^!kick (?P<target>\S+)$", cmd_kick),
        Command("^!start now$", cmd_start),
        Command("^!start$", cmd_placeholder),
        Command("^!start (?P<num>\d+)$", cmd_set_start),
        Command("^!stop$", cmd_stop),
        Command("^!abort$", cmd_abort),
        Command("^!conf print$", cmd_conf_print),
        Command("^!conf default$", cmd_conf_default),
        Command(
            "^!conf (?P<option>witch|hunter|inspector|bacon|recruiting|EG) (?P<value>yes|no)$",
            cmd_conf_set,
        ),
        Command("^!conf (?P<option>wolves) (?P<value>\d+)$", cmd_conf_set),
        Command(
            "^!conf (?P<option>cupid) (?P<value>no|yes|passive|auto)$", cmd_conf_set
        ),
        Command("^!conf (?P<option>survival) (?P<value>\d+)%$", cmd_conf_set),
        Command("^!ping$", cmd_crash_test),
        Command("^!crash recovery$", cmd_crash_fix),
        Command("^!crash recovery @State\.(?P<state>\w+)$", cmd_crash_fix),
        Command("^!copyover$", cmd_copyover),
        Command("^!reboot$", cmd_reboot),
        Command("^!say (?P<msg>.+) in (?P<delay>)s$", cmd_say),
        Command("^!bot killall$", cmd_botkill),
        Command("^!bot (?P<bottype>\S+) (?P<botname>\S+)$", cmd_botinit),
    ]

    cmds_private = [
        Command("^!fire (?P<loverA>\S+) (?P<loverB>\S+)$", cmd_fire),
        Command("^!(bite|kill|attack) (?P<target>\S+|don'?t care)$", cmd_bite),
        Command("^!(scratch|recruit) (?P<target>\S+)$", cmd_recruit),
        Command("^!stalk (?P<target>\S+)$", cmd_stalk),
        Command("^!cuddle (?P<target>\S+)$", cmd_cuddle),
        Command("^!spook (?P<target>\S+)$", cmd_spook),
        Command("^!beer$", cmd_beer),
        Command("^!cider (?P<target>\S+)$", cmd_cider),
        Command("^!sleep$", cmd_sleep),
        Command("^!shoot (?P<target>\S+)$", cmd_shoot),
        Command("^!mod (?P<pwd>\S+)$", cmd_mod_login),
        Command("^!shell$", cmd_shell),
    ]

    cmds_public = [
        Command("^!say (?P<msg>.+) in (?P<delay>\d+)s$", cmd_say),
        Command("^!choose (?P<q>.+?)\??$", cmd_choose),
        Command("^!suicide$", cmd_suicide),
        Command("^!propose (?P<target>\S+)$", cmd_propose),
        Command("^!second (?P<target>\S+)$", cmd_second),
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
    log_file = open("altfullmoon.log", "a")

    def log(msg):
        log_file.write(msg)
        log_file.flush()

    import crescentmoon as fullmoon

    class ReBoot(Exception):
        pass

    while True:
        try:
            reload(fullmoon)
            n = fullmoon.Narrator("MunicipalMayor", host="localhost", log=log)
            while True:
                try:
                    n()
                    #### ADDED SHEEP CODE ####
                    for name in n.sheepdata:
                        try:
                            n.sheepdata[name]()
                        except ZeroDivisionError:
                            n.sheepremove.append(name)
                        except n.sheepdata[name].BadBot, ex:
                            print "BadBot."
                            log(
                                "*** BADSHEEP: %s\n%s\n"
                                % (datetime.datetime.now(), traceback.format_exc())
                            )
                            n.sheepremove.append(name)
                    for name in n.sheepremove:
                        # n.sheepdata.remove(n.sheepdata[number])
                        print n.sheepdata
                        print n.sheepremove
                        print "\n"
                        n.sheepdata[name].s.send("QUIT\n")
                        del n.sheepdata[name]
                    n.sheepremove = []
                    #### END ADDED SHEEP CODE ####
                    sleep(0.2)
                except n.BadBot:
                    raise
                except n.ReBoot:
                    raise ReBoot
                except n.CopyOver:
                    log("*** COPYOVER: %s\n" % (datetime.datetime.now()))
                    d = n.__dict__
                    s = n.state.__name__
                    try:
                        reload(fullmoon)
                        n = fullmoon.Narrator()
                        n.__dict__ = d
                        n.state = getattr(fullmoon.State, s)
                    except Exception:
                        n.say("Could not copyover: new code sucks.")
                        log(
                            "*** 1D10T: %s\n%s\n"
                            % (datetime.datetime.now(), traceback.format_exc())
                        )
                except Exception:
                    n.say("An exception was thrown. Please check '!ping'.")
                    log(
                        "*** ERROR: %s\n%s\n"
                        % (datetime.datetime.now(), traceback.format_exc())
                    )
        except ReBoot:
            n.s.close()
            del n
            sleep(5)
            log("*** REBOOT: %s\n" % (datetime.datetime.now()))
        except Exception:
            log(
                "*** FAIL: %s\n%s\n" % (datetime.datetime.now(), traceback.format_exc())
            )
            sleep(20)
