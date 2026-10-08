#include <assert.h>
#include "hack.h"
static struct obj* expected(struct obj* prev,int lx,int hx,int ly,int hy) {
 struct obj* o=prev?prev->nobj:fobj;
 for(;o;o=o->nobj)if(o->ox>=lx && o->ox<=hx && o->oy>=ly && o->oy<=hy)return o;
 return NULL;
}
int main(void) {
 struct obj* nodes=(struct obj*)calloc(2501,sizeof(struct obj));
 nh_cur=(struct nh_ctx*)calloc(1,sizeof(struct nh_ctx));assert(nodes && nh_cur);
 long checks=0, spatial_checks=0;
 for(int trial=0;trial<2400;trial++) {
  int sizes[]={0,1,63,64,65,127,128,129,1024,2048,2500}; int n=sizes[(trial/2)%11];
  for(int i=0;i<n;i++){nodes[i].nobj=i+1<n?&nodes[i+1]:NULL;nodes[i].ox=trial%2 ? (schar)((i*17+trial)%256-128) : 1+(i*17+trial)%79;nodes[i].oy=trial%2 ? (schar)((i*13+trial)%256-128) : (i*13+trial)%21;}
  fobj=n?nodes:NULL;nh_fobj_invalidate();struct nh_fobj_cursor cursor;struct obj* prev=NULL;
  int lx=trial%2 ? -128 : 1,hx=trial%2 ? 127 : 79,ly=trial%2 ? -128 : 0,hy=trial%2 ? 127 : 20;
  for(int k=0;;k++) {
   struct obj* want=expected(prev,lx,hx,ly,hy);
   struct obj* got=nh_fobj_next(&cursor,prev,lx,hx,ly,hy);assert(got==want);checks++;if(nh_fobj_spatial && !cursor.fallback) spatial_checks++;
   if(!got)break;prev=got;
   if(k%17==3){lx=-200+(trial+k)%73;hx=200-(trial+k)%71;ly=-200+(trial+k)%79;hy=200-(trial+k)%67;}
   if(k%17==7){lx=-128;hx=127;ly=-128;hy=127;}
   if(k%17==12){lx=1+(trial+k)%10;hx=79-(trial+k)%7;ly=(trial+k)%3;hy=20-(trial+k)%4;}
   if(trial%5==0 && k==5 && prev->nobj){nh_fobj_invalidate();prev->nobj=prev->nobj->nobj;}
   if(trial%5==0 && k==8){nh_fobj_invalidate();nodes[2500].nobj=prev->nobj;nodes[2500].ox=lx;nodes[2500].oy=ly;prev->nobj=&nodes[2500];}
  }
 }
 fobj=NULL;nh_fobj_invalidate();struct nh_fobj_cursor cursor;assert(!nh_fobj_next(&cursor,NULL,1,79,0,20));
 free(nodes);free(nh_cur);nh_cur=NULL;
 assert(spatial_checks>10000); printf("PASS %ld spatial and %ld total cursor comparisons: ordered bounds, shrink, mutation continuation, empty and overflow\n",spatial_checks,checks);
 return 0;
}
