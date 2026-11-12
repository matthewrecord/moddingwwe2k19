"""Match card fix for Dynamite '22 in slot 158: the slot's own layout (atb0) draws the foreground with slot 158's
quad (scale 0.5 x 1.0, size 908) made for its 1024x256 image; the mod's 2048x1024 foreground was made for the
205 Live layout (scale 0.5 x 0.5, size 454). Patch only those three foreground values in 158's layout to the 205 Live
ones (text positions stay slot 158's). Layout re-stored ZLIB-compressed (the game reads ZLIB, as the mod's own files)."""
import os, sys, zlib, struct, hashlib, json
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); sys.path.insert(0, os.path.join(H, '..', 'lib'))
import ooz, shdc2
from yukes import HSPC
M = '/mnt/user-data/uploads/common/WWE 2K19/_arena_work/in/mc/'; OUT = sys.argv[1]; rd = lambda p: open(p, 'rb').read()
def un(z):
    if z[:4] == b'OODL': us, cs = struct.unpack_from('<II', z, 16); return ooz.decompress(z[24:24 + cs], us)
    return zlib.decompress(z[16:])
def zl(u):
    c = zlib.compress(u, 9); return b'ZLIB' + struct.pack('<III', 0x1230, len(c), len(u)) + c
built = rd(OUT + '/../dyn22_cards/pac/menu/win/Assets/wwe19_anime/match_up/ltag_158_overlimit_2011_win.pac') if False else None
# start from the installed card build (slot 158 card + mod files 1, 3, 4)
tgt = rd(M + 'ltag_158_overlimit_2011_win.pac'); Ht = HSPC(tgt); src = shdc2.files(HSPC(rd(M + 'dyn_ltag_003.pac')).files[0]['data'])
own = shdc2.files(Ht.files[0]['data']); lay = bytearray(un(own[7])); ref = un(src[6])
for off in (0xf64, 0xff0, 0xff4, 0x16b0, 0x16b4):
    assert lay[off:off + 4] != ref[off:off + 4] or off in (0xff0, 0x16b0), hex(off)
    lay[off:off + 4] = ref[off:off + 4]
assert struct.unpack_from('<f', lay, 0xf64)[0] == 454.0 and struct.unpack_from('<2f', lay, 0xff0) == (0.5, 0.5) and struct.unpack_from('<2f', lay, 0x16b0) == (0.5, 0.5)
new = shdc2.build(Ht.files[0]['data'], {1: src[1], 3: src[3], 4: src[4], 7: zl(bytes(lay))})
assert un(shdc2.files(new)[7]) == bytes(lay)
data = Ht.replace(0, new); os.makedirs(OUT, exist_ok=True); open(OUT + '/ltag_158_overlimit_2011_win.pac', 'wb').write(data)
print(json.dumps({'size': len(data), 'md5': hashlib.md5(data).hexdigest()}))
