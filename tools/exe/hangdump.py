"""Per-thread summary of a FULL process dump (Task Manager 'Create dump file' on a frozen game): where each thread waits,
with module+offset return addresses found on its stack. pip install minidump.  python3 hangdump.py <dmp>
2026-11-14: used on the belt-session freeze (all 144 threads in waits = deadlock)."""
import sys, struct, logging
logging.disable(logging.CRITICAL)
from minidump.minidumpfile import MinidumpFile
m = MinidumpFile.parse(sys.argv[1])
mods = sorted((x.baseaddress, x.endaddress, x.name.split('\\\\')[-1]) for x in m.modules.modules)
def where(a):
    for b, e, n in mods:
        if b <= a < e: return '%s+%x' % (n, a - b)
    return hex(a)
rr = m.get_reader().get_buffered_reader()
for t in m.threads.threads:
    c = t.ContextObject
    if c is None: continue
    rets = []
    try:
        rr.move(c.Rsp)
        for i in range(600):
            w = where(struct.unpack('<Q', rr.read(8))[0])
            if not w.startswith('0x') and len(rets) < 10: rets.append(w)
    except Exception: pass
    print(t.ThreadId, 'rip', where(c.Rip), '|', ' '.join(rets))
