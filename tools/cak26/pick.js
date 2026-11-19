// node pick.js <cak-reader.js> <2K26 dir> <outDir> <id,id,...>
// For each character id: every file under Characters/<id>_*/ ; one version per relative path:
// models/materials prefer bakedfile100 then 61,80,52,60,51 ; textures prefer 61,80,52,60,51,100 (1024 tier like earlier extractions)
const path=require('path'),fs=require('fs');
const R=require(process.argv[2]); const dir=process.argv[3]; const out=process.argv[4]; const ids=new Set(process.argv[5].split(','));
const order={model:['bakedfile100.cak','bakedfile61.cak','bakedfile80.cak','bakedfile52.cak','bakedfile60.cak','bakedfile51.cak'],
             tex:['bakedfile61.cak','bakedfile80.cak','bakedfile52.cak','bakedfile60.cak','bakedfile51.cak','bakedfile100.cak']};
const arcs=['bakedfile100.cak','bakedfile61.cak','bakedfile80.cak','bakedfile52.cak','bakedfile60.cak','bakedfile51.cak'];
const cand={};
for(const a of arcs){ const s=R.openArchive(path.join(dir,a),{});
  for(const f of s.files){ const m=/^Characters\/(\d+)_[^/]+\/(.+)$/.exec(f.name); if(!m||!ids.has(m[1])||!f.extractable) continue;
    (cand[f.name]=cand[f.name]||{})[a]={f,key:s.key>>>0,native:f.nativeName}; } }
fs.mkdirSync(out,{recursive:true}); const meta=[]; const fds={};
for(const [name,vs] of Object.entries(cand)){
  const kind=/\/Textures\/|\/CAS\//.test(name)&&/\.dds$/i.test(name)?'tex':'model';
  const a=order[kind].find(x=>vs[x]); if(!a) continue; const {f,key,native}=vs[a];
  fds[a]=fds[a]||fs.openSync(path.join(dir,a),'r');
  const buf=Buffer.alloc(f.storedSize); fs.readSync(fds[a],buf,0,f.storedSize,Number(f.offset));
  const fn=`${meta.length}.raw`; fs.writeFileSync(path.join(out,fn),buf);
  meta.push({arc:a,file:fn,name,native,key,offset:f.offset,storedSize:f.storedSize,expandedSize:f.expandedSize,compressed:f.compressed,protected:f.protected,chunks:f.chunks});
}
fs.writeFileSync(path.join(out,'meta.json'),JSON.stringify(meta)); console.log('files',meta.length);
