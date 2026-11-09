# Executable analysis helpers (read-only)

Need `pip install --user capstone pefile` on the laptop shell; run with plain `python3` (not `-I`, which hides user
site-packages). Never name a script after a stdlib module (a `dis.py` broke capstone once).

| Script | Usage |
| --- | --- |
| `xref.py` | `xref.py <exe> <file-offset-hex>...` : RIP-relative code references to data at those file offsets |
| `disasm_at.py` | `disasm_at.py <exe> <VA-hex> <length-hex>` : disassembly with string annotations |
| `callers.py` | `callers.py <exe> <IAT-VA-hex>...` : call sites of imported functions |
| `cildump.py` | `cildump.py <assembly> <out.txt> [TypeFilter]` : CIL of every method with resolved tokens (cloud side; `pip install dnfile dncil`) |
