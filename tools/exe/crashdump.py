"""Summarise a game minidump (CrashDump/2KMiniDump_*.dmp): exception, faulting address, exe return addresses on
the faulting thread's stack. pip install minidump. Usage: python3 crashdump.py <dmp>"""
import sys, struct, logging
logging.disable(logging.CRITICAL)
from minidump.minidumpfile import MinidumpFile
m = MinidumpFile.parse(sys.argv[1])
e = m.exception.exception_records[0]; r = e.ExceptionRecord
print(r.ExceptionCode, hex(r.ExceptionAddress), [hex(x) for x in r.ExceptionInformation[:r.NumberParameters]])
for t in m.threads.threads:
    if t.ThreadId != e.ThreadId: continue
    c = t.ContextObject
    print(' '.join(f'{k}={getattr(c, k):x}' for k in ['Rip', 'Rax', 'Rbx', 'Rcx', 'Rdx', 'Rsi', 'Rdi', 'Rbp', 'Rsp',
                                                       'R8', 'R9', 'R10', 'R11', 'R12', 'R13', 'R14', 'R15']))
    rr = m.get_reader().get_buffered_reader()
    try:
        rr.move(c.Rsp)
        for i in range(400):
            v = struct.unpack('<Q', rr.read(8))[0]
            if 0x140001000 <= v < 0x141e06000: print('  stack+%x' % (i * 8), hex(v))
    except Exception as x: print('  (stack read stopped:', x, ')')
