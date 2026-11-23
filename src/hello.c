#include <arm_sve.h>
#include <stdio.h>
int main(){ printf("VL=%d bits, svcntw=%d\n",(int)svcntb()*8,(int)svcntw()); }
