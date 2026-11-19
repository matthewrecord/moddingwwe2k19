// node cakindex.js <cak-reader.js> <2K26 dir> <out.tsv>   (archive, name, type, stored, expanded, offset, extractable, named, compressed)
const path=require('path'),fs=require('fs');
const R=require(process.argv[2]); const dir=process.argv[3]; const out=fs.createWriteStream(process.argv[4]);
for(const a of fs.readdirSync(dir).filter(f=>/\.cak$/i.test(f)).sort()){
  try{ const s=R.openArchive(path.join(dir,a),{});
    for(const f of s.files) out.write([a,f.name,f.type,f.storedSize,f.expandedSize,f.offset,f.extractable?1:0,f.nameResolved?1:0,f.compressed?1:0].join('\t')+'\n');
    console.log(a,s.files.length);
  }catch(e){ console.log(a,'ERR',e.message); }
}
out.end();
