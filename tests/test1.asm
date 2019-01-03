; This is a comment
   ;So is this.

*=$2000
VAL1 = #10
VAL2 = $20
 LDY #$DF
 STY $2304
BEGIN LDY #0
 LDY $23
 LDA #$34
 ROL A
 TAX
 LDA #$90
 ADC #$10
 ORA #1
 PHA
 LDA #0
 PLA
 SEC
 SED
 LDA VAL1
 LDA VAL2
 BNE BEGIN
