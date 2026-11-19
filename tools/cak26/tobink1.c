// tobink1.exe [folder] : convert every .mp4 under folder to Bink 1 (.bk2 extension) using RAD binkc.exe
#include <windows.h>
#include <stdio.h>
#include <string.h>
static char dir[MAX_PATH], tmp[MAX_PATH], logp[MAX_PATH]; static FILE*lg; static int ok=0,fail=0;
static const char*RAD="C:\\Program Files (x86)\\RADVideo\\binkc.exe";
static int run(const char*cmd,int hide,PROCESS_INFORMATION*out){STARTUPINFOA si={sizeof si};PROCESS_INFORMATION pi;
 if(hide){si.dwFlags=STARTF_USESHOWWINDOW;si.wShowWindow=SW_HIDE;}
 char c[4096];strcpy(c,cmd); if(!CreateProcessA(0,c,0,0,0,hide?CREATE_NO_WINDOW:0,0,0,&si,&pi))return -1;
 if(out){*out=pi;return 0;} WaitForSingleObject(pi.hProcess,INFINITE);DWORD rc;GetExitCodeProcess(pi.hProcess,&rc);CloseHandle(pi.hProcess);CloseHandle(pi.hThread);return rc;}
static long long fsize(const char*p){WIN32_FILE_ATTRIBUTE_DATA a;if(!GetFileAttributesExA(p,GetFileExInfoStandard,&a))return -1;return ((long long)a.nFileSizeHigh<<32)|a.nFileSizeLow;}
static void cleardir(const char*d){char p[MAX_PATH];WIN32_FIND_DATAA f;sprintf(p,"%s\\*",d);HANDLE h=FindFirstFileA(p,&f);if(h!=INVALID_HANDLE_VALUE){do{if(f.cFileName[0]=='.')continue;sprintf(p,"%s\\%s",d,f.cFileName);DeleteFileA(p);}while(FindNextFileA(h,&f));FindClose(h);}}
static int one(const char*mp4){
 char out[MAX_PATH];strcpy(out,mp4);strcpy(strrchr(out,'.'),".bk2"); if(fsize(out)>=0)return 1;
 printf("%s\n",mp4); fflush(stdout);
 char fr[MAX_PATH],bik[MAX_PATH],lst[MAX_PATH],cmd[4096]; sprintf(fr,"%s\\frames",tmp); CreateDirectoryA(fr,0); cleardir(fr);
 sprintf(bik,"%s\\out.bik",tmp); sprintf(lst,"%s\\frames.lst",tmp); DeleteFileA(bik);
 sprintf(cmd,"\"%s\\ffmpeg.exe\" -v error -y -i \"%s\" -an -start_number 0 -pix_fmt bgr24 \"%s\\f%%04d.bmp\"",dir,mp4,fr);
 if(run(cmd,1,0)!=0){fprintf(lg,"FAILED ffmpeg %s\n",mp4);return 0;}
 FILE*l=fopen(lst,"w");int n=0;for(;;n++){char b[MAX_PATH];sprintf(b,"%s\\f%04d.bmp",fr,n);if(fsize(b)<0)break;fprintf(l,"%s\n",b);}fclose(l);
 sprintf(cmd,"\"%s\" \"%s\" \"%s\" /F29.97 /O",RAD,lst,bik); PROCESS_INFORMATION pi;
 if(run(cmd,0,&pi)!=0){fprintf(lg,"FAILED start binkc %s\n",mp4);return 0;}
 long long last=-2;int stable=0;
 for(;;){ if(WaitForSingleObject(pi.hProcess,1500)==WAIT_OBJECT_0)break; long long s=fsize(bik);
   if(s>0&&s==last){if(++stable>=2){Sleep(1000);TerminateProcess(pi.hProcess,0);break;}}else stable=0; last=s;}
 CloseHandle(pi.hProcess);CloseHandle(pi.hThread); Sleep(300);
 // verify frame count in header
 FILE*b=fopen(bik,"rb");unsigned h[3]={0};if(b){fread(h,4,3,b);fclose(b);}
 if(!b||h[2]!=(unsigned)n){fprintf(lg,"FAILED %s (frames %u of %d)\n",mp4,h[2],n);return 0;}
 if(!MoveFileExA(bik,out,MOVEFILE_REPLACE_EXISTING|MOVEFILE_COPY_ALLOWED)){fprintf(lg,"FAILED move %s\n",mp4);return 0;}
 fprintf(lg,"OK %s (%d frames)\n",mp4,n);fflush(lg);return 1;}
static int walk(const char*d){char p[MAX_PATH];WIN32_FIND_DATAA f;sprintf(p,"%s\\*",d);HANDLE h=FindFirstFileA(p,&f);if(h==INVALID_HANDLE_VALUE)return 1;
 do{if(f.cFileName[0]=='.')continue;sprintf(p,"%s\\%s",d,f.cFileName);
  if(f.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY){if(!walk(p)){FindClose(h);return 0;}}
  else{size_t L=strlen(p);if(L>4&&!_stricmp(p+L-4,".mp4")){if(one(p))ok++;else{fail++;FindClose(h);return 0;}}}}while(FindNextFileA(h,&f));FindClose(h);return 1;}
int main(int argc,char**argv){GetModuleFileNameA(0,dir,MAX_PATH);*strrchr(dir,'\\')=0;
 char root[MAX_PATH]; if(argc>1)strcpy(root,argv[1]); else sprintf(root,"%s\\..\\..\\Videos (2K19 Derived)",dir);
 GetTempPathA(MAX_PATH,tmp);sprintf(tmp+strlen(tmp),"bk1_%lu",GetCurrentProcessId());CreateDirectoryA(tmp,0);
 sprintf(logp,"%s\\tobink1_%lu.log",dir,GetCurrentProcessId());lg=fopen(logp,"w");
 printf("Converting .mp4 under %s\n",root); int r=walk(root); char fr[MAX_PATH];sprintf(fr,"%s\\frames",tmp);cleardir(fr);
 fprintf(lg,"%s: %d ok, %d failed\n",r?"finished":"stopped",ok,fail);fclose(lg);
 printf("\n%s: %d converted, %d failed. Log: %s\nPress Enter to close.",r?"ALL DONE":"STOPPED after a failure",ok,fail,logp);getchar();return 0;}
