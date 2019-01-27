; code for an interrupt serviced data buffer. similar code is used to drive the XY
; stepper motors on a plotter with new position information every 5mS and also to
; allow pen up/down movement time of 70mS

                *= $B000        ; set origin (buffer and variables must be in RAM)

Buffer				; 256 byte buffer (must start at page edge)
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	.word	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000

BRindx				; buffer read index
	.byte $00

BWindx				; buffer write index
	.byte $00

Sendf                           ; am sending flag
	.byte $00

WByte                           ; temp store for the byte to be sent
	.byte $00

; write the data to the buffer a byte at a time and increment the pointer.
; the routine is called with the byte to write in A. If the interrupt device
; is idle when this routine is called it will wake it up by doing a BRK
; before it exits
;
; destroys the Y register

		*= $C000	; set origin (can be ROM or RAM)

Incwritb
	STA	WByte		; save byte to write
	LDA	BRindx		; get read index
        SEC                     ; set carry for subtract
	SBC	BWindx		; subtract write index
	BEQ	Dowrite		; if equal then buffer empty so do write
	CMP	#$02		; need at least n+1 bytes to avoid rollover
	BCC	Incwritb	; loop if no space


                                ; construct and write data to buffer
Dowrite
	LDY	BWindx		; get write index
	LDA	WByte		; get byte to write
	STA	Buffer,Y	; save it
        INY                     ; increment index to next byte
	STY	BWindx		; save new write index byte

; now see if the interrupt service routine is already running or if it's idle

	LDA	Sendf		; get the sending flag
	BNE	Doingit		; skip call if running
        BRK                     ; software call to interrupt routine
        NOP                     ; need this as return from BRK is +1 byte!
        CLI                     ; enable the interrupts

Doingit
	RTS

; this is the interrupt service routine. takes a byte a time from the buffer
; and does some thing with it. also sets up the device(s) for the next interrupt

; no registers altered

BuffIRQ
        PHA                     ; save A
        TXA                     ; copy X
        PHA                     ; save X
        TYA                     ; copy Y
        PHA                     ; save Y

; insert code here to ensure this is the interrupt you want. if it isn't then just exit
; quietly via ResExit the end of the routine

Getnext
	JSR	Increadb	; increment pointer and read byte from buffer
	BCS	ExitIRQ		; branch if no byte to do

; here would be the guts of the routine such as sending the byte to the ACIA or a
; printer port or some other byte device. it will also ensure the device is set to
; generate an interrupt when it's completed it's task

	LDA	#$FF		; set byte
	STA	Sendf		; set sending flag
	JMP	ResExit		; restore the registers & exit

                                ; all done so clear the flag restore the regs & exit
ExitIRQ
        LDA     #$00            ; clear byte
	STA	Sendf		; clear sending flag

ResExit
        PLA                     ; pull Y
        TAY                     ; restore it
        PLA                     ; pull X
        TAX                     ; restore it
        PLA                     ; restore A
        RTI                     ; this was an interrupt service so exit properly

; get byte from the buffer and increment the pointer. If the buffer is empty then
; exit with the carry flag set else exit with carry clear and the byte in A

Increadb
	LDY	BRindx		; get buffer read index
	CPY	BWindx		; compare write index
	BEQ	NOktoread	; branch if empty (= sets carry)
	LDA	Buffer,Y	; get byte from buffer
        INY                     ; increment pointer
	STY	BRindx		; save buffer read index
        CLC                     ; clear not ok flag

NOktoread
	RTS