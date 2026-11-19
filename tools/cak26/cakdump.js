// node cakdump.js <cak-reader.js> <2K26 dir> <outDir> '{"bakedfile02.cak":["*"],"bakedfile01.cak":["MoveData/AttackData.jsfb"]}'
const path=require('path'),fs=require('fs');
const R=require(process.argv[2]); const dir=process.argv[3]; const outDir=process.argv[4]; const sel=JSON.parse(process.argv[5]);
fs.mkdirSync(outDir,{recursive:true}); const meta=[];
for(const [arc,pats] of Object.entries(sel)){
  const s=R.openArchive(path.join(dir,arc),{}); const fd=fs.openSync(path.join(dir,arc),'r');
  for(const f of s.files){
    if(!f.extractable) continue;
    if(!pats.some(p=>p==='*'||f.name.includes(p))) continue;
    const buf=Buffer.alloc(f.storedSize); fs.readSync(fd,buf,0,f.storedSize,Number(f.offset));
    const fn=`${arc.replace('.cak','')}_${f.id}.raw`; fs.writeFileSync(path.join(outDir,fn),buf);
    meta.push({arc,file:fn,name:f.name,type:f.type,key:s.key>>>0,offset:f.offset,storedSize:f.storedSize,expandedSize:f.expandedSize,compressed:f.compressed,protected:f.protected,chunks:f.chunks});
  }
  fs.closeSync(fd);
}
fs.writeFileSync(path.join(outDir,'meta.json'),JSON.stringify(meta));
console.log('dumped',meta.length);
