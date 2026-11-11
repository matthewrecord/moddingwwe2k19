"""List Universe match results from a decoded Universe blob (UNVSBODY0001.bin from savedecode.py).
usage: python3 matches.py UNVSBODY0001.bin idnames.tsv
Participant entry (16 bytes, found 2026-11-10 against Matthew's card): u16 id, u16 role, u16 id, u16 role, u16 result,
u16 0, u16 0xff00, u16 0. role low byte = side (0/1), high byte: 0 wrestler, 1 (0x100) = side B, 2 = manager
(0x002 side A manager, 0x102 side B manager). result: 0x1FF win+pinfall, 0x3FF win, 0x2FF lost (pinned), 0x4FF lost.
Match header: entries start 0x28 bytes after a u16 'title|kind' word: high byte = championship id (0xFF none, e.g.
0x96 = 150 = Matthew's AEW US Championship), low byte = kind/position; the u16 before the ffff ffff pair (-0x30) is
the Universe day when set. Every card seems stored twice (copy +0x3C00); duplicates are dropped by content."""
import csv, struct, sys
RES = {0x1FF: 'won (pin)', 0x3FF: 'won', 0x2FF: 'lost (pinned)', 0x4FF: 'lost'}
def parse(b):
  def entry(o):
      i, r, i2, r2, res = struct.unpack_from('<5H', b, o)
      return (i, r, res) if i == i2 and r == r2 and i < 1024 and res in RES else None
  seen, out, o = set(), [], 0
  while o < len(b) - 16:
      e = entry(o)
      if not e: o += 2; continue
      group = []
      while o < len(b) - 16 and (e := entry(o)): group.append(e); o += 16
      start = o - 16 * len(group)
      tk = struct.unpack_from('<H', b, start - 0x28)[0]; day = struct.unpack_from('<H', b, start - 0x30)[0]
      key = (tk, tuple(group))
      if key in seen: continue
      seen.add(key)
      wr = [g for g in group if g[1] & 0xFF != 2]
      if len(wr) < 2 or not any(g[2] in (0x1FF, 0x3FF) for g in wr) or not any(g[2] in (0x2FF, 0x4FF) for g in wr):
          continue                                     # not a match card (needs a winner and a loser)
      title = None if tk >> 8 == 0xFF else tk >> 8
      out.append((start, day, title, tk & 0xFF, group))
  return out

if __name__ == '__main__':
  b = open(sys.argv[1], 'rb').read()
  nm = {int(r['id']): (r['current'] or r['original']) for r in csv.DictReader(open(sys.argv[2]), delimiter='\t')} if len(sys.argv) > 2 else {}
  out = parse(b)
  for start, day, title, kind, group in out:
    sides = {}
    for i, r, res in group:
        who = nm.get(i, str(i)) + (' (manager)' if r & 0xFF == 2 else '')
        sides.setdefault(r >> 8 if r & 0xFF != 2 else r >> 8, []).append(f'{who} {RES[res]}')
    print(f'{start:#x} day {day} {"title " + str(title) if title is not None else "non-title"} kind {kind}: ' +
          ' | '.join('side %d: %s' % (k, ', '.join(v)) for k, v in sorted(sides.items())))
