# Arena slots: what may be overwritten (Matthew's list, kept current)
Updated 2026-11-14 (after handoff 019). Source of truth for which arena slots a downloaded arena may replace.
Full history and reasoning: `writeup/Arena_inventory.md` on branch `claude/slots50-gfx`.

## Rule
A downloaded arena only goes into a slot Matthew has named as unwanted, or one taken from the reserve list below,
in order. The slot a mod was made for is irrelevant. Nothing else gets replaced: not Money in the Bank '13 (for All
In), not the current SmackDown/Raw/NXT/Main Event/205 Live slots, not 312/316/402/105 (105 is the original
WrestleMania 31 and stays).

## Named unwanted slots (27) and what is in them now
| slot | was | now |
| --- | --- | --- |
| 4 | Payback '17 (select number 24: set it to make the slot selectable) | **free**, held for AEW x NJPW Forbidden Door (on hold) |
| 5 | Battleground '13 (select number 24) | Tokyo Dome |
| 53 | No Mercy '16 | SmackDown 21 |
| 96 | Great Balls of Fire | Raw |
| 107 | No Way Out '01 | AEW Dynamite '20 |
| 112 | Backlash '03 | AEW Revolution |
| 117 | Armageddon '02 | AEW Dark |
| 118 | Bad Blood '04 | AEW All Out |
| 119 | Vengeance '01 | AEW Double or Nothing |
| 123 | WrestleMania 13 | All In |
| 124 | In Your House '97 | Royal Rumble (Retro) |
| 125 | D-Generation X | WrestleMania 27 |
| 127 | Unforgiven '98 | NXT 2.0 |
| 128 | Over the Edge '98 | NXT White & Gold |
| 130 | Rock Bottom '98 | WrestleMania 35 |
| 132 | WrestleMania 15 | WrestleMania 38 |
| 133 | Backlash '00 | AEW Full Gear |
| 134 | King of the Ring '99 | Ring of Honor '05 |
| 135 | Fully Loaded '99 | Royal Rumble 2020 |
| 138 | Backlash '01 | ROH Death Before Dishonor |
| 139 | Armageddon '99 | AEW Rampage |
| 140 | Payback '13 | Survivor Series '26 (copy of stock SS '17 slot 11, Matthew's mat + logos; handoff 020) |
| 143 | Night of Champions '09 | SummerSlam '09 |
| 149 | Armageddon '03 | AEW Road Rager |
| 158 | Over the Limit '11 | AEW Dynamite '22 |
| 159 | Vengeance '11 | AEW Grand Slam |
| 160 | Payback '14 | SummerSlam '22 |

Not on the list but used for port stages that keep their own arena: 104 WrestleMania 29, 115 WrestleMania 32.

## Reserve list (Matthew agreed; use in this order when more slots are needed)
Already used from it: Battleground '15 (141) → Raw '20; Survivor Series '11 (153) → SmackDown '20.

**Still available:**
1. **One** of Survivor Series '12 / '13 (154, 145). Matthew keeps one of the Survivor Series slots: ask which before using either.
2. Hell in a Cell '10 (152)
3. Hell in a Cell '11 (144)
4. TLC '13 (146)
5. Elimination Chamber '13 (147)
6. Extreme Rules '11 (156)
7. St. Valentine's Day Massacre (131)
8. Judgment Day '04 (120)

**Keep (never use):** Capitol Punishment '11 (41), Money in the Bank '11 (148), Raw '11 (150), SmackDown '08 (157).

**Free right now without touching the reserve:** none. 4 (Payback '17) is held for Forbidden Door.

## Keeping this current
Whenever an arena goes into or comes out of a slot, update the tables here (on the arena branch and on `main`),
in the same commit as the install note.
