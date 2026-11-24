#pragma once
#include <stdio.h>
#include <stdlib.h>
#ifdef GEM5
#include <gem5/m5ops.h>
#define ROI_BEGIN() m5_reset_stats(0,0)
#define ROI_END()   m5_dump_stats(0,0)
#else                       /* qemu: las m5ops darían SIGILL */
#define ROI_BEGIN()
#define ROI_END()
#endif
static float *mat(int n){
 return aligned_alloc(64,(size_t)n*n*sizeof(float));
 } /* n múltiplo de 16 */
static void init(float*a,int n,int s){
 for(int i=0;i<n*n;i++) a[i]=((i*s)%13-6)*0.25f;
 }
static double checksum(const float*c,int n){
 double s=0; for(int i=0;i<n*n;i++) s+=c[i]; return s; }
