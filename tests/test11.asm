rgConfig        =       $6000   ; write: D6=1 - NMI is off, D6=0 - NMI is on
rgStatus        =       $6000   ; read:  D6=0 - UART is busy
rgTxD           =       $5000   ; write: data to send via UART

vcNMI           =       $FFFA

Refresh         =       450     ; NMI rate in Hz

        ldx     #<NMI           ; installing the NMI vector
        ldy     #>NMI
        stx     vcNMI
        sty     vcNMI+1
        lda     #$40            ; on start NMI is off
        sta     InUse

Again
        lda     #0
        sta     Flag
        sta     Ticks           ; initializing counter
        sta     Ticks+1
        sta     Ticks+2
        sta     Ticks+3
        lda     #$FE            ; initializing NMI counter (zeropoint minus 2 ticks)
        sta     Timer
        lda     #$FF
        sta     Timer+1
        lda     InUse           ; turn on NMI
        and     #$BF
        sta     rgConfig
        sta     InUse

-       bit     Flag            ; waiting for zeropoint minus 1 tick
        bpl     -
        lda     #0
        sta     Flag

-       bit     Flag            ; waiting for true zeropoint
        bpl     -
        lda     #0
        sta     Flag

Main                            ; main counting cycle
;number of ticks per command   sum of ticks
;                          v   v
        lda     Ticks     ;4
        clc               ;2   6
        sed               ;2   8
        adc     #$53      ;2  10
        sta     Ticks     ;4  14
        lda     Ticks+1   ;4  18
        adc     #0        ;2  20
        sta     Ticks+1   ;4  24
        lda     Ticks+2   ;4  28
        adc     #0        ;2  30
        sta     Ticks+2   ;4  34
        lda     Ticks+3   ;4  38
        adc     #0        ;2  40
        sta     Ticks+3   ;4  44
        cld               ;2  46
        bit     Flag      ;4  50
        bpl     Main      ;3  53

        lda     #0        ;2
        sta     Flag      ;4   6
        lda     Ticks     ;4  10
        clc               ;2  12
        sed               ;2  14
        adc     #$95      ;2  16
        sta     Ticks     ;4  20
        lda     Ticks+1   ;4  24
        adc     #0        ;2  26
        sta     Ticks+1   ;4  30
        lda     Ticks+2   ;4  34
        adc     #0        ;2  36
        sta     Ticks+2   ;4  40
        lda     Ticks+3   ;4  44
        adc     #0        ;2  46
        sta     Ticks+3   ;4  50
        cld               ;2  52
        lda     Timer     ;4  56
        cmp     #<Refresh ;2  58
        bne     Main      ;3  61 + 34 (from NMI ISR) = 95
        lda     Timer+1   ; 4
        cmp     #>Refresh ; 2
        bne     Main      ; 3

        lda     InUse           ; turn off NMI
        ora     #$40
        sta     rgConfig
        sta     InUse

        ldx     #0              ; send first string to the host
-       lda     Mes1,x
        beq     +
        jsr     Send
        inx
        jmp     -

+       lda     Ticks+3
        pha
        lsr
        lsr
        lsr
        lsr
        beq     +               ; delete non-significant zero (clock < 10MHz)
        jsr     PrintDigit
+       pla
        and     #15
        jsr     PrintDigit
        lda     #"."            ; decimal point
        jsr     Send
        lda     Ticks+2
        jsr     PrintTwoDigits
        lda     Ticks+1
        jsr     PrintTwoDigits
        lda     Ticks
        jsr     PrintTwoDigits

        ldx     #0              ; send second string to the host
-       lda     Mes2,x
        beq     +
        jsr     Send
        inx
        jmp     -
+       jmp     Again           ; repeat process

PrintTwoDigits
        pha
        lsr
        lsr
        lsr
        lsr
        jsr     PrintDigit
        pla
        and     #15
        jsr     PrintDigit
        rts

PrintDigit
        ora     #$30
        jsr     Send
        rts

Send
        bit     rgStatus
        bvc     Send
        sta     rgTxD
        rts

Mes1
        .db     13
        .tx     "Current clock frequency is "
        .db     0

Mes2
        .tx     " MHz"
        .db     0

Ticks   .br     4,0
Timer   .br     2,0
InUse   .db     0
Flag    .db     0

NMI                        ;6
        pha                ;3   9
        inc     Timer      ;6  15
        bne     +          ;3  18
        inc     Timer+1    ; 5
+       lda     #$80       ;2  20
        sta     Flag       ;4  24
        pla                ;4  28
        rti                ;6  34