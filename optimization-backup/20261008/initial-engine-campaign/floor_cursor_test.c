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
 long checks=0;
 for(int trial=0;trial<300;trial++) {
  int n=trial%3==0?2500:trial%3==1?2048:81;
  for(int i=0;i<n;i++){nodes[i].nobj=i+1<n?&nodes[i+1]:NULL;nodes[i].ox=1+(i*17+trial)%79;nodes[i].oy=(i*13+trial)%21;}
  fobj=nodes;nh_fobj_invalidate();struct nh_fobj_cursor cursor;struct obj* prev=NULL;
  int lx=1,hx=79,ly=0,hy=20;
  for(int k=0;;k++) {
   struct obj* want=expected(prev,lx,hx,ly,hy);
   struct obj* got=nh_fobj_next(&cursor,prev,lx,hx,ly,hy);assert(got==want);checks++;
   if(!got)break;prev=got;
   if(k==3){lx+=trial%10;hx-=trial%7;ly+=trial%3;hy-=trial%4;}
   if(k==5 && prev->nobj){nh_fobj_invalidate();prev->nobj=prev->nobj->nobj;}
   if(k==8){nh_fobj_invalidate();nodes[2500].nobj=prev->nobj;nodes[2500].ox=lx;nodes[2500].oy=ly;prev->nobj=&nodes[2500];}
  }
 }
 fobj=NULL;nh_fobj_invalidate();struct nh_fobj_cursor cursor;assert(!nh_fobj_next(&cursor,NULL,1,79,0,20));
 free(nodes);free(nh_cur);nh_cur=NULL;
 printf("PASS %ld cursor comparisons: ordered bounds, shrink, mutation continuation, empty and overflow\n",checks);
 return 0;
}
