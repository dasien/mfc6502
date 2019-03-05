from mfcbase import MFCBase
from lexertoken import LexerToken


class Assembler(MFCBase):

    def __init__(self, infile, outfile, startaddr=None, includecounter=False):

        # Labels are supported.
        self.__labels = dict()

        # So are pseudo-ops.
        self.__pesudoops = dict()

        # Pointer to current character in file.
        self.__linepos = 0

        # Temp string storage.
        self.__currentstring = ''

        # Used to backup one token.
        self.__oldtoken = None

        # Two pass assembler.
        self.__pass = 0

        # Default program counter.
        self.pc = 0x0000

        # Superclass init.
        super(Assembler, self).__init__(infile, outfile, startaddr, includecounter)

        # Load opcode & pseudo op tables.
        self.loadopcodes()
        self.loadpesudoops()

    def assemble(self):

        # This is a temp counter to hold starting pc position.
        tmppc = self.pc

        # Parse the input file.
        self.parse()

        # Perform two pass assembly.
        for self.__pass in (1, 2):

            # Reset the program counter.
            self.pc = tmppc

            # Loop through each line.
            for sourceline in super(Assembler, self).sourcelines:

                # Reset line position counter.
                self.__linepos = 0

                # Get the current token.
                token = self.gettoken(sourceline)

                # Loop through each character in the line.
                while token.type != LexerToken.EOL:

                    # print the token type.
                    print("Found token type: %s with value %s" % (token.type, token.value))

                    # Check to see if we have an opcode.
                    if token.type == LexerToken.OPCODE:

                        # Calculate the operand for this opcode.
                        opcodehex, operand, length = self.getoperand(sourceline, token.value, tmppc)

                        # Write the data to the file.
                        self.writelinedata(opcodehex, operand)

                        # Increment the program counter based on operand.
                        self.pc += length

                        # Get the next token
                        token = self.gettoken(sourceline)

                    # Check to see if we have a pseudo-op.
                    elif token.type == LexerToken.PSEUDO:

                        # Get the method associated with this pseudo-op.
                        pseudo = self.__pesudoops[token.value]

                        # Execute the instruction.
                        pseudo(sourceline)

                        # Get the next token
                        token = self.gettoken(sourceline)

                    # Check to see if we have label.
                    elif token.type == LexerToken.LABEL:

                        # Get the text of the label.
                        label = self.__currentstring

                        # Get the next token.
                        token = self.gettoken(sourceline)

                        # Check to see if this is assignment.
                        if token.type == LexerToken.EQUAL:

                            # Fetch the value.
                            value = self.parseterm(sourceline, 0, 65535)

                            # Check to see if we found a value.
                            if value is not None:

                                # Assign the value to the label.
                                self.__labels[label] = value

                            else:

                                # Assign the current address to label.
                                self.__labels[label] = self.pc

                        # This is a label with nothing after it on the line
                        elif token.type == LexerToken.COLON:

                            # Assign the current address to label.
                            self.__labels[label] = self.pc

                            # Get the next token
                            token = self.gettoken(sourceline)

                        # This is a label with a pseudo-op after it.
                        elif token.type == LexerToken.PSEUDO:

                            # Assign the current address to label.
                            self.__labels[label] = self.pc

                        # This is just a label with no colon.
                        elif token.type == LexerToken.EOL:

                            # Assign the current address to label.
                            self.__labels[label] = self.pc

                    # This should be the address into which the program is loaded.
                    elif token == LexerToken.ASTERISK:

                        # Get the next token.
                        token = self.gettoken(sourceline)

                        # Check to see if this is assignment.
                        if token == LexerToken.EQUAL:

                            # Fetch the value.
                            value = self.parseterm(sourceline, 0, 65535)

                            # Check to see if we found a value.
                            if value is not None:

                                # Assign the value to the label.
                                self.pc = value

    def gettoken(self, line):

        retval = LexerToken(None, None)

        # First check to see if we need to return the previous token.
        if self.__oldtoken is not None:

            # Set the return value to this token.
            retval = self.__oldtoken

            # Reset old token.
            self.__oldtoken = None

        else:

            # Check to see if we are at the end of the line.
            if self.__linepos >= len(line):

                # Set token type.
                retval.type = LexerToken.EOL

            else:

                # Get the current character.
                currentchar = line[self.__linepos]

                # Check to see if this is a whitespace char.
                while currentchar.isspace() or currentchar == '\t':

                    # Advance pointer.
                    self.__linepos += 1

                    # Check to see if we are at the end of the line.
                    if self.__linepos >= len(line):

                        # Set token type.
                        retval.type = LexerToken.EOL

                    # Get next character.
                    currentchar = line[self.__linepos]

                # Comment.
                if currentchar == ';':
                    self.__linepos = len(line)
                    retval.type = LexerToken.EOL

                # Literal integer value.
                elif currentchar == '#':
                    retval.type = LexerToken.HASH

                # Indirect/Indexed.
                elif currentchar == '(':
                    retval.type = LexerToken.LPAREN

                # Indirect/Indexed.
                elif currentchar == ')':
                    retval.type = LexerToken.RPAREN

                # Separator for data list or indirect/indexed.
                elif currentchar == ',':
                    retval.type = LexerToken.COMMA

                # Expression/Address adjustment.
                elif currentchar == '+':
                    retval.type = LexerToken.PLUS

                # Expression/Address adjustment
                elif currentchar == '-':
                    retval.type = LexerToken.MINUS

                # Assignment.
                elif currentchar == '=':
                    retval.type = LexerToken.EQUAL

                # Program counter.
                elif currentchar == '*':
                    retval.type = LexerToken.ASTERISK

                # Label ending (sometimes).
                elif currentchar == ':':
                    retval.type = LexerToken.COLON

                # High byte notation.
                elif currentchar == '<':
                    retval.type = LexerToken.LANGLE

                # Low byte notation.
                elif currentchar == '>':
                    retval.type = LexerToken.RANGLE

                # Square bracket.
                elif currentchar == '[':
                    retval.type = LexerToken.LSQUARE

                # Close bracket.
                elif currentchar == ']':
                    retval.type = LexerToken.RSQUARE

                # Quoted string.
                elif currentchar == '"':
                    retval.type = LexerToken.QUOTE

                # Start of a pseudo-op
                elif currentchar == '.':

                    # String buffer.
                    tmpstr = []

                    # Append the dot.
                    tmpstr.append(currentchar)

                    # Increment counter to get to next character.
                    self.__linepos += 1

                    # Get the next character.
                    currentchar = line[self.__linepos]

                    # Collect all consecutive chars.
                    while currentchar.isalnum():

                        # Append the current char.
                        tmpstr.append(currentchar)

                        # Increment pointer.
                        self.__linepos += 1

                        # Check to see if we are at the end of the line.
                        if self.__linepos == len(line):
                            break

                        # Append next char.
                        currentchar = line[self.__linepos]

                    # Concat string.
                    self.__currentstring = ''.join(tmpstr)

                    # Check to see if we have an instruction.
                    if self.__currentstring in self.__pesudoops:

                        retval.value = self.__currentstring
                        retval.type = LexerToken.PSEUDO

                # Start of hex number.
                elif currentchar == '$':

                    # Increment counter to get to number.
                    self.__linepos += 1

                    # Parse the hex number.
                    retval.value = self.getnumber(16, line)
                    retval.type = LexerToken.INTEGER

                # Start of decimal number.
                elif currentchar.isdigit():
                    retval.value = self.getnumber(10, line)
                    retval.type = LexerToken.INTEGER

                # Alpha character.
                elif currentchar.isalpha():

                    # String buffer.
                    tmpstr = []

                    # Collect all consecutive chars.
                    while currentchar.isalnum():

                        # Append the current char.
                        tmpstr.append(currentchar)

                        # Increment pointer.
                        self.__linepos += 1

                        # Check to see if we are at the end of the line.
                        if self.__linepos == len(line):
                            break

                        # Append next char.
                        currentchar = line[self.__linepos]

                    # Concat string.
                    self.__currentstring = ''.join(tmpstr)

                    # Check to see if we have an instruction.
                    if self.__currentstring in self.opcodes:
                        retval.value = self.__currentstring
                        retval.type = LexerToken.OPCODE

                    # Accumulator addressing.
                    elif self.__currentstring == "A":
                        retval.type = LexerToken.ACC

                    # X indexed addressing.
                    elif self.__currentstring == "X":
                        retval.type = LexerToken.XREG

                    # Y indexed addressing.
                    elif self.__currentstring == "Y":
                        retval.type = LexerToken.YREG

                    # This is a label.
                    else:
                        retval.value = self.__currentstring
                        retval.type = LexerToken.LABEL

            # Increment counter.
            self.__linepos += 1

        # Return token.
        return retval

    def getnumber(self, base, line):

        retval = 0

        # Make sure we don't go past end of line.
        while self.__linepos < len(line):

            # Get the character.
            currentchar = line[self.__linepos]

            # Check to see if this is a digit
            if currentchar.isdigit():

                # Calculate base 10 value of ASCII digit. (48 is ASCII 0)
                retval = (retval * base) + ord(currentchar) - 48

            # Check to see if this is a hex digit.
            elif 'A' <= currentchar <= 'F' and base == 16:

                # Calculate base 16 value of ASCII character (65 is ASCII A)
                retval = (retval * base) + (ord(currentchar) - 65) + 10

            else:
                break

            # Increment position.
            self.__linepos += 1

        return retval

    def getoperand(self, line, opcode, origpc):

        # Return values.
        opcodehex = 0
        operand = 0
        length = 0

        # Get the next token.
        token = self.gettoken(line)

        # If the command is a branch, handle relative jump translation.
        if opcode in ["BRL", "BMI", "BVC", "BVS", "BCC", "BCS", "BNE", "BEQ"]:

            # All of these are relative addressing.
            opcodehex = self.opcodes[opcode]['REL']

            # Length is the one-byte opcode + the one byte jump.
            length = 2

            if token.type == LexerToken.INTEGER:

                operand = token.value & 0xFF

            elif token.type == LexerToken.LABEL:

                if self.__currentstring in self.__labels:
                    token.value = self.__labels[self.__currentstring]

                elif self.__pass == 1:
                    token.value = 0
                    length = 0

                else:
                    self.error("Undefined label: " + self.__currentstring)

                operand = (((token.value - origpc) - (self.pc + 2)) & 0xFF)

        else:
            # Based on the token, we can determine the base addressing type.
            if token.type == LexerToken.EOL:

                # This is an isntruction that doesn't take an operand.
                operand = None
                opcodehex = self.opcodes[opcode]['IMP']

                # Length is just the one-byte opcode.
                length = 1

            # This indicates immediate mode.
            elif token.type == LexerToken.HASH:

                # This is a literal decimal or hex value.
                operand = self.parseterm(line, -128, 255)
                opcodehex = self.opcodes[opcode]['IM']

                # Length is the one-byte opcode + one byte value.
                length = 2

            elif token.type == LexerToken.ACC:

                # This opcode is taking the accumulator as the operand.
                operand = None
                opcodehex = self.opcodes[opcode]['ACC']

                # Length is just the one-byte opcode.
                length = 1

            # Check to see if we have a label as the operand.
            elif token.type == LexerToken.LABEL:

                # Change the type (for processing in next block).
                token.type = LexerToken.INTEGER

                # Check to see if we have this label already in symbol table.
                if self.__currentstring in self.__labels:

                    # Assign the value to the label.
                    token.value = self.__labels[self.__currentstring]

                # If this is the first pass, assign dummy value.
                elif self.__pass == 1:

                    # Assign the value.
                    token.value = 0x100
                    length = 0

                else:

                    # We shouldn't get here unless there is a problem.
                    self.error("Undefined label: " + self.__currentstring)

            # If we have an integer, just need to determine between zero page and absolute (including x/y indexing).
            if token.type == LexerToken.INTEGER:

                # Set the operand value.
                operand = token.value

                # Check to see if this is indexed addressing.
                if self.gettoken(line) != LexerToken.COMMA:

                    # If the operand is less than 256, it is zero page addressing.
                    if token.value <= 0xFF:

                        # Get the opcode hex value.
                        opcodehex = self.opcodes[opcode]['ZP']

                        # Length is the one-byte opcode + the zero page address.
                        length = 2

                    else:

                        # Get the opcode hex value.
                        opcodehex = self.opcodes[opcode]['ABS']

                        # Length is the one-byte opcode + the two-byte address.
                        length = 3

                else:

                    # If we saw the comma, need to see if it is X or Y indexed addressing.
                    token = self.gettoken(line)

                    # X indexing.
                    if token.type == LexerToken.XREG:

                        # If the operand is less than 256, it is zero page addressing.
                        if token.value <= 0xFF:

                            # Get the opcode hex value.
                            opcodehex = self.opcodes[opcode]['ZPX']

                            # Length is the one-byte opcode + the one-byte address.
                            length = 2

                        else:

                            # Get the opcode hex value.
                            opcodehex = self.opcodes[opcode]['ABSX']

                            # Length is the one-byte opcode + the two-byte address.
                            length = 3

                    # Y indexing.
                    elif token.type == LexerToken.YREG:

                        # If the operand is less than 256, it is zero page addressing.
                        if token.value <= 0xFF:

                            # Get the opcode hex value.
                            opcodehex = self.opcodes[opcode]['ZPY']

                            # Length is the one-byte opcode + the one-byte address.
                            length = 2

                        else:

                            # Get the opcode hex value.
                            opcodehex = self.opcodes[opcode]['ABSY']

                            # Length is the one-byte opcode + the two-byte address.
                            length = 3

                    else:

                        self.error("Unknown address syntax")

                print("Operand:{0} Opcodehex {1}".format(operand, opcodehex))

        # Return the opcode hex, operand, and pc offset.
        return opcodehex, operand, length

    def parseterm(self, line, minvalue, maxvalue):

        # Generate the factors for this operand.
        retval = self.parsefactor1(line)

        # Check to see that we are in the bounds for the call.
        if retval is not None and (retval < minvalue or retval > maxvalue):

            # Set retval to none.
            retval = None

        # Return the term.
        return retval

    def parsefactor1(self, line):

        # Nested call to handle operator precedence.
        value = self.parsefactor2(line)

        while value is not None:

            # Peek ahead to get the next token.
            token = self.gettoken(line)

            #  Handle addition.
            if token.type == LexerToken.PLUS:

                # Get the factor for the operation.  This allows for any multiplication to occur first.
                value2 = self.parsefactor2(line)

                if value2 is not None:

                    # Do the math.
                    value = value + value2

                else:
                    break

            # Handle subtraction.
            elif token.type == LexerToken.MINUS:

                # Get the factor for the operation.  This allows for any multiplication to occur first.
                value2 = self.parsefactor2(line)

                if value2 is not None:

                    # Do the math.
                    value = value - value2

                else:
                    break

            # Put token back from look ahead.
            self.__oldtoken = token

            break
        return value

    def parsefactor2(self, line):

        # Parse out the factor value.
        value = self.parsenumber(line)

        while value is not None:

            # Peek ahead to get next token.
            token = self.gettoken(line)

            # Handle multiplication.
            if token.type == LexerToken.ASTERISK:

                # Parse next factor.
                value2 = self.parsenumber(line)

                if value2 is not None:

                    # Do the math.
                    value = value * value2

                else:
                    break

            # Put token back from look ahead.
            self.__oldtoken = token
            break

        return value

    def parsenumber(self, line):
        multiplier = 1
        value = None

        # Get the next token.
        token = self.gettoken(line)

        # This indicates a program counter offset.
        if token.type == LexerToken.ASTERISK:

            # Set value to program counter.
            value = self.pc

        elif token.type == LexerToken.LSQUARE:

            # Get the value between the brackets.
            value = self.parsefactor1(line)

            # Check to see if we have a close bracket.
            if self.gettoken(line) != LexerToken.RSQUARE:
                self.error("Missing ]")

        # This is for LSB processing of 2 byte values.
        elif token.type == LexerToken.LANGLE:

            # Recursive call to get the value.
            value = self.parsenumber(line)

            # Check to see if we have a value.
            if value is not None:

                # Send back just the LSB.
                value = value & 0xFF

        # This is for MSB processing of 2 byte values.
        elif token.type == LexerToken.RANGLE:

            # Recursive call to get the value.
            value = self.parsenumber(line)

            # Check to see if we have a value.
            if value is not None:

                # Send back just the MSB.
                value = (value >> 8) & 0xFF

        if token.type == LexerToken.PLUS:

            # Get the next token (should be the next factor).
            token = self.gettoken(line)

            # The value should be positive.
            multiplier = 1

        if token.type == LexerToken.MINUS:

            # Get the next token (should be the next factor).
            token = self.gettoken(line)

            # The value should be negative.
            multiplier = -1

        # The factor is a label.
        if token.type == LexerToken.LABEL:

            # Check to see if the label is recorded already.
            if self.__currentstring in self.__labels:

                # Get its value.
                value = self.__labels[self.__currentstring]

                # Change the type to numeric.
                token.type = LexerToken.INTEGER

            elif self.__pass == 1:
                value = 0x100

            else:
                self.error("Undefined label: " + self.__currentstring)

        # This is just a numeric value.  Set the value accordingly.
        elif token.type == LexerToken.INTEGER and token.value is not None:
            value = token.value

        elif token.type == LexerToken.STRING and len(self.__currentstring) == 1:
            value = ord(self.__currentstring[0])

        else:
            self.error("Value expected")

        # Return the generated value.
        return value if value is None else value * multiplier

    def error(self, errmsg):
        if self.__pass == 2:
            print("PY6502: {0} : error: {1}".format(self.infile, errmsg))

    def writelinedata(self, opcodehex, operand):

        # Check to see if we should be printing.
        if self.__pass == 2:

            # Keep running tally of bytes.
            self.incrementbyteswritten(operand)

            if self.includecounter:

                # Format the ouptut.
                outline = "{:04X} {:02X} ".format(self.pc, opcodehex)

            else:

                # Format the ouptut.
                outline = "{:02X} ".format(opcodehex)

            # Check to see if we have an operand.
            if operand is not None:

                if operand < 256:

                    # Append operand.
                    outline += "{:02X}".format(operand)

                else:
                    test = "{:04X}".format(operand)
                    test = test[2:] + " " + test[:2]

                    # Append operand.
                    outline += test

            # Write current value for PC and hex for opcode and operand.
            self.writeline(outline)

    def incrementbyteswritten(self, operand):

        # Just increment for opcode.
        self.bytecount += 1

        # Make sure we have an operand.
        if operand is not None:

            if operand <= 0xFF:

                # Increment for one byte operand.
                self.bytecount += 1

            else:

                # Increment for two byte operand.
                self.bytecount += 2

    def handlestart(self, sourceline):

        # Get the address token.
        token = self.gettoken(sourceline)

        # Check to see that we have what we want.
        if token.type == LexerToken.INTEGER and token.value > 0:

            # Assign the program counter.
            self.pc = token.value

    def handlebyte(self, sourceline):

        # Get the address token.
        token = self.gettoken(sourceline)

        # Loop through data.
        while token.type != LexerToken.EOL:

            # Check to see that we have what we want.
            if token.type == LexerToken.INTEGER:

                # Write this byte to the file.
                self.writelinedata(token.value, None)

                # Increment program counter.
                self.pc += 1

                # Advance token pointer.
                token = self.gettoken(sourceline)

            # Check to see if this is a separator.
            elif token.type == LexerToken.COMMA:

                # Advance token pointer.
                token = self.gettoken(sourceline)

            # Check to see if this is a quote (byte can be used for strings as well).
            elif token.type == LexerToken.QUOTE:

                # Put the token back.
                self.__oldtoken = token

                # Call ascii handler.
                self.handleascii(sourceline)

                # Advance token pointer.
                token = self.gettoken(sourceline)

    def handleascii(self, sourceline):

        # Flag for closing quote of string.
        closequote = False

        # Get the next token.
        token = self.gettoken(sourceline)

        # Loop through data.
        while token.type != LexerToken.EOL:

            # Need the first quote.
            if token.type == LexerToken.QUOTE and not closequote:

                # Flip flag - next quote will be a close.
                closequote = True

                # Get the next token.
                token = self.gettoken(sourceline)

                # Loop through the string.
                for letter in token.value:

                    # Write this byte to the file.
                    self.writelinedata(ord(letter), None)

                    # Increment program counter.
                    self.pc += 1

            # Check to see if this is a separator.
            elif token.type == LexerToken.COMMA:

                # Flip flag - next quote will be an open.
                closequote = False

            # Advance token pointer.
            token = self.gettoken(sourceline)

        # Error check to see if user closed the quote.
        if not closequote:
            self.error("String not closed properly.")

    def handleword(self, sourceline):

        # Get the address token.
        token = self.gettoken(sourceline)

        # Loop through data.
        while token.type != LexerToken.EOL:

            # Check to see that we have what we want.
            if token.type == LexerToken.INTEGER and token.value > 0:

                # Write these bytes to the file in little endian.
                self.writelinedata((token.value & 0xFF), None)
                self.writelinedata((token.value >> 8) & 0xFF, None)

                # Increment program counter.
                self.pc += 2

            # Check to see if this is a separator.
            elif token.type == LexerToken.COMMA:

                # Advance token pointer.
                token = self.gettoken(sourceline)

    def handleend(self):
        pass

    def loadpesudoops(self):
        self.__pesudoops = {
            '.ORG': self.handlestart,
            '*=': self.handlestart,
            '.BYTE': self.handlebyte,
            '.DB': self.handlebyte,
            '.ASCII': self.handleascii,
            '.TX': self.handleascii,
            '.WORD': self.handleword,
            '.DW': self.handleword,
            '.END': self.handleend,
        }

    def loadopcodes(self):
        self.opcodes = {
            'ADC': {'IM': 0x69, 'ZP': 0x65, 'ZPX': 0x75, 'ABS': 0x6D, 'ABSX': 0x7D, 'ABSY': 0x79, 'INDX': 0x61,
                    'INDY': 0x71},
            'AND': {'IM': 0x29, 'ZP': 0x25, 'ZPX': 0x35, 'ABS': 0x2D, 'ABSX': 0x3D, 'ABSY': 0x39, 'INDX': 0x21,
                    'INDY': 0x31},
            'ASL': {'ZP': 0x06, 'ZPX': 0x16, 'ABS': 0x0E, 'ABSX': 0x1E, 'ACC': 0x0A},
            'BIT': {'ZP': 0x24, 'ABS': 0x2C},
            'BPL': {'REL': 0x10},
            'BMI': {'REL': 0x30},
            'BVC': {'REL': 0x50},
            'BVS': {'REL': 0x70},
            'BCC': {'REL': 0x90},
            'BCS': {'REL': 0xB0},
            'BNE': {'REL': 0xD0},
            'BEQ': {'REL': 0xF0},
            'BRK': {'IMP': 0x00},
            'CMP': {'IM': 0xC9, 'ZP': 0xC5, 'ZPX': 0xD5, 'ABS': 0xCD, 'ABSX': 0xDD, 'ABSY': 0xD9, 'INDX': 0xC1,
                    'INDY': 0xD1},
            'CPX': {'IM': 0xE0, 'ZP': 0xD4, 'ABS': 0xEC},
            'CPY': {'IM': 0xC0, 'ZP': 0xC4, 'ABS': 0xCC},
            'DEC': {'ZP': 0xC6, 'ZPX': 0xD6, 'ZPY': 0xCE, 'ABS': 0xDC},
            'EOR': {'IM': 0x49, 'ZP': 0x45, 'ZPX': 0x55, 'ABS': 0x4D, 'ABSX': 0x5D, 'ABSY': 0x59, 'INDX': 0x41,
                    'INDY': 0x51},
            'CLC': {'IMP': 0x18},
            'SEC': {'IMP': 0x38},
            'CLI': {'IMP': 0x58},
            'SEI': {'IMP': 0x78},
            'CLV': {'IMP': 0xB8},
            'CLD': {'IMP': 0xD8},
            'SED': {'IMP': 0xF8},
            'INC': {'ZP': 0xE6, 'ZPX': 0xF6, 'ABS': 0xEE, 'ABSX': 0xFE},
            'JMP': {'ABS': 0x4C, 'IND': 0x6C},
            'JSR': {'ABS': 0x20},
            'LDA': {'IM': 0xA9, 'ZP': 0xA5, 'ZPX': 0xB5, 'ABS': 0xAD, 'ABSX': 0xBD, 'ABSY': 0xB9, 'INDX': 0xA1,
                    'INDY': 0xB1},
            'LDX': {'IM': 0xA2, 'ZP': 0xA6, 'ZPY': 0xB6, 'ABS': 0xAE, 'ABSY': 0xBE},
            'LDY': {'IM': 0xA0, 'ZP': 0xA4, 'ZPX': 0xB4, 'ABS': 0xAC, 'ABSX': 0xBC},
            'LSR': {'ZP': 0x46, 'ZPX': 0x56, 'ABS': 0x4E, 'ABSX': 0x5E},
            'NOP': {'IMP': 0xEA},
            'ORA': {'IM': 0x09, 'ZP': 0x05, 'ZPX': 0x15, 'ABS': 0x0D, 'ABSX': 0x1D, 'ABSY': 0x19, 'INDX': 0x01,
                    'INDY': 0x11},
            'TAX': {'IMP': 0xAA},
            'TXA': {'IMP': 0x8A},
            'DEX': {'IMP': 0xCA},
            'INX': {'IMP': 0xE8},
            'TAY': {'IMP': 0xA8},
            'TYA': {'IMP': 0x98},
            'DEY': {'IMP': 0x88},
            'INY': {'IMP': 0xC8},
            'ROL': {'ZP': 0x26, 'ZPX': 0x36, 'ABS': 0x2E, 'ABSX': 0x3E, 'ACC': 0x2A},
            'ROR': {'ZP': 0x66, 'ZPX': 0x76, 'ABS': 0x6E, 'ABSX': 0x7E, 'ACC': 0x6A},
            'RTI': {'IMP': 0x40},
            'RTS': {'IMP': 0x60},
            'SBC': {'IM': 0xE9, 'ZP': 0xE5, 'ZPX': 0xF5, 'ABS': 0xED, 'ABSX': 0xFD, 'ABSY': 0xF9, 'INDX': 0xE1,
                    'INDY': 0xF1},
            'STA': {'ZP': 0x85, 'ZPX': 0x95, 'ABS': 0x8D, 'ABSX': 0x9D, 'ABSY': 0x99, 'INDX': 0x81, 'INDY': 0x91},
            'TXS': {'IMP': 0x9A},
            'TSX': {'IMP': 0x8A},
            'PHA': {'IMP': 0x48},
            'PLA': {'IMP': 0x68},
            'PHP': {'IMP': 0x08},
            'PLP': {'IMP': 0x28},
            'STX': {'ZP': 0x86, 'ZPY': 0x96, 'ABS': 0x8E},
            'STY': {'ZP': 0x84, 'ZPX': 0x94, 'ABS': 0x8C}
        }
