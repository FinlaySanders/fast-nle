#include <stdint.h>
#include <limits.h>
#include <stdio.h>
#include <assert.h>
int main(void) {
    uint32_t s=4717; long checks=0;
    int thresholds[]={50,75,85,95};
    for(int k=0;k<1000000;k++) {
        s=s*1664525u+1013904223u;int scaled=(int)s;
        s=s*1664525u+1013904223u;int cap=(s&INT_MAX)|1;
        if(k<65536) cap=k+1;
        for(int j=0;j<4;j++) {
            int t=thresholds[j];
            assert((scaled/cap<t)==((long long)scaled<(long long)t*cap));checks++;
            for(int delta=-2;delta<=2;delta++) {
                long long boundary=(long long)t*cap+delta;
                if(boundary>=INT_MIN&&boundary<=INT_MAX){int x=(int)boundary;assert((x/cap<t)==((long long)x<(long long)t*cap));checks++;}
            }
        }
    }
    printf("PASS %ld division/threshold comparisons\n",checks);
}
