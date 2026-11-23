#include "bench.h"
int main(int argc,char**argv){
  int n=atoi(argv[1]);
  float *A=mat(n),*B=mat(n),*C=mat(n);
  init(A,n,3); init(B,n,5);
  for(int i=0;i<n*n;i++) C[i]=0;
  ROI_BEGIN();
  for(int i=0;i<n;i++) for(int k=0;k<n;k++){
    float a=A[i*n+k];
    for(int j=0;j<n;j++) C[i*n+j]+=a*B[k*n+j]; }
  ROI_END();
  printf("checksum=%.6e\n",checksum(C,n)); return 0; }
