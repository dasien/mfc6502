from datetime import datetime
from memory import Memory
from mfcbase import MFCBase


class Processor(MFCBase):

    def __init__(self, infile, outfile, startaddr, includecounter, verbose):

        # These represent the program counter, a, x, y registers, stack pointer, processor flags, and a cycle counter.
        self.pc = 0x0000
        self.a = 0x00
        self.x = 0x00
        self.y = 0x00
        self.sp = 0x01FF
        self.pf = 0x00
        self.cy = 0
        self.maxmemory = 65536
        self.instructions = None
        self.verbose = verbose

        # Load the allowable instructions.
        self.loadinstructionset()

        # Superclass init.
        super(Processor, self).__init__(infile, outfile, startaddr, includecounter)

        # Initialize memory (64k).
        self._memory = Memory(self.maxmemory)

        # Parse the input file.
        self.parse()

        # Load program into memory.
        self.loadmemory(startaddr, self.sourcelines)

        # Set the program counter.
        self.pc = startaddr

    # region CPU Control

    def loadmemory(self, startaddress, data):

        # Load the data into memory.
        self._memory.load(startaddress, data)

    def reset(self):

        # Reset registers.
        self.a = 0x00
        self.x = 0x00
        self.y = 0x00
        self.sp = 0xff

        # Reset flags
        self.pf = Flags.BREAK | Flags.UNUSED

        # Read the data from the reset vector.
        addrlow = self._memory.readbyte(Vectors.RESET_ADDR_LOW)
        addrhigh = self._memory.readbyte(Vectors.RESET_ADDR_HIGH)

        # Check to see that we have valid reset vector address.
        if (self.validateaddress(addrlow)) and (self.validateaddress(addrhigh)):

            # Set program counter to address.
            self.pc = (addrlow & 0xff) | ((addrhigh << 8) & 0xff00)

            return True
        else:
            print("ERROR: Bad reset vector address %s,%s" %
                  (format(str(self._memory.readbyte(addrlow)), '02X'), format(str(self._memory.readbyte(addrhigh)), '02X')))
            return False

    # def singlestep(self):

    def freerun(self):

        # Begin message.
        self.writeheadermessage()

        # Loop through the code that is loaded in memory.
        while self._memory.readbyte(self.pc) is not -1:
            # Fetch the first instruction.
            opcode = self._memory.readbyte(self.pc)

            # Get the command from the supported opcodes.
            instruction = self.instructions[opcode]

            # Increment program counter.
            self.pc += 1

            # Execute instruction.
            instruction()

        # End message.
        self.writefootermessage()

    def showcpustate(self):

        # Get string versions of the byte values.
        str_pc = self.onebytetostring(self.pc)
        str_a = self.onebytetostring(self.a)
        str_x = self.onebytetostring(self.x)
        str_y = self.onebytetostring(self.y)
        str_sp = self.onebytetostring(self.sp & 0xFF)
        str_pf = self.onebytetostring(self.pf)

        print("PC:" + str_pc + " A:" + str_a + " X:" + str_x + " Y:" + str_y + " SP:" + str_sp + " Flags:" + str_pf +
              " CPU Cycles:" + str(self.cy))

    # endregion

    # region Helper Methods

    def writeheadermessage(self):
        print(";;;;;;;;;;;;;;;;;;;;;;;;;")
        print("; Execution Begins: %s" % datetime.now())
        print(";;;;;;;;;;;;;;;;;;;;;;;;;")

    def writefootermessage(self):
        print(";;;;;;;;;;;;;;;;;;;;;;;;;")
        print("; Execution Ends: %s" % datetime.now())
        print(";;;;;;;;;;;;;;;;;;;;;;;;;")

    def onebytetostring(self, value):
        return "0x%02x" % value

    def twobytestostring(self, value):
        return "0x%04x" % value

    # TODO: Need to calculate accurate cycle times for calculations that cross page boundries.
    def calcuateaddress(self, useonebyte, offset):

        address = -1

        # Check to see if we are basing the address on one byte or two.
        if useonebyte:

            # Calculate the correct address.
            address = self._memory.readbyte(self.pc + offset) & 0xFF

        else:
            # Calculate the correct address.
            address = self._memory.readbyte(self.pc) + (0x100 * self._memory.readbyte(self.pc + 1)) + offset

        # Check to make sure it is a valid address.
        self.validateaddress(address)

        return address

    def validateaddress(self, address):
        if address < 0 or address > self.maxmemory:
            print("Invalid address: ${0:04X}".format(address))
            return False

        else:
            return True

    def converttobcd(self, value):

        # Mask LSbit to see if that digit is greater than 9.
        if value & 0x0F > 0x09:
            # Roll the digit.
            value += 0x06

        # Mast MSbit to see if that digit is greater than 9.
        if value & 0xF0 > 0x90:
            # Roll that digit.
            value += 0x60

        return value

    # endregion

    # region ALU Helpers
    def addvalues(self, val1, val2):

        # Do the math.
        result = val1 + val2 + self.getflag(Flags.CARRY)

        # Check to see if this is BCD mode.
        if self.getflag(Flags.DECIMAL):

            # Do the conversion to BCD.
            result = self.converttobcd(result)

            # Now check to see if we need to set carry.
            self.setflag(Flags.CARRY, (result > 0x99))

        else:

            # Set carry and overflow based on result.
            self.setflag(Flags.CARRY, (result > 0xFF))
            self.setflag(Flags.OVERFLOW, (val1 < 128 and val2 < 128 and result > 127))

        # Return the 2 byte result.
        return result & 0xFF

    def subtractvalues(self, val1, val2):

        # Do the math.
        result = val1 - val2 - self.getflag(Flags.CARRY)

        # Check to see if this is BCD mode.
        if self.getflag(Flags.DECIMAL):

            # Do the conversion to BCD.
            result = self.converttobcd(result)

            # Now check to see if we need to set carry.
            self.setflag(Flags.CARRY, (result > 0x99))

        else:

            # Set carry and overflow based on result.
            self.setflag(Flags.CARRY, (result <= 0xFF))
            self.setflag(Flags.OVERFLOW, (val1 < 128 and val2 < 128 and result > 127))

        # Return the 2 byte result.
        return result & 0xFF

    # endregion

    # region Stack Helpers
    def pushstack8(self, value):

        # Push value to current stack pointer.
        self._memory.writebyte(self.sp, value)

        # Decrement stack pointer.
        self.sp -= 1

    def popstack8(self):

        # Increment the stack pointer.
        self.sp += 1

        # Return the value at this address.
        return self._memory.readbyte(self.sp)

    def stackpush16(self, value):

        # Push the first byte to stack pointer.
        self._memory.writebyte(self.sp, (value & 0xFF))

        # Push the high byte to the stack.
        self._memory.writebyte((self.sp - 1), ((value >> 8) & 0xFF))

        # Decrement the stack pointer
        self.sp -= 2

    def stackpop16(self):

        # Increment the stack pointer.
        self.sp += 2

        # Return the combined value of the stack pointer low byte + the high byte.
        return self._memory.readbyte(self.sp) + (0x100 * self._memory.readbyte(self.sp - 1))

    # endregion

    # region Flag Helpers
    def getflag(self, flag):

        return self.pf & flag

    def setflag(self, flag, value):

        if value:
            self.pf |= flag

        else:
            self.pf &= ~flag

    # endregion

    # region Opcode Handlers

    # region ADC
    def handleADCimmediate(self):

        # Check for valid address.
        if self.validateaddress(self.pc):
            # Update accumulator with result.
            self.a = self.addvalues(self.a, self._memory.readbyte(self.pc))

            # Update flags.
            self.setflag(Flags.ZERO, (self.a == 0))
            self.setflag(Flags.NEGATIVE, (self.a & 0x80))

            # Update program and cycle counters.
            self.pc += 1
            self.cy += 2

    def handleADCzeropage(self):

        # Check for valid address.
        if self.validateaddress(self.pc):
            # Update accumulator with result.
            self.a = self.addvalues(self.a, self._memory.readbyte(self.pc))

            # Update flags.
            self.setflag(Flags.ZERO, (self.a == 0))
            self.setflag(Flags.NEGATIVE, (self.a & 0x80))

            # Update program and cycle counters.
            self.pc += 1
            self.cy += 3

    def handleADCzeropagex(self):

        address = (self.pc + self.x) & 0xFF

        # Check for valid address.
        if self.validateaddress(address):
            # Update accumulator with result.
            self.a = self.addvalues(self.a, address)

            # Update flags.
            self.setflag(Flags.ZERO, (self.a == 0))
            self.setflag(Flags.NEGATIVE, (self.a & 0x80))

            # Update program and cycle counters.
            self.pc += 1
            self.cy += 4

    def handleADCabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Update accumulator with result.
        self.a = self.addvalues(self.a, val)

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update program and cycle counters.
        self.pc += 2
        self.cy += 4

    def handleADCabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Update accumulator with result.
        self.a = self.addvalues(self.a, val)

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update program and cycle counters.
        self.pc += 2
        self.cy += 4

    def handleADCabsolutey(self):

        # Get the address.
        address = self.calcuateaddress(False, self.y)

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Update accumulator with result.
        self.a = self.addvalues(self.a, val)

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update program and cycle counters.
        self.pc += 2
        self.cy += 4

    def handleADCindexedindirect(self):

        # Get the address.
        address = self.calcuateaddress(False, (self.pc + self.x))

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Update accumulator with result.
        self.a = self.addvalues(self.a, val)

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update program and cycle counters.
        self.pc += 2
        self.cy += 6

    def handleADCindirectindexed(self):

        # Get the address.
        address = self.calcuateaddress(False, (self.pc + self.y))

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Update accumulator with result.
        self.a = self.addvalues(self.a, val)

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update program and cycle counters.
        self.pc += 2
        self.cy += 5

    # endregion

    # region LDA
    def handleLDAimmediate(self):

        # Load the accumulator with value.
        self.a = self._memory.readbyte(self.pc)

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update program and cycle counters.
        self.pc += 1
        self.cy += 2

    # endregion

    # region CLC
    def handleCLC(self):

        # Clear flag value.
        self.setflag(Flags.CARRY, 0)

        # Update program and cycle counters.
        self.pc += 1
        self.cy += 2

    # endregion

    # region CLD
    def handleCLD(self):

        # Clear flag value.
        self.setflag(Flags.DECIMAL, 0)

        # Update program and cycle counters.
        self.pc += 1
        self.cy += 2

    # endregion

    # region CLI
    def handleCLI(self):

        # Clear flag value.
        self.setflag(Flags.INTERRUPT, 0)

        # Update program and cycle counters.
        self.pc += 1
        self.cy += 2

    # endregion

    # region CLV
    def handleCLV(self):

        # Clear flag value.
        self.setflag(Flags.OVERFLOW, 0)

        # Update program and cycle counters.
        self.pc += 1
        self.cy += 2

    # endregion

    # region PHA
    def handlePHA(self):

        # Push the accumulator onto the stack.
        self.pushstack8(self.a)

        # Update cycle counter.
        self.cy += 3

    # endregion

    # region PHP
    def handlePHP(self):

        # Push the processor flags onto the stack.
        self.pushstack8(self.pf)

        # Update cycle counter.
        self.cy += 3

    # endregion

    # region PLA
    def handlePLA(self):

        # Pop the value of the stack pointer to the accumulator.
        self.a = self.popstack8()

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update cycle counter.
        self.cy += 4

    #endregion

    # region PLP
    def handlePLP(self):

        # Set processor flags from stack value.
        self.pf = self.popstack8()

    #endregion

    # region SEC
    def handleSEC(self):

        # Clear flag value.
        self.setflag(Flags.CARRY, 1)

        # Update program and cycle counters.
        self.pc += 1
        self.cy += 2

    # endregion

    # region SED
    def handleSED(self):

        # Clear flag value.
        self.setflag(Flags.DECIMAL, 1)

        # Update program and cycle counters.
        self.pc += 1
        self.cy += 2

    # endregion

    # region SEI
    def handleSEI(self):

        # Clear flag value.
        self.setflag(Flags.INTERRUPT, 1)

        # Update program and cycle counters.
        self.pc += 1
        self.cy += 2

    # endregion

    # region STA
    def handleSTAzeropage(self):

        # Get address.
        address = self.calcuateaddress(True, 0)

        # Store accumulator value.
        self._memory.writebyte(address, self.a)

        # Update program and cycle counters.
        self.pc += 1
        self.cy += 3

    def handleSTAzeropagex(self):

        # Get address.
        address = self.calcuateaddress(True, self.x)

        # Store accumulator value.
        self._memory.writebyte(address, self.a)

        # Update program and cycle counters.
        self.pc += 1
        self.cy += 4

    def handleSTAabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Store accumulator value.
        self._memory.writebyte(address, self.a)

        # Update program and cycle counters.
        self.pc += 2
        self.cy += 4

    def handleSTAabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Store accumulator value.
        self._memory.writebyte(address, self.a)

        # Update program and cycle counters.
        self.pc += 2
        self.cy += 5

    def handleSTAabsolutey(self):

        # Get the address.
        address = self.calcuateaddress(False, self.y)

        # Store accumulator value.
        self._memory.writebyte(address, self.a)

        # Update program and cycle counters.
        self.pc += 2
        self.cy += 5

    # endregion

    # region STX
    def handleSTXzeropage(self):

        # Get address.
        address = self.calcuateaddress(True, 0)

        # Store accumulator value.
        self._memory.writebyte(address, self.x)

        # Update program and cycle counters.
        self.pc += 1
        self.cy += 3

    def handleSTXabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Store accumulator value.
        self._memory.writebyte(address, self.x)

        # Update program and cycle counters.
        self.pc += 2
        self.cy += 4

    # endregion

    # region STY
    def handleSTYzeropage(self):

        # Get address.
        address = self.calcuateaddress(True, 0)

        # Store accumulator value.
        self._memory.writebyte(address, self.y)

        # Update program and cycle counters.
        self.pc += 1
        self.cy += 3

    def handleSTYabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Store accumulator value.
        self._memory.writebyte(address, self.y)

        # Update program and cycle counters.
        self.pc += 2
        self.cy += 4

    # endregion

    # region TAX
    def handleTAX(self):

        # Copy accumulator to x register.
        self.x = self.a

        # Update flags.
        self.setflag(Flags.ZERO, (self.x == 0))
        self.setflag(Flags.NEGATIVE, (self.x & 0x80))

        # Update cycle counter.
        self.cy += 2

    # endregion

    # region TAY
    def handleTAY(self):

        # Copy accumulator to y register.
        self.y = self.a

        # Update flags.
        self.setflag(Flags.ZERO, (self.y == 0))
        self.setflag(Flags.NEGATIVE, (self.y & 0x80))

        # Update cycle counter.
        self.cy += 2

    # endregion

    # region TSX
    def handleTSX(self):

        # Copy stack pointer to x register.
        self.x = self._memory.readbyte(self.sp)

        # Update flags.
        self.setflag(Flags.ZERO, (self.y == 0))
        self.setflag(Flags.NEGATIVE, (self.y & 0x80))

        # Update cycle counter.
        self.cy += 2

    # endregion

    # region TXA
    def handleTXA(self):

        # Copy x register to accumulator.
        self.a = self.x

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update cycle counter.
        self.cy += 2

    # endregion

    # region TXS
    def handleTXS(self):

        # Copy x register to current stack pointer.
        self.sp = self.x

        # Update cycle counter.
        self.cy += 2

    # region TYA
    def handleTYA(self):

        # Copy y register to accumulator.
        self.a = self.y

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update cycle counter.
        self.cy += 2

    # endregion

    # endregion

    # region Instruction Set
    def loadinstructionset(self):
        self.instructions = {
            0x08: self.handlePHP,
            0x18: self.handleCLC,
            0x28: self.handlePLP,
            0x38: self.handleSEC,
            0x48: self.handlePHA,
            0x58: self.handleCLI,
            0x65: self.handleADCzeropage,
            0x68: self.handlePLA,
            0x69: self.handleADCimmediate,
            0x6D: self.handleADCabsolute,
            0x75: self.handleADCzeropagex,
            0x78: self.handleSEI,
            0x79: self.handleADCabsolutey,
            0x7D: self.handleADCabsolutex,
            0x84: self.handleSTYzeropage,
            0x85: self.handleSTAzeropage,
            0x86: self.handleSTXzeropage,
            0x8A: self.handleTXA,
            0x8C: self.handleSTYabsolute,
            0x8D: self.handleSTAabsolute,
            0x8E: self.handleSTXabsolute,
            0x95: self.handleSTAzeropagex,
            0x98: self.handleTYA,
            0x99: self.handleSTAabsolutey,
            0x9A: self.handleTXS,
            0x9D: self.handleSTAabsolutex,
            0xA8: self.handleTAY,
            0xA9: self.handleLDAimmediate,
            0xAA: self.handleTAX,
            0xB8: self.handleCLV,
            0xBA: self.handleTSX,
            0xD8: self.handleCLD,
            0xF8: self.handleSED
        }
    # endregion


class Flags(object):
    # Processor flags.
    NEGATIVE = 128
    OVERFLOW = 64
    UNUSED = 32
    BREAK = 16
    DECIMAL = 8
    INTERRUPT = 4
    ZERO = 2
    CARRY = 1


class Vectors(object):
    # Inturrupt address (NMI).
    NMI_ADDR_LOW = 0xfffa
    NMI_ADDR_HIGH = 0xfffb

    # Interrupt address (IRQ).
    IRQ_ADDR_LOW = 0xfffe
    IRQ_ADDR_HIGH = 0xffff

    # Reset address.
    RESET_ADDR_LOW = 0xfffc
    RESET_ADDR_HIGH = 0xfffd
