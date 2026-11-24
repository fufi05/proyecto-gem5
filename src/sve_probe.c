/* Imprime el VL efectivo: sirve para verificar que sve_vl_se se aplica */
#include <arm_sve.h>
#include <stdio.h>
int main(void){
    printf("VL=%d bits, svcntw=%d\n",(int)svcntb()*8,(int)svcntw());
    return 0;
}
