class Token(object):

    # Token types.
    EOL = 0
    EOF = 1
    INTEGER = 2
    STRING = 3
    OPCODE = 4
    PSEUDO = 5
    LABEL = 6
    ACC = 7
    XREG = 8
    YREG = 9
    HASH = 10
    COMMA = 11
    DOT = 12
    COLON = 13
    EQUAL = 14
    STAR = 15
    PLUS = 16
    MINUS = 17
    LPAREN = 18
    RPAREN = 19
    LANGLE = 20
    RANGLE = 21
    LSQUARE = 22
    RSQUARE = 23

    def __init__(self, type= None, value=None):

        # Member variables.
        self.type = type
        self.value = value