import sys,os,shutil,subprocess,json,tables
from epk import payload,build_single
R=sys.argv[1]+'/'; rd=lambda p:open(p,'rb').read()
def st(src,S,T,out):
    o=subprocess.run(['python3','reslot_stage.py',src,str(S),str(T),out],capture_output=True,text=True); print(S,'->',T,[l for l in o.stdout.split('\n') if 'SKIP' in l],o.stderr[-300:])
def put(out,rel,data):
    p=out+rel; os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'wb').write(data)
A={t:'../in/b2_%d/'%t for t in (139,149,159,112,133,107)}
for t in A: shutil.rmtree(A[t],ignore_errors=True)
st(R+"AEW Rampage '21",116,139,A[139]); st(R+"AEW Road Rager '21",120,149,A[149])
put(A[139],'pac/arena/barricade/arbarricade00025.pac',rd(R+"AEW Rampage '21/pac/arena/barricade/arbarricade00025.pac"))
put(A[139],'pac/arena/turnbuckle/arturnbuckle00016.pac',rd(R+"AEW Rampage '21/pac/arena/turnbuckle/arturnbuckle00016.pac"))
put(A[149],'pac/arena/barricade/arbarricade00029.pac',rd(R+"AEW Road Rager '21/pac/arena/barricade/arbarricade00029.pac"))
put(A[149],'pac/arena/turnbuckle/arturnbuckle00020.pac',rd(R+"AEW Road Rager '21/pac/arena/turnbuckle/arturnbuckle00020.pac"))
st(R+"AEW - Grand Slam New",3,159,A[159]); st(R+"AEW Grand Slam - Switched to Slot 163",163,159,A[159]); st(R+"AEW Copyright, Locators, ETC",3,159,A[159])
put(A[159],'pac/arena/stadium/arstadium00074.pac',rd(R+"AEW - Grand Slam New/pac/arena/stadium/arstadium00074.pac"))
st(R+"AEW Revolution",10,112,A[112]); st('../in/src_m10',10,112,A[112])
put(A[112],'pac/arena/barricade/arbarricade00066.pac',rd(R+"AEW Revolution/pac/arena/barricade/arbarricade00066.pac"))
put(A[112],'pac/arena/turnbuckle/arturnbuckle00051.pac',rd(R+"AEW Revolution/pac/arena/turnbuckle/arturnbuckle00051.pac"))
FG=R+"AEW Full Gear Arena (Switched to the Fastlane Slot)/"
st(FG,14,133,A[133]); st('../in/src_m14',14,133,A[133])
put(A[133],'pac/arena/barricade/arbarricade00055.pac',rd(FG+"arena/barricade/arbarricade00055.pac"))
put(A[133],'pac/arena/turnbuckle/arturnbuckle00067.pac',rd(FG+"arena/turnbuckle/arturnbuckle00067.pac"))
st(R+"AEW Dynamite GFX/Easy Install",3,107,A[107]); st('../in/src_m3',3,107,A[107])
put(A[107],'pac/arena/barricade/arbarricade00030.pac',build_single(b'EPAC',b'SGSN',b'BR30',payload(rd(R+"AEW Dynamite 20/pac/arena/barricade/arbarricade00022.pac")),b'\0'*0x800))
for t in A: print(t,sorted(os.path.relpath(os.path.join(r,f),A[t]).replace('pac/menu/win/Assets/wwe19_singleread/','') for r,_,fs in os.walk(A[t]) for f in fs if '/mov/' in os.path.join(r,f) or 'entrance' in r))
