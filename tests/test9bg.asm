; Testing pesudo op codes, multiple pc resets and labels

.org $1000

LDA #01
STA $01
LDA TEST
STA $02
ADC $01
STA $03

.org $2000

		.byte	$0d, $0a, $00
		.ascii	"WWWWWWWWWWWWWWWWBBBBBBBBBBBBBBBBWWWWWWWWWWWWWWWW"
		.byte	"KQCCBBRRPPPPPPPPKQCCBBRRPPPPPPPP"
TEST:		.byte	$FF
