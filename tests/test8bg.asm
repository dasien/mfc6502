
  JSR init
  JSR loop
  JSR end

init:
  LDX #$00
  RTS

loop:
  INX
  CPX #$05
  BNE loop
  RTS

end:
  BRK

;Hexdigdata	.byte	"0123456789ABCDEF"
;banner		.ascii	"MicroChess (c) 1996-2002 Peter Jennings, peterj@benlo.com"
		.byte	$0d, $0a, $00
		.ascii	"WWWWWWWWWWWWWWWWBBBBBBBBBBBBBBBBWWWWWWWWWWWWWWWW"
		.byte	"KQCCBBRRPPPPPPPPKQCCBBRRPPPPPPPP"
		.byte	$00
;
; end of added code
;
; BLOCK DATA
		*= $1580
SETW		.byte 	$03, $04, $00, $07, $02, $05, $01, $06
        	.byte 	$10, $17, $11, $16, $12, $15, $14, $13
        	.byte 	$73, $74, $70, $77, $72, $75, $71, $76
	 	.byte	$60, $67, $61, $66, $62, $65, $64, $63

MOVEX   	.byte 	$00, $F0, $FF, $01, $10, $11, $0F, $EF, $F1
		.byte	$DF, $E1, $EE, $F2, $12, $0E, $1F, $21

POINTS  	.byte 	$0B, $0A, $06, $06, $04, $04, $04, $04
		.byte 	$02, $02, $02, $02, $02, $02, $02, $02

OPNING  	.byte 	$99, $25, $0B, $25, $01, $00, $33, $25
		.byte	$07, $36, $34, $0D, $34, $34, $0E, $52
        	.byte 	$25, $0D, $45, $35, $04, $55, $22, $06
		.byte	$43, $33, $0F, $CC
