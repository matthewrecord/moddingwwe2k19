"""Refit a match-card foreground made for the 205 Live layout (2048x1024, content in the bottom half) to a slot whose
layout draws its foreground as a wide strip (slot 158: 1024x256 texture shown at about 6.7:1 on screen, measured
from Matthew's screenshot). Crop the content to the strip's on-screen aspect (keeping the bottom, where the
'UP NEXT' box is) and encode BC7 at the slot's own texture size."""
import sys, zlib, struct, numpy as np, texture2ddecoder, etcpak
from PIL import Image
def decode(dds):
    h, w = struct.unpack_from('<II', dds, 12); img = texture2ddecoder.decode_bc7(dds[148:148 + w * h], w, h)
    return Image.frombytes('RGBA', (w, h), img, 'raw', 'BGRA')
def fit(src_dds, tmpl_dds, aspect):
    im = decode(src_dds); W, H = im.size; ch = round(W / aspect)
    crop = im.crop((0, H - ch, W, H))
    th, tw = struct.unpack_from('<II', tmpl_dds, 12)
    out = crop.resize((tw, th), Image.LANCZOS)
    rgba = np.array(out.convert('RGBA')); bgra = rgba.copy()  # etcpak takes RGBA order
    data = etcpak.compress_bc7(bgra.tobytes(), tw, th)
    assert len(data) == tw * th, (len(data), tw * th)
    return tmpl_dds[:148] + data, out
