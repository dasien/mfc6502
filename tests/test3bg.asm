; Perform simple addition and test transfers to from registers and stack.

LDA #01
PHA
LDA #02
PHA
PLA
TAX
PLA
TAY
TXA
STY $01
ADC $01