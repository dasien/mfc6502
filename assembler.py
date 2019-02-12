from mfcbase import MFCBase
from token import Token

# TODO: Need to remove all the file position parsing in favor of tokens.
class Assembler(MFCBase):

    def __init__(self, infile, outfile, startaddr=None, includecounter=False):

        # Labels are supported.
        self.__labels = dict()

        # So are directives.
        self.__directives = dict()

        # Pointer to current character in file.
        self.__linepos = 0

        # Default program counter.
        self.pc = 0x0000

        # Superclass init.
        super(Assembler, self).__init__(infile, outfile, startaddr, includecounter)

        # Load opcode table.
        self.loadopcodes()

    def assemble(self):

        # Parse the input file.
        self.parse()

        # Loop through each line.
        for sourceline in  super(Assembler, self).sourcelines:

            # Get the current token.
            token = self.gettoken()

                # Loop through each character in the line.
                while token.type != token.EOL:

        # Create the lookup table for labels/variables.
        self.buildsymboltable()

        # Parse the commands into hex codes.
        self.parsecommands()

    def gettoken(self, line):

        retVal = Token.__init__()

        # Check to see if we are at the end of the line.
        if self.__linepos >= len(line):

            # Set token type.
            retVal.type = Token.EOL

        else:

            # Get the current character.
            currentchar = line[self.__linepos]

            # Check to see if this is a whitespace char.
            while currentchar.isspace():

                # Advance pointer.
                self.__linepos += 1

                # Check to see if we are at the end of the line.
                if self.__linepos >= len(line):

                    # Set token type.
                    retVal.type = Token.EOL

                else:

                    # Get next character.
                    currentchar = line[self.__linepos]


    def buildsymboltable(self):

        try:

            # A temporary program counter.
            temp = self.pc

            # Loop through the source lines (label pass).
            for sourceline in super(Assembler, self).sourcelines:

                # Check to see if this is a program counter.
                if not self.setprogramcounter(sourceline):

                    # Check to see if we have a label at the first part of line.
                    if sourceline[0] in super(Assembler, self).opcodes:

                        # Handle branches with default operand length.
                        if sourceline[0] in ["BRL", "BMI", "BVC", "BVS", "BCC", "BCS", "BNE", "BEQ"]:
                            opcodelen = 2

                        # Handle jumps with default operand length.
                        elif sourceline[0] in ["JSR", "JMP"]:
                            opcodelen = 3

                        # All other opcodes should be referencing known variables.
                        else:

                            # Get the hex value of the opcode and the length.
                            if len(sourceline) == 1:
                                opcodehex, opcodelen, operand = self.getopcodedata(sourceline[0], None)

                            else:

                                # Check to see if the operand is a label.
                                if sourceline[1] in self.__labels:

                                    # Use the value stored for the label as operand.
                                    opcodehex, opcodelen, operand = self.getopcodedata(sourceline[0],
                                                                                       self.__labels[sourceline[1]])

                                else:

                                    # Get command data.
                                    opcodehex, opcodelen, operand = self.getopcodedata(sourceline[0], sourceline[1])

                        # Increment program counter.
                        self.incrementprogramcounter(opcodelen)

                    elif len(super(Assembler, self).sourcelines) == 2:

                        # Check to see if this is a variable.
                        if sourceline[1] == "=" or sourceline[1] == ".EQU":
                            # This is a variable.  Add it to symbol table with address.
                            self.createvariable(sourceline)

                    else:

                        # We found a label.  Add it with current program counter value.
                        self.createsymbol(sourceline)

            # After processing for labels, reset the program counter.
            self.pc = temp

            # Report Symbols found.
            print("Found %s symbols..." % len(self.__labels))

        except:
            print("Error building symbols table.")

    def parsecommands(self):

        try:

            # Loop through file.
            for sourceline in super(Assembler, self).sourcelines:

                # Reset print flag.
                printlinedata = True

                # Check to see if this is a program counter.
                if not self.setprogramcounter(sourceline):

                    # Variables for discrete parts.
                    opcodehex = None
                    opcodelen = None
                    operand = None

                    # Check to see that we have found an opcode.
                    if sourceline[0] in super(Assembler, self).opcodes:

                        # Check to see if there is an operand.
                        if len(sourceline) == 1:

                            # No operand present.  Get command data.
                            opcodehex, opcodelen, operand = self.getopcodedata(sourceline[0], None)

                        else:

                            # Need to see if this is a label (could have ,X or ,Y after label name)
                            labelparts = sourceline[1].split(",")

                            if labelparts[0] in self.__labels:

                                # Check to see if there is an offset.
                                if len(labelparts) == 1:

                                    # Use the value stored for the label as operand.
                                    opcodehex, opcodelen, operand = self.getopcodedata(sourceline[0],
                                                                                       self.__labels[labelparts[0]])
                                else:

                                    fulllabel = self.__labels[labelparts[0]] + "," + labelparts[1]

                                    # Use the value stored for the label with the offset as operand.
                                    opcodehex, opcodelen, operand = self.getopcodedata(sourceline[0], fulllabel)

                            else:
                                # Operand is address or value.  Get command data.
                                opcodehex, opcodelen, operand = self.getopcodedata(sourceline[0], sourceline[1])

                    elif sourceline[0] in self.__labels:

                        # Check to see if it is a label with a blaank line (opcode on next line).
                        if len(sourceline) > 1:

                            # We found a label.  Need to get the opcode from the next part.
                            if sourceline[1] in super(Assembler, self).opcodes:

                                # Get the hex value of the opcode and the length.
                                opcodehex, opcodelen, operand = self.resolvesymboldata(sourceline)

                            # Check to see if this is an assignment.
                            elif sourceline[1] == "=" or sourceline[1] == ".EQU":

                                # This is a variable assignment - skip it.
                                continue

                        else:

                            # Flag this line as only a label so no printing is done.
                            printlinedata = False
                    else:

                        # We shouldn't get here unless something is wrong.
                        raise Exception("Syntax Error.")

                    # Check to see if we should print the line.
                    if printlinedata:
                        # Write the data for the line and logging data.
                        self.writelinedata(opcodehex, operand)

                        # Increment program counter.
                        self.incrementprogramcounter(opcodelen)

            # Report bytes written.
            print("Wrote %s bytes to file..." % super(Assembler, self).bytecount)

        except:
            print("Error in command parsing.")

    def writelinedata(self, opcodehex, operand):

        # Handle blank operands.
        if operand is None:
            # Make it blank.
            operand = ""

        # Keep running tally of bytes.
        self.incrementbyteswritten(operand)

        if self.includecounter:
            # Format the ouptut.
            outline = "%s %s %s" % (format(self.pc, '04X'), format(opcodehex, '02X'), operand)

        else:
            # Format the ouptut.
            outline = "%s %s" % (format(opcodehex, '02X'), operand)

        # Write current value for PC and hex for opcode and operand.
        self.writeline(outline)

    def createsymbol(self, sourceline):

        # Remove trailing colon if present.
        label = sourceline[0].rstrip(':')

        # Add symbol to table.
        self.__labels[label] = "${0:04X}".format(super(Assembler, self).pc)

        # Check to see if there is only a label on this line.
        if len(sourceline) > 1:

            if sourceline[1] in super(Assembler, self).opcodes:
                # Get the hex value of the opcode and the length.
                opcodehex, opcodelen, operand = self.resolvesymboldata(sourceline)

                # Increment program counter.
                self.incrementprogramcounter(opcodelen)

    def resolvesymboldata(self, sourceline):

        # Get the hex value of the opcode and the length.
        if len(sourceline) == 2:

            # Get command data.
            opcodehex, opcodelen, operand = self.getopcodedata(sourceline[1], None)

        else:

            # Get command data.
            opcodehex, opcodelen, operand = self.getopcodedata(sourceline[1], sourceline[2])

        return opcodehex, opcodelen, operand

    def createvariable(self, sourceline):

        # Clean up any non address parts.
        address = sourceline[2].strip("<>(),")

        #  Log it to the label table with value.
        self.__labels[sourceline[0]] = address

    def getopcodedata(self, opcode, operand):

        # Get the hex value of the opcode and the length.
        opcodehex, opcodelen = self.gethexvalueandlength(opcode, operand)

        # If the command is a branch, handle relative jump translation.
        if opcode in ["BRL", "BMI", "BVC", "BVS", "BCC", "BCS", "BNE", "BEQ"]:
            # Calculate jump distance.
            operand = self.computebranchhex(super(Assembler, self).pc, operand)

        # Get the operand in correct notation (LSB, HSB).
        formattedoperand = self.getoperandvalue(operand)

        # Check to see if a hex code was found.
        if opcodehex is None:
            raise Exception("Invalid Addressing Mode for Opcode %s" % opcode)

        return opcodehex, opcodelen, formattedoperand

    def computebranchhex(self, currentaddress, branchtoaddress):

        # Stip out any formatting chars.
        branchtoaddress = branchtoaddress.strip("#$")

        # Branching is from PC + 2 (because the PC hasn't incremented yet for this opcode)
        increment = int("2", 16)

        # Convert to hex.
        ba = int(branchtoaddress, 16)

        # Increment temp program counter.
        currentaddress += increment

        # Calculate branch distance.
        distance = (ba - currentaddress)

        if distance < -127 or distance > 128:
            raise Exception("Branch address too far.")

        # Convert back to bytes.
        value = distance.to_bytes(1, "big", signed=True)

        formatted = ''.join(["%02X " % x for x in value]).strip()

        return formatted

    def setprogramcounter(self, line):

        # Return value.
        retval = False
        val = "0"

        # Chect to see if the line begins with PC identifier.
        if line[0:3] == "*=$":
            val = line[3:]
            retval = True

        # Handle the .ORG directive.
        elif line[0] == ".ORG":
            val = line[1][1:]
            retval = True

        if retval:

            try:
                intval = int(val)

                if intval < 1 or intval > 65535:
                    raise ValueError

                else:
                    # Set the counter.
                    self.pc = intval

            except ValueError:
                print('Invalid address or format for program counter.')

        return retval

    def incrementprogramcounter(self, offset):

        # Add the offset.
        self.pc += offset

    def incrementbyteswritten(self, operand):

        # Just increment for opcode.
        self.bytecount += 1

        if len(operand) == 2:

            # Increment for one byte operand.
            self.bytecount += 1

        elif len(operand) == 5:

            # Increment for two byte operand.
            self.bytecount += 2

    def gethexvalueandlength(self, opcode, operand):

        # Lookup opcode in table.
        command = super(Assembler, self).opcodes[opcode]

        # The return value.
        hexcode = None
        length = 0

        # Check for implied addressing.
        if operand is None:
            hexcode = command['IMP']
            length = 1

        # Deal with branch instructions.
        elif opcode in ["BRL", "BMI", "BVC", "BVS", "BCC", "BCS", "BNE", "BEQ"]:
            hexcode = command['REL']
            length = 2

        # Check to see if this is immediate.
        elif operand[0] == "#" or operand[0:2] == "#$":
            hexcode = command['IM']
            length = 2

        # Check for zero page.
        elif operand[0] == "$" and len(operand) == 3:
            hexcode = command['ZP']
            length = 2

        # This can be either zero page or absolute (two byte)
        elif operand[0] == "$" and len(operand) == 5:
            hexcode = command['ABS']
            length = 3

            # Check for zero page, x.
            if operand[3:5] == ",X":
                hexcode = command['ZPX']
                length = 2

            # Check for zero page, x.
            if operand[3:5] == ",Y":
                hexcode = command['ZPY']
                length = 2

        # Check for absolute with x or y.
        elif operand[0] == "$" and len(operand) == 7:

            length = 3

            # Check for absolute, x.
            if operand[5:7] == ",X":
                hexcode = command['ABSX']

            # Check for absolute, y.
            if operand[5:7] == ",Y":
                hexcode = command['ABSY']

        # Check for indirect.
        elif operand[0] == "(" and len(operand) == 7:
            hexcode = command['IND']
            length = 3

            # Check for indirect, x.
            if operand[4:7] == ",X)":
                hexcode = command['INDX']
                length = 2

            # Check for indirect, y.
            if operand[4:7] == "),Y":
                hexcode = command['INDY']
                length = 2

        # Check for accumumlator.
        elif operand[0] == "A":
            hexcode = command['ACC']
            length = 1

        # Return value.
        return hexcode, length

    def getoperandvalue(self, operand):

        # The return address.
        retval = None

        if operand is not None and operand is not "A":
            retval = operand.strip("#$(),XY")

            # Swap byte order for 2 byte addresses.
            if len(retval) == 4:
                retval = retval[2:] + " " + retval[:2]

        return retval

    def handleStart(self):
        pass

    def handleByte(self):
        pass

    def handleASCII(self):
        pass

    def handleWord(self):
        pass

    def handleEnd(self):
        pass

    def loaddirectives(self):
        self.__directives = {
            '.org': self.handleStart,
            'org': self.handleStart,
            '*=': self.handleStart,
            '.byte':  self.handleByte,
            '.db': self.handleByte,
            'db': self.handleByte,
            '.ascii': self.handleASCII,
            '.tx': self.handleASCII,
            'tx': self.handleASCII,
            '.word': self.handleWord,
            '.dw': self.handleWord,
            'dw': self.handleWord,
            '.end': self.handleEnd,
            'end': self.handleEnd
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
