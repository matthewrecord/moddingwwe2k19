// Decode a Bink 2 file with RAD's bink2w64.dll and pipe frames into ffmpeg.
// usage: bk2dec.exe in.bk2 out.mp4 [surface] [frames]
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
typedef struct { unsigned W,H,Frames,FrameNum,LastFrameNum,Rate,RateDiv; } BH;
typedef BH* (__stdcall *tOpen)(const char*,unsigned);
typedef int (__stdcall *tDo)(BH*);
typedef void (__stdcall *tNext)(BH*);
typedef int (__stdcall *tCopy)(BH*,void*,unsigned,unsigned,unsigned,unsigned,unsigned);
typedef void (__stdcall *tClose)(BH*);
typedef const char* (__stdcall *tErr)(void);
int main(int argc,char**argv){
  if(argc<3){fprintf(stderr,"usage: bk2dec in.bk2 out.mp4 [surface] [frames]\n");return 1;}
  char dll[MAX_PATH]; GetModuleFileNameA(NULL,dll,MAX_PATH); char*s=strrchr(dll,'\\'); strcpy(s+1,"bink2w64.dll");
  HMODULE m=LoadLibraryA(dll); if(!m){fprintf(stderr,"cannot load %s\n",dll);return 2;}
  tOpen O=(tOpen)GetProcAddress(m,"BinkOpen"); tDo D=(tDo)GetProcAddress(m,"BinkDoFrame"); tNext N=(tNext)GetProcAddress(m,"BinkNextFrame");
  tCopy C=(tCopy)GetProcAddress(m,"BinkCopyToBuffer"); tClose X=(tClose)GetProcAddress(m,"BinkClose"); tErr E=(tErr)GetProcAddress(m,"BinkGetError");
  unsigned surf=argc>3?strtoul(argv[3],0,0):3; unsigned lim=argc>4?atoi(argv[4]):0;
  BH*b=O(argv[1],0); if(!b){fprintf(stderr,"BinkOpen failed: %s\n",E?E():"?");return 3;}
  unsigned w=b->W,h=b->H,n=b->Frames; if(lim&&lim<n)n=lim;
  fprintf(stderr,"%s: %ux%u %u frames %u/%u fps\n",argv[1],w,h,b->Frames,b->Rate,b->RateDiv);
  char cmd[4096]; snprintf(cmd,sizeof cmd,"\"\"%sffmpeg.exe\" -hide_banner -loglevel error -y -f rawvideo -pix_fmt bgra -s %ux%u -framerate %u/%u -i - -c:v libx264 -preset veryfast -crf 14 -pix_fmt yuv420p \"%s\"\"",
    "",w,h,b->Rate,b->RateDiv?b->RateDiv:1,argv[2]);
  { char d2[MAX_PATH]; strcpy(d2,dll); *strrchr(d2,'\\')=0; char c2[4600]; snprintf(c2,sizeof c2,"\"\"%s\\ffmpeg.exe\" -hide_banner -loglevel error -y -f rawvideo -pix_fmt bgra -s %ux%u -framerate %u/%u -i - -c:v libx264 -preset veryfast -crf 14 -pix_fmt yuv420p \"%s\"\"",d2,w,h,b->Rate,b->RateDiv?b->RateDiv:1,argv[2]); strcpy(cmd,c2);}
  FILE*p=_popen(cmd,"wb"); if(!p){fprintf(stderr,"cannot start ffmpeg\n");return 4;}
  size_t pitch=(size_t)w*4; unsigned char*buf=malloc(pitch*h);
  for(unsigned i=0;i<n;i++){ D(b); memset(buf,0,pitch*h); C(b,buf,(unsigned)pitch,h,0,0,surf|0x80000000u);
    for(size_t k=0;k<pitch*h;k+=4) buf[k+3]=255; fwrite(buf,1,pitch*h,p); if(i+1<n) N(b); }
  X(b); int r=_pclose(p); fprintf(stderr,"done rc=%d\n",r); return r?5:0;
}
