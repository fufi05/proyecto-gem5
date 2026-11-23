/* gemm_sve.c - C = A*B, orden i-k-j, SVE con predicados (vector-length agnostic) */
#include <arm_sve.h>
#include "bench.h"

int main(int argc,char **argv){
    if(argc<2){ fprintf(stderr,"uso: %s N\n",argv[0]); return 1; }
    int n=atoi(argv[1]);
    float *A=mat(n),*B=mat(n),*C=mat(n);
    init(A,n,3); init(B,n,5);
    for(int i=0;i<n*n;i++) C[i]=0.0f;

    ROI_BEGIN();
    for(int i=0;i<n;i++)
        for(int k=0;k<n;k++){
            svfloat32_t va=svdup_f32(A[i*n+k]);          /* a replicado en todos los carriles */
            for(int j=0;j<n;j+=(int)svcntw()){           /* svcntw() = floats por vector */
                svbool_t pg=svwhilelt_b32(j,n);          /* carriles activos; cubre el remanente */
                svfloat32_t c=svld1(pg,&C[i*n+j]);
                svfloat32_t b=svld1(pg,&B[k*n+j]);
                svst1(pg,&C[i*n+j],svmla_x(pg,c,b,va));  /* c + b*va fusionado */
            }
        }
    ROI_END();

    printf("checksum=%.6e\n",checksum(C,n));
    return 0;
}