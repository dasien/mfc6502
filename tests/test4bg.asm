; Test for absolute addressing

LDA #01 ; end of line comment
STA $c000
LDA #02
ADC $c000
