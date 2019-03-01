from mfcbase import MFCBase


class Disassembler(MFCBase):

    def __init__(self, infile, outfile, startaddr, includecounter, counterinfile):

        # This variable handles the writing of the start position of file.
        self.__programstartset = False

        # Superclass init.
        super(Disassembler, self).__init__(infile, outfile, startaddr, includecounter, counterinfile)

        # Load the hex values.
        self.loadhexcodes()

    def disassemble(self):

        # Parse the input file.
        self.parse()

        # Parse the commands into hex codes.
        self.parsecommands()

    def parsecommands(self):

        # Loop through file.
        for sourceline in super(Disassembler, self).sourcelines:

            # Split into parts based on spaces.
            lineparts = sourceline.split()

            # Check to see if we have a start address handled.
            if not self.__programstartset:

                # Set the program listing start address (if possible).
                self.setprogramstartaddress(lineparts)

                # Write file header.
                self.writeheader()

            # Check to see if we should skip the program counter.
            if self.counterinfile:

                # Get the opcode and operand, skipping the hex address.
                opcode, operand = self.getopcodeandoperand(lineparts, 1)

            else:

                # Get the opcode and operand.
                opcode, operand = self.getopcodeandoperand(lineparts, 0)

            # Get command formatter based on operand.
            command = self.opcodes[int(opcode, 16)]

            # Call formatting and output functions.
            command[1](command[0], operand)

    def getopcodeandoperand(self, line, opcodepos):

        operand = None

        # Get the next byte - this is the opcode.
        opcode = line[opcodepos]

        # Based on the number of tokens we have, grab operand.
        if len(line) == (opcodepos + 2):

            # There is a 1 byte operand.
            operand = int(line[opcodepos + 1], 16)

        elif len(line) == (opcodepos + 3):

            # There is a 2 byte operand.  This is little endian so we need the last part first.
            operand = int(line[opcodepos + 2] + line[opcodepos + 1], 16)

        # Return the opcode and operand.
        return opcode, operand

    def setprogramstartaddress(self, line):

        # This procedure should only ever run once.
        self.__programstartset = True

        try:

            # Check to see if line starts with a hex address
            if self.counterinfile:

                # Try to convert
                intval = int(line[0], 16)

                if intval < 1 or intval > 65535:
                    raise ValueError

                else:
                    # Set the counter.
                    self.pc = intval

        except ValueError:
            print('Invalid address or format for program counter.')

    def signextend(self, r):
        return r if r < 0x80 else r - 0x100

    def writeheader(self):

        self.writeline(";;;;;;;;;;;;;;;;;;;;;;;;;")
        self.writeline("; %s" % self.outfile.name)
        self.writeline(";")
        self.writeline("; Disassembled by mfc6502")
        self.writeline(";;;;;;;;;;;;;;;;;;;;;;;;;")
        self.writeline("")

        # Output the program start.
        output = "*=$" + "{:04X}".format(self.pc)
        self.writeline(output)
        self.writeline("")

    def writelinedata(self, size, value):
        str_out = []

        # Check to see if we should output the instruction address.
        if self.includecounter:
            str_out.append("{0:04X} ".format(self.pc))

        # Append opcode
        str_out.append(value)

        # Write the line to the file.
        self.writeline("".join(str_out))
        self.pc += size

    def formatasempty(self, opcode, operand=None):
        self.writelinedata(1, opcode)

    def formatasimmediate(self, opcode, operand):
        self.writelinedata(2, "{0} #${1:02X}".format(opcode, operand))

    def formataszeropage(self, opcode, operand):
        self.writelinedata(2, "{0} ${1:02X}".format(opcode, operand))

    def formataszeropagex(self, opcode, operand):
        self.writelinedata(2, "{0} ${1:02X},X".format(opcode, operand))

    def formataszeropagey(self, opcode, operand):
        self.writelinedata(2, "{0} ${1:02X},Y".format(opcode, operand))

    def formatasabsolute(self, opcode, operand):
        self.writelinedata(3, "{0} ${1:04X}".format(opcode, operand))

    def formatasabsolutex(self, opcode, operand):
        self.writelinedata(3, "{0} ${1:04X},X".format(opcode, operand))

    def formatasabsolutey(self, opcode, operand):
        self.writelinedata(3, "{0} ${1:04X},Y".format(opcode, operand))

    def formatasindirectx(self, opcode, operand):
        self.writelinedata(2, "{0} (${1:02X},X)".format(opcode, operand))

    def formatasindirecty(self, opcode, operand):
        self.writelinedata(2, "{0} (${1:02X}),Y".format(opcode, operand))

    def formatasbranch(self, opcode, operand):
        self.writelinedata(2, "{0} {1:04X}".format(opcode, self.pc + 2 + self.signextend(operand)))

    def formatasjump(self, opcode, operand):
        self.writelinedata(3, "{0} {1:04X}".format(opcode, operand))

    def loadhexcodes(self):
        self.opcodes = {
            0x00: ("BRK", self.formatasempty),
            0x01: ("ORA", self.formatasindirectx),
            0x05: ("ORA", self.formataszeropage),
            0x06: ("ASL", self.formataszeropage),
            0x08: ("PHP", self.formatasempty),
            0x09: ("ORA", self.formatasimmediate),
            0x0A: ("LDY", self.formatasimmediate),
            0x0D: ("ORA", self.formatasabsolute),
            0x0E: ("ASL", self.formatasabsolute),
            0x10: ("BPL", self.formatasbranch),
            0x11: ("ORA", self.formatasindirecty),
            0x15: ("ORA", self.formataszeropagex),
            0x16: ("ASL", self.formataszeropagex),
            0x18: ("CLC", self.formatasempty),
            0x19: ("ORA", self.formatasabsolutey),
            0x1D: ("ORA", self.formatasabsolutex),
            0x1E: ("ASL", self.formatasabsolutex),
            0x20: ("JSR", self.formatasjump),
            0x21: ("AND", self.formatasindirectx),
            0x24: ("BIT", self.formataszeropage),
            0x25: ("AND", self.formataszeropage),
            0x26: ("ROL", self.formataszeropage),
            0x28: ("PLP", self.formatasempty),
            0x29: ("AND", self.formatasimmediate),
            0x2A: ("ROL", self.formatasempty),
            0x2C: ("BIT", self.formatasabsolute),
            0x2D: ("AND", self.formatasabsolute),
            0x2E: ("ROL", self.formatasabsolute),
            0x30: ("BMI", self.formatasbranch),
            0x31: ("AND", self.formatasindirecty),
            0x35: ("AND", self.formataszeropagex),
            0x36: ("ROL", self.formataszeropagex),
            0x38: ("SEC", self.formatasempty),
            0x39: ("AND", self.formatasabsolutey),
            0x3D: ("AND", self.formatasabsolutex),
            0x3E: ("ROL", self.formatasabsolutex),
            0x40: ("RTI", self.formatasempty),
            0x41: ("EOR", self.formatasindirectx),
            0x45: ("EOR", self.formataszeropage),
            0x46: ("LSR", self.formataszeropage),
            0x48: ("PHA", self.formatasempty),
            0x49: ("EOR", self.formatasimmediate),
            0x4A: ("LSR", self.formatasempty),
            0x4C: ("JMP", self.formatasjump),
            0x4D: ("EOR", self.formatasabsolute),
            0x4E: ("LSR", self.formatasabsolute),
            0x50: ("BVC", self.formatasbranch),
            0x51: ("EOR", self.formatasindirecty),
            0x55: ("EOR", self.formataszeropagex),
            0x56: ("LSR", self.formataszeropagex),
            0x58: ("CLI", self.formatasempty),
            0x59: ("EOR", self.formatasabsolutey),
            0x5A: ("PHY", self.formatasempty),
            0x5D: ("EOR", self.formatasabsolutex),
            0x5E: ("LSR", self.formatasabsolutex),
            0x60: ("RTS", self.formatasempty),
            0x61: ("ADC", self.formatasindirectx),
            0x65: ("ADC", self.formataszeropage),
            0x66: ("ROR", self.formataszeropage),
            0x68: ("PLA", self.formatasempty),
            0x69: ("ADC", self.formatasimmediate),
            0x6A: ("ROR", self.formatasempty),
            0x6D: ("ADC", self.formatasabsolute),
            0x6E: ("ROR", self.formatasabsolute),
            0x70: ("BVS", self.formatasbranch),
            0x71: ("ADC", self.formatasindirecty),
            0x75: ("ADC", self.formataszeropagex),
            0x76: ("ROR", self.formataszeropagex),
            0x78: ("SEI", self.formatasempty),
            0x79: ("ADC", self.formatasabsolutey),
            0x7A: ("PLY", self.formatasempty),
            0x7D: ("ADC", self.formatasabsolutex),
            0x7E: ("ROR", self.formatasabsolutex),
            0x81: ("STA", self.formatasindirectx),
            0x84: ("STY", self.formataszeropage),
            0x85: ("STA", self.formataszeropage),
            0x86: ("STX", self.formataszeropage),
            0x88: ("DEY", self.formatasempty),
            0x8A: ("TXA", self.formatasempty),
            0x8C: ("STY", self.formatasabsolute),
            0x8D: ("STA", self.formatasabsolute),
            0x8E: ("STX", self.formatasabsolute),
            0x90: ("BCC", self.formatasbranch),
            0x91: ("STA", self.formatasindirecty),
            0x94: ("STY", self.formataszeropagex),
            0x95: ("STA", self.formataszeropagex),
            0x96: ("STX", self.formataszeropagey),
            0x98: ("TYA", self.formatasempty),
            0x99: ("STA", self.formatasabsolutey),
            0x9A: ("TXS", self.formatasempty),
            0x9D: ("STA", self.formatasabsolutex),
            0xA0: ("LDY", self.formatasimmediate),
            0xA1: ("LDA", self.formatasindirectx),
            0xA2: ("LDX", self.formatasimmediate),
            0xA4: ("LDY", self.formataszeropage),
            0xA5: ("LDA", self.formataszeropage),
            0xA6: ("LDX", self.formataszeropage),
            0xA8: ("TAY", self.formatasempty),
            0xA9: ("LDA", self.formatasimmediate),
            0xAA: ("TAX", self.formatasempty),
            0xAC: ("LDY", self.formatasabsolute),
            0xAD: ("LDA", self.formatasabsolute),
            0xAE: ("LDX", self.formatasabsolute),
            0xB0: ("BCS", self.formatasbranch),
            0xB1: ("LDA", self.formatasindirecty),
            0xB4: ("LDY", self.formataszeropagex),
            0xB5: ("LDA", self.formataszeropagex),
            0xB6: ("LDX", self.formataszeropagey),
            0xB8: ("CLV", self.formatasempty),
            0xB9: ("LDA", self.formatasabsolutey),
            0xBA: ("TSX", self.formatasempty),
            0xBC: ("LDY", self.formatasabsolutex),
            0xBD: ("LDA", self.formatasabsolutex),
            0xBE: ("LDX", self.formatasabsolutey),
            0xC0: ("CPY", self.formatasimmediate),
            0xC1: ("CMP", self.formatasindirectx),
            0xC4: ("CPY", self.formataszeropage),
            0xC5: ("CMP", self.formataszeropage),
            0xC6: ("DEC", self.formataszeropage),
            0xC8: ("INY", self.formatasempty),
            0xC9: ("CMP", self.formatasimmediate),
            0xCA: ("DEX", self.formatasempty),
            0xCC: ("CPY", self.formatasabsolute),
            0xCD: ("CMP", self.formatasabsolute),
            0xCE: ("DEC", self.formatasabsolute),
            0xD0: ("BNE", self.formatasbranch),
            0xD1: ("CMP", self.formatasindirecty),
            0xD5: ("CMP", self.formataszeropagex),
            0xD6: ("DEC", self.formataszeropagex),
            0xD8: ("CLD", self.formatasempty),
            0xD9: ("CMP", self.formatasabsolutey),
            0xDA: ("PHX", self.formatasempty),
            0xDD: ("CMP", self.formatasabsolutex),
            0xDE: ("DEC", self.formatasabsolutex),
            0xE0: ("CPX", self.formatasimmediate),
            0xE1: ("SBC", self.formatasindirectx),
            0xE4: ("CPX", self.formataszeropage),
            0xE5: ("SBC", self.formataszeropage),
            0xE6: ("INC", self.formataszeropage),
            0xE8: ("INX", self.formatasempty),
            0xE9: ("SBC", self.formatasimmediate),
            0xEA: ("NOP", self.formatasempty),
            0xEC: ("CPX", self.formatasabsolute),
            0xED: ("SBC", self.formatasabsolute),
            0xEE: ("INC", self.formatasabsolute),
            0xF0: ("BEQ", self.formatasbranch),
            0xF1: ("SBC", self.formatasindirecty),
            0xF5: ("SBC", self.formataszeropagex),
            0xF6: ("INC", self.formataszeropagex),
            0xF8: ("SED", self.formatasempty),
            0xF9: ("SBC", self.formatasabsolutey),
            0xFA: ("PLX", self.formatasempty),
            0xFD: ("SBC", self.formatasabsolutex),
            0xFE: ("INC", self.formatasabsolutex),
            0xFF: (".SYS", self.formatasimmediate)
        }
