LDX #$01   ;X is $01
LDA #$aa   ;A is $aa
STA $a0,X ;Store the value of A at memory location $a1
ADC #01
INX        ;Increment X
STA $a0,X ;Store the value of A at memory location $a2
