"""
    Narrative aspects of fullmoon

    Author: Joe Taylor and Sandy Taylor
    Date: Ages ago. This was extracted from the original source
"""

import random

class Vote:
    aye = ['aye','yes','yup','lynch','kill','taken','squee','die']
    abstain = ['abstain','pass','none','meh','don\'t care']
    nay = ['nay','no','never','nope','save','release','spare','avast','noooo','nooo']

class RandLine( object ):
    def __init__( self, *lines ):
        self.lines = lines
    def __str__( self ):
        return random.choice( self.lines )

class Narrative:
    class RoleAssignment:
        wolf = "You are a werewolf. At night you may make attacks with your pack."
        villager = "You are an innocent villager. Your task is to try not to die."
        witch = "You are the witch. At night you find out who is to die, may save one life, and take one life."
        inspector = "You are the inspector. Each night you may inspect another player to find out their role."
        hunter = "You are the hunter. When you die, you may choose someone to kill somebody."
        cupid = "You are cupid. You must choose the lovers for the game immediately using the fire private command."
        vampire = "You are a vampire. At night you may make attacks."
        class Inventory:
            cheese = "You appear to own some cheese."
            bacon = "You have found a massive rasher of bacon in your larder. If wolves attack, you may use it to distract the wolves so that you can get away"
    class DeathReveal: # must end in a space! eg. ". "
        wolf = RandLine( "According to their will they were a werewolf all along. Hoorah! And how very helpful... ",
                         "The cellar full of all those missing body parts is a dead giveaway. They were a werewolf all along! ",
                         "With that much hair, they *must* have been a werewolf. ",
                         "Such sharp teeth they had. And such a long tail! ",
                         "They must have been a werewolf all along. Allergic reactions to silver don't usually extend to spontaneous combustion. ",
                         "What an interesting collection of dismembered body parts they have in their fridge. Only a WOLF would eat that! ",
                         )
        witch = RandLine( "The big bubbling pot of potion is a dead giveaway. ",
                          "They try to fly away on a broomstick, but luckily such a device doesn't actually have a means of propulsion. Anyway, THEY'RE A WITCH. ",
                          "Washing off their makeup reveals green skin (which all witches have). Witch! ",
                          "Only a witch would have needed all of those spellbooks. "
                          )
        inspector = RandLine( "Their collection of magnifying glasses is incredible. They must have been an inspector! ",
                              "A search of body reveals their official papers. They were an inspector all along. Oops, this might have been a *real* crime... ",
                              "After tearing apart the body, you find their diary. You read it and...oops, you just killed the inspector! "
                              )
        hunter = RandLine( "You've grossly underestimated them, as they bring out a gun and manage to fire a shot off before being ripped to pieces. ",
                           "Their cunningly hidden pump action shotgun claims a victim before they are overwhelmed! ",
                           "They are only brought down after a difficult chase, and shots are fired before the end! "
                           )
        cupid = RandLine( "They were cupid. Oops. ",
                          "A quick search of their house reveals a funny bow and list of happy couples. This person was cupid! ",
                          "Oh no, you just killed cupid! And weddings are so *fun* :( "
                          )
        villager = RandLine( "A search of their house and property doesn't find anything incriminating. It looks like they weren't a werewolf after all. ",
                             "The howling as night falls is undiminished. Looks like they weren't a werewolf after all. ",
                             "Their necklace is real silver, but they've often been seen wearing it. Not a werewolf! ",
                             "Their relatives testify that they were at home all night. Not a wolf after all! ",
                             "That wasn't a real tail, this is a furry, not a werewolf! "
                             )
        class Inventory:
            bacon = RandLine( "They have BACON. Everything else is put on hold to allow OM NOM NOM. ",
                              "OM NOM NOM. They has bacon. "
                              )
            cheese = RandLine( "For some reason they had cheese in their pockets. ",
                               "They were carrying around a small block of cheddar. ",
                               "It appears they have a pet cheese. ",
                               "Why are they carrying a block of cheese around? ",
                               "What a fine looking Bree they have stashed in their slacks. ",
                               "They are hiding a delightful blue cheese under their hat. ",
                              )
    class InspectorReveal:
        wolf = RandLine( "You follow %(target)s into the woods and see them change into a snarling beast! ", "You sneak into the house of your stalkee. There are bloody remains - clearly, you have stalked a wolf!", "There is wolf hair all over their house and the floor is littered with squeeky toys." )
        witch = RandLine( "You sneak into %(target)s's house and find all manner of potions and spell books. Witch!", "Sneaking into %(target)s's house, you find a number of jars of potion. They're a witch!", "You try to sneak into house, but are chased away by a flying broomstick. Never mind, this is probably enough evidence on its own" )
        hunter = RandLine( "You sneak into %(target)s's bedroom and find a shotgun hidden under the bed. Seems this person could be dangerous!", "They're always polishing their guns, and have more hidden than most of the villagers have realised. This person is the hunter!" )
        cupid = RandLine( "When searching through %(target)s's belongings, you find a bizarre bow and arrow. Weirdo - and probably also cupid.", "You check the records and observe an unusually high attendance at weddings. In fullmoonland this is enough to declare CUPID!" )
        innocent = RandLine( "You follow %(target)s home at night but they do nothing but have a cup of tea and head to bed.", "Nothing suspicious, this person seems perfectly normal.", "They seem to have a fetish for LaTeX, but other than that they are rather normal", "You find several animal costumes and a large collection of stuffed animals. This just makes them an innocent furry though. ")
    class Death: # must end in a space: eg ". "
        wolfAttack = RandLine( "%(victim)s is missing a head. "
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
        hunterAttack = RandLine( "%(hunter)s shoots %(victim)s dead with his hunting rifle. ", "%(hunter)s shoots %(victim)s dead with his shotgun. ", "%(hunter)s shoots %(victim)s dead with his bow and arrow. ", "%(hunter)s shoots %(victim)s dead with his pistol. ", "%(hunter)s shoots %(victim)s dead with his ion cannon. ", "%(hunter)s shoots %(victim)s dead with his phaser. ", "%(hunter)s shoots %(victim)s dead with his bolter. "  )
        witchAttack = RandLine( "%(victim)s was found frothing at the mouth. Looks like they angered a witch! ", "%(victim)s seems to have choked whilst drinking some bizarre blue liquid... " )
        lover = RandLine( "%(victim)s dies of a broken heart mouring their %(lover)s. ", "%(victim)s explodes at the very moment their %(lover)s dies. ", "%(victim)s has been reading too much Romeo and Juliet. They're found dead soon after their lover, %(lover)s, dies. " )
        lynched = RandLine( "%(victim)s becomes the target of the mob's hatred, and is torn apart! ", "The rabid mob attacks %(victim)s. ", "The lynch mob has spoken! %(victim)s is attacked and quickly beaten to death. ", "%(victim)s is taken up to the gallows and the whole village plays hangman. " )
        suicide = RandLine( "%(victim)s couldn't take the pressure. They hung themselves in their bedroom. ", "Fearing the worst, %(victim)s commits suicide with a paperclip and a small bottle of Salad Cream. ", "Unable to cope, %(victim)s took their own life with some duct tape and a pair of trousers. ", "Perhaps %(victim)s thought they could fly. Maybe they just couldn't take it anymore. Either way, %(victim)s probably shouldn't have jumped off that cliff if they wanted to live. " )
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
            baconEscape = RandLine( "You leap, the scent of blood in your OMGBACON. OM NOM NOM. Never mind.", "You can see %(target)s... so vunerable... so easy to kill... wait, is that BACON? OM NOM NOM! " )
            survivalEscape = "You crash through your %(target)s's window, entering their house, but in the melee they manage to escape."
            beerEscape = RandLine( "Your target was saved by the witch. Stupid witch :(", "That pesky witch saved %(target)s from your attack! " )
        class All:
            wolfScratch = "The wolves made quite a kerfuffle, but noone seems to have been harmed. Unless...could there be another wolf!?"
            wolfFail = RandLine( "The wolves have not attacked tonight. Hooray for beurocracy.",
                                 "Despite all that howling, nobody was killed at all. Hurrah!",
                                 "It seems the wolves lived off squirrels alone last night...", )
    class Events:
        sunset = RandLine( "Sunset has arrived again and the rising moon is greeted by howling. The villagers huddle in their houses, hoping desperately to be allowed to survive the night.", "With the setting of the sun, a chorus of howls greet the rising moon.", "The villages huddle in their houses, watching fearfully as the sun slips below the horizon" )
        sunrise = RandLine( "Sunrise.", "A cock crows.", "The sun rises, the sky turning a delightful blood red as it does.", "The villagers wake up to another sunny day." )
        mobForm = RandLine( "A fearful mob gathers, looking for someone to blame for the nightly howling. It's only a matter of time before they're angry and drunk enough to suggest a target. ",
                            "With the sun high in the sky, the villagers grow bold and prepare to fight back. Before long this could turn pretty nasty! ",
                            "Safe in the sunlight, the villagers leave the safety of their homes and gather in the market square. Full of fear and anger, they discuss who they suspect to be behind the killing. For now voices are raised but fists are not. For now anyway... " )
        mobPropose = "The mob's ferocity has reached killing point. They have begun to suggest targets for their anger!"
        mobChoose = "The mob is angry! %(nominee)s is suspected of being a werewolf! What do they have to say for themselves?"
        mobVote = "The time has come. Should %(nominee)s be lynched? You have up to 2 minutes to decide, cast your votes now!"
        mobFail = "A so %(nominee)s is spared by the mob, but the people are still scared and angry. Who will be suspected now?"
        mobDismissed = "Seeing the futility of their plans, the mob departs home hoping not to be the next victim."
        mobContinue = "Not satisfied with killing %(victim)s the mob remains, still bloodthirsty and willing to attack another victim. Other candidates may be suggested."
    class Victory:
        innocent = RandLine( "The innocents win (though only by tearing apart their friends until the ones that happen to be evil are dead)! Remaining villagers: %(villagers)s", "The peasants rejoice! The werewolves that plagued this village have been eradicated! Remaining villagers: %(villagers)s", "Xenophobia prevails! Long live the superior race! Remaining villagers: %(villagers)s"  )
        wolves = RandLine( "Wolves win! Remaining wolves: %(wolves)s", "Wolves win! Remaining wolves: %(wolves)s", "Wolves win! Remaining wolves: %(wolves)s. Help! I'm stuck in a #fullmoon writing factory!"  )
        lovers = RandLine( "Oh baby! %(lover1)s and %(lover2)s get it on! inclement: Bad Aule! But I won't delete this for some reason", "The two lovers remain, and live happily ever after. UNTIL NEXT TIME..." )

