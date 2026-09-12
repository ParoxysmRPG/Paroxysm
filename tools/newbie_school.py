"""Newbie school lessons supplied by the user, keyed by existing room vnum.

Keep paragraphs: these are tutorial text, not ordinary landscape descriptions.
Lighting, weather, exits, the ATM notice, and the pager are engine output.
"""

LESSONS = {
50: ('Movement and Helpfiles', """
Information about all the game's systems and lore is available in helpfiles.
You can also find it all on our website, http://paroxysm.net

To look at a helpfile type help (file name). If there is more than one
match you can use help 2.(file name) etc. You can use helpsearch (argument)
to look for any helpfile that contains that text.

You can also type commands to see a list of commands, and then use help
<commandname>.

To move about the game you'll use the cardinal directions, north, south,
east, west, northeast, southeast, northwest, southwest, up, down. Simply
type one on a new line and hit enter; you can also use the shortcuts, n, s,
e, w, ne, se, nw, sw, u, d.

In each room you'll see the available exits, in this room the only
available exit is to the north. Type n and hit enter when you are ready to
proceed.

Using the map command out of combat will list the game's maps, while if you
have a phone phone gps will show your current location inside the town. In
combat the map command shows you your immediate surroundings instead. If
you are in a property you can use map level to see a layout of the nearby area.

If you would rather not see descriptions automatically when you enter a room
you can use the brief command.
"""),
51: ('Communication', """
If at any time you have a problem or issue you can ask for help OOCly from
other players by typing newbie <message>, for example, newbie How do I set
my title? This will send a message to everyone on the game. You can also
write people notes OOCly, see help note for more information on how to do
that.

When in the game you can talk ICly with the say and whisper commands, you
can also use say to <person>, or whisper person to direct them to someone
in particular. The say command also accepts brackets to change the way in
which you speak. So you could use say (while laughing) That's a good one.
And it would appear as <Your name> says, while laughing, 'That's a good
one.'

The emote command allows you to convey in-game actions, for instance emote
laughs hard would appear like <Your name> laughs hard. Some simple emotes
are pre-written as socials, you can see a list of these by typing socials,
and use them by just typing their name and any possible targets afterwards.
The emote command can be used in a variety of ways, best explained in help
emoting.

To communicate with members of your faction, society or cult you can use
the fsay, ssay, or csay commands respectively.

Your character will also likely have a phone you can use to text or call
people, see help phone.
"""),
62: ('Concept and Character', """
The most fundamental part of your character is their archetype, there are
various supernatural and mundane character types, you can see them all in
help archetype.

Higher tier archetypes are more powerful but also inevitably more evil as in
this setting power always equals corruption. You can alter the tier of a
character by taking a positive or negative modifier. Note that you
generally cannot change your archetype once you leave newbie school, but
you can change your modifiers. You should look at help moral tier to
understand how to play your character's level of corruption.

Your character also came from somewhere, type history to enter an editor
and write your character's history. While you don't have to do this now, it
eventually will become compulsory to have a history if you keep playing.

Characters also require some secrets, you can use the secrets command to
write a description of yours. These are generally invisible to most other
players unless they have a specific legendary power.

You should also consider your character's drives, in Paroxysm drives are
either fears or ambitions. When your drives negatively impact your
character you have a chance to gain a bonus, see help cdrives for more
information.

Your character also likely has habits, use the habit command to set these
to represent the sorts of things your character does while 'offscreen'.

When in the game you also may wish to form coded relationships with others see
help relationships.

All of these fields can be seen by typing lookup self, and your basic
information can be seen with score.
"""),
59: ('Setting', """
Paroxysm is a modern, paranormal horror game set in the city of Gravesend, a
city that exists in the liminal space between worlds with an unclear
origin.

Paroxysm is a horror setting in which the foundational principle is that power
equals corruption. It is not just a saying that power corrupts in this
world, it is an unbreakable metaphysical law. All the most powerful
individuals are corrupt and so are most of the more powerful organizations.

The two primary themes of the game are Heroic Horror and Gothic Horror.

Heroic Horror is a term that refers to horror settings in which heroism is
still possible and, at least somewhat, effective. Unlike in some horror
genres where characters can only hope to survive their antagonists, in
heroic horror it is possible to defeat them and improve the state of the world.
It differs from standard heroic fantasy in that the victories characters
achieve are small scale and the overall state of the world is never
meaningfully moved to a just or orderly standard. In heroic fantasy
characters generally protect a basically just and moral world from being
corrupted, in heroic horror they are just trying to stop an immoral and
corrupt world from getting worse. The aesthetic of heroes in heroic horror
is much closer to resistance fighters than soldiers or police.

Gothic Horror is a term that refers to a genre of horror in which supernatural
elements function as metaphors for real world psychological or social conflicts.
It also has a heavy emphasis on conveying a general feeling of unease or
haunting.

In Paroxysm all the Demons, Gods, Fae etc used to be human, and many
supernatural elements function as exaggerations of real human traits or
what-ifs that can function as the basis for psychological exploration.

It's important to keep these themes in mind while playing, as all the
mechanics and lore are written with this in mind. Let them guide the
conflicts, choices, and consequences you explore through your character.
"""),
57: ('Training and Development', """
In order to customize and develop your character you can train various stats,
powers and disciplines.

Stats are bought with roleplay experience earned through roleplay of all types
and can vary between -1 and 5. You can use the command stats to see what
stats you have, and stats cost to see what ones you can buy. Each level of
a stat costs more to raise than the last, level 1 costs 10,000 RP xp, level
2, 20,000, 3, 30,000 and so on. So the total cost to raise a stat from 0 to
5 is 150,000 RP Exp. You begin the game with 150,000 newbie RP exp to set
up your character. To raise a stat just type train (stat name). You can do
this anywhere. If you make a mistake you can use negtrain (stat name) to
return the stat for a refund. But keep in mind that once you're out in the
game world this refund won't be the full cost of the stat. (See help
training methods for more information.)

Powers are the same as stats, but represent things related to the
supernatural world or abilities. Use the powers command or powers cost to
see them and train them in the same way.

Disciplines are a statistic that's used specifically in combat, they can be
ranged, melee, or defensive. Disciplines are raised with experience earned
by engaging in combat. They cost 200 experience times the level it's being
raised to. So to raise a discipline from 0 to 1 costs 200, from 1 to 2
costs 400, from 2 to 3 costs 600 etc. You start the game with 150,000
newbie combat exp to use to set up your character. To raise your
disciplines just use train (discipline name) if you make a mistake,
negtrain works for them the same as it does for other stats. You can use
the disciplines command to see your current disciplines, and use
disciplines cost to see the cost of raising any of them.
"""),
58: ('Descriptions', """
Characters should have a description. The simplest way to describe your
character is to simply type describe self. This will put you into an editor
where you can write a few lines about what your character looks like. If
you are feeling more adventurous however, Paroxysm has a much more detailed
description system you can make use of.

To do this type describe (location) to start writing a description of each part
of your body. Whatever parts of your body are exposed then will be shown
when people look at you, just remember to add a space or a newline at the
end or beginning of different parts that are displayed next to each other.
You can customize the order in which these parts appear with describe order
(location) (number), with lower numbers appearing first.

You can use ddesc create (keyword) (location) to create dynamic descriptions
for different body parts that you can switch on and off to update your
description.

You can also use detail (location) (over/under) to describe parts of your
character's body in greater depth. This won't be seen by anybody looking at
the character normally, but will be if they decide to look at that part of
you in greater detail with look (person) (location). Over details are
always displayed, while under details are displayed only when that part of
your body is exposed.

You use look (person) to see their description and clothing. You can use
glance instead to just see the parts of their appearance that have changed
since you last looked at them.

You can use glance (person) to see more basic information about them.

You can use qlook (person) for a quick overview of what they look like.
There is no need to describe every body part of your character, you should
aim for short, readable descriptions wherever possible.
"""),
52: ('Clothes and Tailoring', """
It's relatively important for your character to be dressed before you proceed
on grid. In this room you can buy clothing and customize it to suit you better.
Type list to see everything that's available, and then buy <number> to
purchase something. Once it is purchased you can wear it by simply typing
wear <object> or customize it with the customize command. For instance, buy
1, followed by wear shorts, would purchase and then wear a pair of white
cotton shorts.

You can look at help customize for a full list of options, but at a basic
level simply use customize <object> to enter an editor to change the details
of an item. The shortstring is what's used when the object is in messages,
longstring is what's seen when it's worn or on the ground, and names are
the words that can be used to target it.

When giving an item a wear string you can enclose it in brackets () to make it
show up in front of the item instead of behind.

It's important not to use the customize command to make something more
expensive than what is actually paid for it, in these cases you can use
customize cost to increase the cost appropriately. Over time you'll
assemble several outfits, which can be managed with the outfit command,
help outfit.

The wear command can take layers and locations as arguments, see help wear
for more information. You can also use the expose and unexpose commands to
manipulate worn clothes, help expose.

(This room is a universal stash, see help stash.)

A `wshower`x provides a place to wash before getting dressed.
"""),
53: ('Organizations', """
Much of what happens in Gravesend is a political struggle between different
organizations. While you don't have to join one of these organizations it
is generally harder to find things to do or purpose if you do not.

Factions are groups that are worldwide, player leaders of these groups have
an NPC boss.

Societies are groups that are more local, they might also have chapters
elsewhere but PC leaders do not really have a boss.

Cults are secretive player made groups that worship a spirit known as an
Eidolon, help Eidolon.

Characters can be in up to one of each type of these groups.

You use faction list to see a list of these groups, faction info (name) for
more information on each of them or faction join to join one. See help
society commands for all the commands.

Another important organization in the city is Windermere University, this
is a traditional university but also offers classes in the supernatural.
Students can also be in factions/societies but will be considered interns and
of lower rank. Being a student is often a good idea if you are a new
player. You can view help college for more information.

Additionally there are certain families which are particularly famous in the
supernatural world, known as famed families you can see a list of them in
help famed families. To join one of these families you just need to change
your surname to match them, you can then use the commands in help family.
While not a group PCs can join there are several other organizations that
players can work for while on plots and the like, you can see help
associations for a list of those.
"""),
54: ('Combat', """
There are three types of combat in Paroxysm. Fast combat is real time and what
will happen if you type attack (target).
Slow Combat is turn based and what will happen if you type spar (target).
RP Combat is semi-turn based and more of a coded support system for narrative
combat that is not very dependent on combat specific stats or abilities.
You can start a rpfight with rpfight (target).

The simplest move in combat is to simply type attack <target> this will pick
the best discipline for the job and use a basic attack against that opponent
with it. You can combine this with the move command that allows you to move
towards someone with move <target> charge, or away from them with move
<target> retreat and it will allow you to engage in simple easy fights. If
you want to get involved in more complex fights however, you will want to
set up and use custom attacks, with their own strings and special effects.

Help custom attacks for more information about them, you also might want to
view help move for more information on other types of battle movement. You
can find NPC enemies to fight and earn yourself combat exp by heading towards
the part of the city within the mist. You can use the weather command to
see where the center of the mist is, but it's not a good idea to go
straight to the center, head to a few blocks away and head slowly towards
it until you start to see mist.

You can use the speed command to alter your default combat speed when fighting
NPCs, see help speed.
"""),
61: ('Rules', """
Paroxysm is an IC enforced game. That means once you leave newbie school and
enter out into the game world you will be behaving as your character at all
times. Most of the rules are simply about ensuring everyone is playing ICly
and preventing common internet abuse. See help rules for a full list. You
should also familiarize yourself with our policies, please use help
policies.

If you need to contact the staff of the game for any reason, you should use
a petition, see help petition.
"""),
55: ('Roleplaying', """
Paroxysm is a roleplay enforced game, that means at all times while in the
game your character should act like a real person, a fictional character
with their own identity and actions, and not simply as a video game avatar.
You can think of it like writing an interactive story. If you've never
played a RP game before, look for someone to help steer you around the
curves.

Many people have different definitions of what makes good roleplay and good
roleplayers, but it mostly boils down simply to not being too selfish, and
giving some consideration to the enjoyment of others while writing a believable
and interesting character. If you'd like to read a long guide on
roleplaying, type help roleplaying guide.
"""),
56: ('Concept', """
This is your last chance to check over everything about your character to
ensure you are ready to go, while most aspects of your character can still
be changed once you enter the game a few cannot and others will have costs
applied.

Before entering the game please ensure your character is compliant with the
setting and lore, see help lore if you want to go over any of those files
again.

In particular only characters with the fleshformed modifier can have any
inhuman characteristics.

This is the last room of the newbie school, once you venture forth your
character will be real, be sure they're ready for that, good luck and I
hope you enjoy our game.

Type Enter to enter the game.
"""),
}

SHOWER = [('shower', 'Washable surfaces enclose the shower, with a drain beneath the washing space.')]


def description(vnum):
    """Preserve the supplied paragraph breaks and readable line lengths."""
    return LESSONS[vnum][1].strip() + '`x\n'


def places(vnum):
    return SHOWER if vnum == 52 else []
