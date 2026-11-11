"""Build the character id -> name table from CCT's own files (Matthew 2026-11-10: CCT keeps the original slots).
usage: python3 idnames.py "<pictures>/A - CCT" > idnames.tsv
data.xml: <item slotNumber slotId name slotType> = original game slots; replaced_data.xml: slotNumber -> current name.
Overflow slots 510-515 (ids 937-942) are appended from the slots installer state."""
import sys, xml.etree.ElementTree as ET
d = ET.parse(sys.argv[1] + '/data.xml').getroot(); r = ET.parse(sys.argv[1] + '/replaced_data.xml').getroot()
cur = {it.get('slotNumber'): it.get('name') for it in r.iter('item') if it.get('slotNumber')}
print('id\tslot\ttype\toriginal\tcurrent'); seen = set()
for it in d.iter('item'):
    s, i = it.get('slotNumber'), it.get('slotId')
    if i is None or (s, i) in seen: continue
    seen.add((s, i)); print(f"{i}\t{s}\t{it.get('slotType')}\t{it.get('name')}\t{cur.get(s, '')}")
for i, s, n in ((937, 510, 'Alex Shelley (Test Wrestler 1)'), (938, 511, 'Keith Lee (Test Wrestler 2)'),
                (939, 512, 'Angel Garza (Test Wrestler 3)'), (940, 513, 'Ace Austin (Test Wrestler 4)'),
                (941, 514, 'Darby Allin (Test Wrestler 5)'), (942, 515, 'Moose (Test Wrestler 6)')):
    print(f"{i}\t{s}\tOverflow\t\t{n}")
