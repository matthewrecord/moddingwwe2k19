"""Dump CIL of every method in a .NET assembly with resolved member/string tokens (dnfile + dncil).
Usage: python3 cildump.py <assembly> <out.txt> [TypeSubstring]"""
import sys,dnfile
from dncil.cil.body import CilMethodBody
from dncil.cil.body.reader import CilMethodBodyReaderBase
from dncil.cil.error import MethodBodyFormatError
from dncil.clr.token import Token, StringToken, InvalidToken
class R(CilMethodBodyReaderBase):
    def __init__(s,pe,rva): s.pe=pe; s.off=pe.get_offset_from_rva(rva)
    def read(s,n): d=s.pe.get_data(s.pe.get_rva_from_offset(s.off),n); s.off+=n; return d
    def tell(s): return s.off
    def seek(s,o): s.off=o; return o
pe=dnfile.dnPE(sys.argv[1]); out=open(sys.argv[2],'w'); filt=sys.argv[3] if len(sys.argv)>3 else ''
md=pe.net.mdtables
def tokname(tok):
    try:
        if isinstance(tok,StringToken):
            return repr(pe.net.user_strings.get(tok.rid).value)
        t=tok.table; r=tok.rid
        tbl={0x0a:'MemberRef',0x06:'MethodDef',0x04:'Field',0x01:'TypeRef',0x02:'TypeDef',0x2b:'MethodSpec',0x1b:'TypeSpec'}.get(t)
        if not tbl: return str(tok)
        row=getattr(md,tbl)[r-1]
        if tbl=='MemberRef':
            cls=row.Class.row; cn=getattr(cls,'TypeName',None) or getattr(cls,'Name','?')
            return f"{getattr(cls,'TypeNamespace','')}.{cn}::{row.Name}"
        if tbl in('MethodDef','Field'): return f"{tbl}:{row.Name}"
        if tbl in('TypeRef','TypeDef'): return f"{row.TypeNamespace}.{row.TypeName}"
        return f"{tbl}#{r}"
    except Exception as e: return f"{tok}"
# map methods to types
owners={}
for ti,t in enumerate(md.TypeDef):
    for m in t.MethodList: owners[m.row_index]=f"{t.TypeNamespace}.{t.TypeName}"
for mi,m in enumerate(md.MethodDef,1):
    own=owners.get(mi,'?')
    if filt and filt not in own: continue
    if not m.Rva: continue
    try: body=CilMethodBody(R(pe,m.Rva))
    except Exception as e: out.write(f"\n## {own}::{m.Name} <unreadable {e}>\n"); continue
    out.write(f"\n## {own}::{m.Name}\n")
    for ins in body.instructions:
        op=ins.operand
        o=tokname(op) if isinstance(op,(Token,StringToken)) else op
        out.write(f"  IL_{ins.offset:04x} {ins.opcode.name} {o if o is not None else ''}\n")
print('done')
