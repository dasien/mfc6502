from datetime import datetime
from memory import Memory
from mfcbase import MFCBase


class Processor(MFCBase):
    COMMANDS = """
    c = show cpu state
    e = execute next instruction
    f = continue (free run)
    h = print this list of commands
    m = dump memory contents (m@address ex. m@C004)
    p = print current instruction
    r = reset cpu
    s = dump stack
    t = halt program
    z = dump zero page
    """

    def __init__(self, infile, outfile, startaddr, includecounter, verbose, counterinfile):

        # These represent the program counter, a, x, y registers, stack pointer, processor flags, and a cycle counter.
        self.pc = 0x0000
        self.a = 0x00
        self.x = 0x00
        self.y = 0x00
        self.sp = 0x01FF
        self.pf = 0x00
        self.cy = 0

        # 64k RAM.
        self.maxmemory = 65536

        # The table of opcodes and their execution handlers.
        self.instructions = None

        # TODO: write information to output file.
        self.verbose = verbose

        # The end address of the loaded program.
        self.endaddress = 0

        # Flag to keep stepping through program (for debugging).
        self.nextstep = True

        # Flag to switch off command request (for debugging).
        self.stopbetweensteps = True

        # Load the allowable instructions.
        self.loadinstructionset()

        # Superclass init.
        super(Processor, self).__init__(infile, outfile, startaddr, includecounter, counterinfile)

        # Initialize memory (64k).
        self._memory = Memory(self.maxmemory)

        # Parse the input file.
        self.parse()

        # Load program into memory.
        self.endaddress = self.loadmemory(startaddr, self.sourcelines)

        # Set the program counter.
        self.pc = startaddr

    # region CPU Control

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
                  (format(str(self._memory.readbyte(addrlow)), '02X'),
                   format(str(self._memory.readbyte(addrhigh)), '02X')))
            return False

    def run(self, singlestep):

        # Assign the single step value.
        self.stopbetweensteps = singlestep

        # Begin message.
        self.writeheadermessage()

        # Loop through the code that is loaded in memory.
        while self.pc <= self.endaddress and self.nextstep:

            # Check to see if we are in free run mode.
            if self.stopbetweensteps:

                # Show the interactive debugger.
                self.showdebugger()

            # We are in free run mode.
            else:

                # Execute the next operation.
                self.executestep()

        # End message.
        self.writefootermessage()

    def executestep(self):

        # Fetch the first instruction.
        opcode = self._memory.readbyte(self.pc)

        # Get the command from the supported opcodes.
        instruction = self.instructions[opcode]

        # Increment program counter.
        self.pc += 1

        # Execute instruction.
        instruction()

    def showdebugger(self):

        # Get input from user.
        command = input("Enter Debugger Command (h for list of commands):").lower()

        # Process user command.
        if command[0] == 'c':
            # Print CPU state.
            self.showcpustate()

        elif command[0] == 'e':
            # Execute steps stopping between steps.
            self.executestep()

        elif command[0] == 'f':
            # Switch to free run mode.
            self.stopbetweensteps = False

        elif command[0] == 'h':
            # Print list of commands.
            print(self.COMMANDS)

        elif command[0] == 'm':
            # Get the address.
            addr = int(command[2:], 16)

            # Print the value of that address.
            print("Value at address %04x is %02x" % (addr, self._memory.readbyte(addr)))

        elif command[0] == 'p':
            # Get the current byte.
            opcode = self._memory.readbyte(self.pc)

            # Print the opcode.
            print("Current opcode: %02x" % opcode)

        elif command[0] == 's':
            # Print stack memory.
            self.dumpstack()

        elif command[0] == 't':
            # End execution.
            self.nextstep = False

        elif command[0] == 'z':
            # Print zero page memory.
            self.dumpzeropage()

    def showcpustate(self):

        # Get string versions of the byte values.
        str_pc = self.twobytestostring(self.pc)
        str_a = self.onebytetostring(self.a)
        str_x = self.onebytetostring(self.x)
        str_y = self.onebytetostring(self.y)
        str_sp = self.onebytetostring(self.sp & 0xFF)
        str_pf = self.onebytetostring(self.pf)

        print("PC:" + str_pc + " A:" + str_a + " X:" + str_x + " Y:" + str_y + " SP:" + str_sp + " Flags:" + str_pf +
              " CPU Cycles:" + str(self.cy))

    def dumpzeropage(self):

        # Print the zero page memory contents.
        self._memory.dump(0x00, 0xFF)

    def dumpstack(self):

        # Print stack contents.
        self._memory.dump(0x0100, 0xFF)

    def loadmemory(self, startaddress, data):

        # Load the data into memory.
        return self._memory.load(startaddress, data, self.includecounter)

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
            address = (self._memory.readbyte(self.pc) + offset) & 0xFF

        else:
            # Calculate the correct address.
            address = self._memory.readbyte(self.pc) + (0x100 * self._memory.readbyte(self.pc + 1)) + offset

        # Check to make sure it is a valid address.
        self.validateaddress(address)

        return address

    # TODO: Need to calculate accurate cycle times for calculations that cross page boundries.
    def calculaterelativeaddress(self, address):

        # First increment the address.  This is because relative address is PC + 1.
        address += 1

        # If the address is less than 128, just return it, otherwise subtract 256 from it and return it.
        return address if address < 0x80 else address - 0x100

    # TODO: Need to calculate accurate cycle times for calculations that cross page boundries.
    def calculateindexedaddress(self, offset):

        # This holds any additional cycle timing that needs to be added due to page boundry crossing.
        addcycle = 0

        # Calculate the address as base + offset to get first byte.
        lowbyte = (self._memory.readbyte(self.pc) + offset) & 0xFF

        # Check to see if we wrapped zero page (for additional processor cycle)
        if lowbyte < offset:
            # Increase the cycle offset.
            addcycle = 1

        # Now get the high byte.
        address = lowbyte + (0x100 * self._memory.readbyte(lowbyte + 1))

        # Check to see if this is valid.
        self.validateaddress(address)

        return address, addcycle

    # TODO: Need to calculate accurate cycle times for calculations that cross page boundries.
    def calculateindirectaddress(self, offset):

        # This holds any additional cycle timing that needs to be added due to page boundry crossing.
        addcycle = 0

        # Calculate the address as base + offset to get first byte.
        lowbyte = self._memory.readbyte(self.pc) & 0xFF

        # Check to see if we wrapped zero page (for additional processor cycle)
        if lowbyte < offset:
            # Increase the cycle offset.
            addcycle = 1

        # Now get the high byte.
        address = (lowbyte + (0x100 * self._memory.readbyte(lowbyte + 1))) + offset

        # Check to see if this is valid.
        self.validateaddress(address)

        return address, addcycle

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

        # Do the math A+M+C.
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

        # Do the math A-M-(1-C).
        result = val1 - val2 - (1 - self.getflag(Flags.CARRY))

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

    def comparevalues(self, val1, val2):

        # Set flags.
        self.setflag(Flags.CARRY, (val1 >= val2))
        self.setflag(Flags.ZERO, (val1 == val2))
        self.setflag(Flags.NEGATIVE, (val1 & 0x80))

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

    def pushstack16(self, value):

        # Push the first byte to stack pointer.
        self._memory.writebyte(self.sp, (value & 0xFF))

        # Push the high byte to the stack.
        self._memory.writebyte((self.sp - 1), ((value >> 8) & 0xFF))

        # Decrement the stack pointer
        self.sp -= 2

    def popstack16(self):

        # Increment the stack pointer.
        self.sp += 2

        # Return the combined value of the stack pointer low byte + the high byte.
        value = self._memory.readbyte(self.sp) + (0x100 * self._memory.readbyte(self.sp - 1))

        return value

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

        # Perform operation.
        self.handleADCbase(self.pc, 1, 2)

    def handleADCzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleADCbase(address, 1, 3)

    def handleADCzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleADCbase(address, 1, 4)

    def handleADCabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleADCbase(address, 2, 4)

    def handleADCabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleADCbase(address, 2, 4)

    def handleADCabsolutey(self):

        # Get the address.
        address = self.calcuateaddress(False, self.y)

        # Perform operation.
        self.handleADCbase(address, 2, 4)

    def handleADCindexedindirect(self):

        # Get the address.
        address, cycle = self.calculateindexedaddress(self.x)

        # Perform operation.
        self.handleADCbase(address, 1, 6)

    def handleADCindirectindexed(self):

        # Get the address.
        address, cycle = self.calculateindirectaddress(self.y)

        # Perform operation.
        self.handleADCbase(address, 1, (5 + cycle))

    def handleADCbase(self, address, pcoffset, cycles):

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Update accumulator with result.
        self.a = self.addvalues(self.a, val)

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region AND
    def handleANDimmediate(self):

        # Perform operation.
        self.handleANDbase(self.pc, 1, 2)

    def handleANDzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleANDbase(address, 1, 3)

    def handleANDzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleANDbase(address, 1, 4)

    def handleANDabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleANDbase(address, 2, 4)

    def handleANDabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleANDbase(address, 2, 4)

    def handleANDabsolutey(self):

        # Get the address.
        address = self.calcuateaddress(False, self.y)

        # Perform operation.
        self.handleANDbase(address, 2, 4)

    def handleANDindexedindirect(self):

        # Get the address.
        address, cycle = self.calculateindexedaddress(self.x)

        # Perform operation.
        self.handleANDbase(address, 2, 6)

    def handleANDindirectindexed(self):

        # Get the address.
        address, cycle = self.calculateindirectaddress(self.y)

        # Perform operation.
        self.handleANDbase(address, 2, (5 + cycle))

    def handleANDbase(self, address, pcoffset, cycles):

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Update accumulator with result.
        self.a &= val

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region ASL
    def handleASLaccumulator(self):

        # Take the high bit of value and set it to Carry flag.
        self.setflag(Flags.CARRY, (self.a & 0x80))

        # Rotate the value to the left << one place.  Bit 0 is set to 0.
        self.a = (self.a << 1) & 0xFE

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update cycle counter.
        self.cy += 2

    def handleASLzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleASLbase(address, 1, 5)

    def handleASLzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleASLbase(address, 1, 6)

    def handleASLabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleASLbase(address, 2, 6)

    def handleASLabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleASLbase(address, 2, 7)

    def handleASLbase(self, address, pcoffset, cycles):

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Take the high bit of value and set it to Carry flag.
        self.setflag(Flags.CARRY, (self.a & 0x80))

        # Rotate the value to the left << one place.  Bit 0 is set to 0.
        val = (val << 1) & 0xFE

        # Write the value back to memory.
        self._memory.writebyte(address, val)

        # Update flags.
        self.setflag(Flags.ZERO, (val == 0))
        self.setflag(Flags.NEGATIVE, (val & 0x80))

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region BCC
    def handleBCC(self):

        # Check to see if the carry flag is clear.
        if self.getflag(Flags.CARRY):

            # Update program and cycle counters.
            self.pc += 1
            self.cy += 2

        else:

            # Get address.
            address = self.calcuateaddress(True, 0)

            # Calculate new pc location.
            self.pc += self.calculaterelativeaddress(address)

            # Update cycle counter.
            self.cy += 3

    # endregion

    # region BCS
    def handleBCS(self):

        # Check to see if the carry flag is set.
        if self.getflag(Flags.CARRY):

            # Get address.
            address = self.calcuateaddress(True, 0)

            # Calculate new pc location.
            self.pc += self.calculaterelativeaddress(address)

            # Update cycle counter.
            self.cy += 3

        else:

            # Update program and cycle counters.
            self.pc += 1
            self.cy += 2

    # endregion

    # region BEQ
    def handleBEQ(self):

        # Check to see if the zero flag is set.
        if self.getflag(Flags.ZERO):

            # Get address.
            address = self.calcuateaddress(True, 0)

            # Calculate new pc location.
            self.pc += self.calculaterelativeaddress(address)

            # Update cycle counter.
            self.cy += 3

        else:

            # Update program and cycle counters.
            self.pc += 1
            self.cy += 2

    # endregion

    # region BIT
    def handleBITzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleBITbase(address, 1, 3)

    def handleBITabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleBITbase(address, 2, 4)

    def handleBITbase(self, address, pcoffset, cycles):

        # Perform and on accumulator and value in memory.
        result = self.a & self._memory.readbyte(address)

        # Set flags according to result. Negative flag gets bit 7 if set, and overflow gets bit 6 if set.
        self.setflag(Flags.ZERO, (result == 0))
        self.setflag(Flags.NEGATIVE, (result & 0x80))
        self.setflag(Flags.OVERFLOW, (result & 0x40))

    # endregion

    # region BMI
    def handleBMI(self):

        # Check to see if the negative flag is set.
        if self.getflag(Flags.NEGATIVE):

            # Get address.
            address = self.calcuateaddress(True, 0)

            # Calculate new pc location.
            self.pc += self.calculaterelativeaddress(address)

            # Update cycle counter.
            self.cy += 3

        else:

            # Update program and cycle counters.
            self.pc += 1
            self.cy += 2

    # endregion

    # region BNE
    def handleBNE(self):

        # Check to see if the zero flag is clear.
        if self.getflag(Flags.ZERO):

            # Update program and cycle counters.
            self.pc += 1
            self.cy += 2

        else:

            # Get address.
            address = self.calcuateaddress(True, 0)

            # Calculate new pc location.
            self.pc += self.calculaterelativeaddress(address)

            # Update cycle counter.
            self.cy += 3

    # endregion

    # region BPL
    def handleBPL(self):

        # Check to see if the negative flag is clear.
        if self.getflag(Flags.NEGATIVE):

            # Update program and cycle counters.
            self.pc += 1
            self.cy += 2

        else:

            # Get address.
            address = self.calcuateaddress(True, 0)

            # Calculate new pc location.
            self.pc += self.calculaterelativeaddress(address)

            # Update cycle counter.
            self.cy += 3

    # endregion

    # region BRK
    def handleBRK(self):

        # Increment program counter.
        self.pc += 2

        # Set break flag.
        self.setflag(Flags.BREAK, 1)

        # Store the pc on the stack.
        self.pushstack16(self.pc)

        # Store the pf on the stack.
        self.pushstack8(self.pf)

        # Set the inturrupt flag.
        self.setflag(Flags.INTERRUPT, 1)

        # Load the pc with the inturrupt address vector contents.
        self.pc = self._memory.readtwobytes(Vectors.IRQ_ADDR_LOW)

        # Enter debugger.
        self.showdebugger()

    # endregion

    # region BVC
    def handleBVC(self):

        # Check to see if the overflow flag is clear.
        if self.getflag(Flags.OVERFLOW):

            # Update program and cycle counters.
            self.pc += 1
            self.cy += 2

        else:

            # Get address.
            address = self.calcuateaddress(True, 0)

            # Calculate new pc location.
            self.pc += self.calculaterelativeaddress(address)

            # Update cycle counter.
            self.cy += 3

    # endregion

    # region BVS
    def handleBVS(self):

        # Check to see if the overflow flag is set.
        if self.getflag(Flags.OVERFLOW):

            # Get address.
            address = self.calcuateaddress(True, 0)

            # Calculate new pc location.
            self.pc += self.calculaterelativeaddress(address)

            # Update cycle counter.
            self.cy += 3

        else:

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

    # region CMP
    def handleCMPimmediate(self):

        # Perform operation.
        self.handleCMPbase(self.pc, 1, 2)

    def handleCMPzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, self.pc)

        # Perform operation.
        self.handleCMPbase(address, 1, 3)

    def handleCMPzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleCMPbase(address, 1, 4)

    def handleCMPabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleCMPbase(address, 2, 4)

    def handleCMPabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleCMPbase(address, 2, 4)

    def handleCMPabsolutey(self):

        # Get the address.
        address = self.calcuateaddress(False, self.y)

        # Perform operation.
        self.handleCMPbase(address, 2, 4)

    def handleCMPindexedindirect(self):

        # Get the address.
        address, cycle = self.calculateindexedaddress(self.x)

        # Perform operation.
        self.handleCMPbase(address, 1, 6)

    def handleCMPindirectindexed(self):

        # Get the address.
        address, cycle = self.calculateindirectaddress(self.y)

        # Perform operation.
        self.handleCMPbase(address, 1, (5 + cycle))

    def handleCMPbase(self, address, pcoffset, cycles):

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Do the comparison between accumulator and value.
        self.comparevalues(self.a, val)

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region CPX
    def handleCPXimmediate(self):

        # Perform operation.
        self.handleCPXbase(self.pc, 1, 2)

    def handleCPXzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, self.pc)

        # Perform operation.
        self.handleCPXbase(address, 1, 3)

    def handleCPXabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleCPXbase(address, 2, 4)

    def handleCPXbase(self, address, pcoffset, cycles):

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Do the comparison between register and value.
        self.comparevalues(self.x, val)

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region CPY
    def handleCPYimmediate(self):

        # Perform operation.
        self.handleCPYbase(self.pc, 1, 2)

    def handleCPYzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, self.pc)

        # Perform operation.
        self.handleCPYbase(address, 1, 3)

    def handleCPYabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleCPYbase(address, 2, 4)

    def handleCPYbase(self, address, pcoffset, cycles):

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Do the comparison between register and value.
        self.comparevalues(self.y, val)

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region DEC
    def handleDECzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleDECbase(address, 1, 5)

    def handleDECzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleDECbase(address, 1, 6)

    def handleDECabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleDECbase(address, 2, 6)

    def handleDECabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleDECbase(address, 2, 7)

    def handleDECbase(self, address, pcoffset, cycles):

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Update value.
        val -= 1

        # Write the new value back.
        self._memory.writebyte(address, val)

        # Update flags.
        self.setflag(Flags.ZERO, (val == 0))
        self.setflag(Flags.NEGATIVE, (val & 0x80))

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region DEX
    def handleDEX(self):

        # Decrement the x register.
        self.x -= 1

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update cycle counters.
        self.cy += 2

    # endregion

    # region DEY
    def handleDEY(self):

        # Increment the y register.
        self.y -= 1

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update cycle counters.
        self.cy += 2

    # endregion

    # region EOR
    def handleEORimmediate(self):

        # Perform operation.
        self.handleEORbase(self.pc, 1, 2)

    def handleEORzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleEORbase(address, 1, 3)

    def handleEORzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleEORbase(address, 1, 4)

    def handleEORabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleEORbase(address, 2, 4)

    def handleEORabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleEORbase(address, 2, 4)

    def handleEORabsolutey(self):

        # Get the address.
        address = self.calcuateaddress(False, self.y)

        # Perform operation.
        self.handleEORbase(address, 2, 4)

    def handleEORindexedindirect(self):

        # Get the address.
        address, cycle = self.calculateindexedaddress(self.x)

        # Perform operation.
        self.handleEORbase(address, 2, 6)

    def handleEORindirectindexed(self):

        # Get the address.
        address, cycle = self.calculateindirectaddress(self.y)

        # Perform operation.
        self.handleEORbase(address, 2, (5 + cycle))

    def handleEORbase(self, address, pcoffset, cycles):

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Update accumulator with result.
        self.a ^= val

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update program EOR cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region INC
    def handleINCzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleINCbase(address, 1, 5)

    def handleINCzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleINCbase(address, 1, 6)

    def handleINCabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleINCbase(address, 2, 6)

    def handleINCabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleINCbase(address, 2, 7)

    def handleINCbase(self, address, pcoffset, cycles):

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Update value.
        val += 1

        # Write the new value back.
        self._memory.writebyte(address, val)

        # Update flags.
        self.setflag(Flags.ZERO, (val == 0))
        self.setflag(Flags.NEGATIVE, (val & 0x80))

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region INX
    def handleINX(self):

        # Increment the x register.
        self.x += 1

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update cycle counters.
        self.cy += 2

    # endregion

    # region INY
    def handleINY(self):

        # Increment the y register.
        self.y += 1

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update cycle counters.
        self.cy += 2

    # endregion

    # region JMP
    def handleJMPabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform Operation.
        self.handleJMPbase(address, 2, 3)

    def handleJMPindirect(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Use this to get the actual jump address.
        jumpaddress = self._memory.readbyte(address) + (0x100 * self._memory.readbyte(address + 1))

        # Perform Operation
        self.handleJMPbase(jumpaddress, 2, 5)

    def handleJMPbase(self, address, pcoffset, cycles):

        # Set the program counter to address.
        self.pc = address

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region JSR
    def handleJSR(self):

        # Push next instruction onto the stack.
        self.pushstack16(self.pc + 2)

        # Set pc to the address of subroutine.
        self.pc = self.calcuateaddress(False, 0)

        # Update cycle count.
        self.cy += 6

    # endregion

    # region LDA
    def handleLDAimmediate(self):

        # Perform operation.
        self.handleLDAbase(self.pc, 1, 2)

    def handleLDAzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleLDAbase(address, 1, 3)

    def handleLDAzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleLDAbase(address, 2, 4)

    def handleLDAabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleLDAbase(address, 2, 4)

    def handleLDAabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleLDAbase(address, 2, 4)

    def handleLDAabsolutey(self):

        # Get the address.
        address = self.calcuateaddress(False, self.y)

        # Perform operation.
        self.handleLDAbase(address, 2, 4)

    def handleLDAindexedindirect(self):

        # Get the address.
        address, cycle = self.calculateindexedaddress(self.x)

        # Perform operation.
        self.handleLDAbase(address, 2, 6)

    def handleLDAindirectindexed(self):

        # Get the address.
        address, cycle = self.calculateindirectaddress(self.y)

        # Perform operation.
        self.handleLDAbase(address, 2, (5 + cycle))

    def handleLDAbase(self, address, pcoffset, cycles):

        # Load the accumulator with value.
        self.a = self._memory.readbyte(address)

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region LDX
    def handleLDXimmediate(self):

        # Perform operation.
        self.handleLDXbase(self.pc, 1, 2)

    def handleLDXzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleLDXbase(address, 1, 3)

    def handleLDXzeropagey(self):

        # Get the address.
        address = self.calcuateaddress(True, self.y)

        # Perform operation.
        self.handleLDXbase(address, 1, 4)

    def handleLDXabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleLDXbase(address, 2, 4)

    def handleLDXabsolutey(self):

        # Get the address.
        address = self.calcuateaddress(False, self.y)

        # Perform operation.
        self.handleLDXbase(address, 2, 4)

    def handleLDXbase(self, address, pcoffset, cycles):

        # Load the x register with value.
        self.x = self._memory.readbyte(address)

        # Update flags.
        self.setflag(Flags.ZERO, (self.x == 0))
        self.setflag(Flags.NEGATIVE, (self.x & 0x80))

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region LDY
    def handleLDYimmediate(self):

        # Perform operation.
        self.handleLDYbase(self.pc, 1, 2)

    def handleLDYzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleLDYbase(address, 1, 3)

    def handleLDYzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleLDYbase(address, 1, 4)

    def handleLDYabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleLDYbase(address, 2, 4)

    def handleLDYabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleLDYbase(address, 2, 4)

    def handleLDYbase(self, address, pcoffset, cycles):

        # Load the x register with value.
        self.y = self._memory.readbyte(address)

        # Update flags.
        self.setflag(Flags.ZERO, (self.y == 0))
        self.setflag(Flags.NEGATIVE, (self.y & 0x80))

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region LSR
    def handleLSRaccumulator(self):

        # Take the low bit of value and set it to Carry flag.
        self.setflag(Flags.CARRY, (self.a & 0x01))

        # Rotate the value to the right >> one place.  Bit 7 is set to 0.
        self.a = (self.a >> 1) & 0x7F

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update cycle counter.
        self.cy += 2

    def handleLSRzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleLSRbase(address, 1, 5)

    def handleLSRzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleLSRbase(address, 1, 6)

    def handleLSRabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleLSRbase(address, 2, 6)

    def handleLSRabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleLSRbase(address, 2, 7)

    def handleLSRbase(self, address, pcoffset, cycles):

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Take the low bit of value and set it to Carry flag.
        self.setflag(Flags.CARRY, (val & 0x01))

        # Rotate the value to the right >> one place.  Bit 7 is set to 0.
        val = (val >> 1) & 0xFE

        # Write the value back to memory.
        self._memory.writebyte(address, val)

        # Update flags.
        self.setflag(Flags.ZERO, (val == 0))
        self.setflag(Flags.NEGATIVE, (val & 0x80))

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region NOP
    def handleNOP(self):

        # Update cycle counter.
        self.cy += 2

    # endregion

    # region ORA
    def handleORAimmediate(self):

        # Perform operation.
        self.handleORAbase(self.pc, 1, 2)

    def handleORAzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleORAbase(address, 1, 3)

    def handleORAzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleORAbase(address, 1, 4)

    def handleORAabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleORAbase(address, 2, 4)

    def handleORAabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleORAbase(address, 2, 4)

    def handleORAabsolutey(self):

        # Get the address.
        address = self.calcuateaddress(False, self.y)

        # Perform operation.
        self.handleORAbase(address, 2, 4)

    def handleORAindexedindirect(self):

        # Get the address.
        address, cycle = self.calculateindexedaddress(self.x)

        # Perform operation.
        self.handleORAbase(address, 2, 6)

    def handleORAindirectindexed(self):

        # Get the address.
        address, cycle = self.calculateindirectaddress(self.y)

        # Perform operation.
        self.handleORAbase(address, 2, (5 + cycle))

    def handleORAbase(self, address, pcoffset, cycles):

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Update accumulator with result.
        self.a |= val

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

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

    # region PHX
    def handlePHX(self):

        # Push the x register onto the stack.
        self.pushstack8(self.x)

        # Update cycle counter.
        self.cy += 3

    # endregion

    # region PHY
    def handlePHY(self):

        # Push the y register onto the stack.
        self.pushstack8(self.y)

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

    # endregion

    # region PLP
    def handlePLP(self):

        # Set processor flags from stack value.
        self.pf = self.popstack8()

    # endregion

    # region PLX
    def handlePLX(self):

        # Pop the value of the stack pointer to the x register.
        self.x = self.popstack8()

        # Update flags.
        self.setflag(Flags.ZERO, (self.x == 0))
        self.setflag(Flags.NEGATIVE, (self.x & 0x80))

        # Update cycle counter.
        self.cy += 4

    # endregion

    # region PLY
    def handlePLA(self):

        # Pop the value of the stack pointer to the y register.
        self.y = self.popstack8()

        # Update flags.
        self.setflag(Flags.ZERO, (self.y == 0))
        self.setflag(Flags.NEGATIVE, (self.y & 0x80))

        # Update cycle counter.
        self.cy += 4

    # endregion

    # region ROL
    def handleROLaccumulator(self):

        # Capture current CFlag
        ctmp = self.getflag(Flags.CARRY)

        # Take the high bit of value and set it to Carry flag.
        self.setflag(Flags.CARRY, (self.a & 0x80))

        # Rotate the value to the left << one place.  Bit 0 is set to the value of the old CFlag.
        self.a = ((self.a << 1) | (0x01 if ctmp else 0)) & 0xFF

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update cycle counter.
        self.cy += 2

    def handleROLzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleROLbase(address, 1, 5)

    def handleROLzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleROLbase(address, 1, 6)

    def handleROLabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleROLbase(address, 2, 6)

    def handleROLabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleROLbase(address, 2, 7)

    def handleROLbase(self, address, pcoffset, cycles):

        # Capture current CFlag
        ctmp = self.getflag(Flags.CARRY)

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Take the high bit of value and set it to Carry flag.
        self.setflag(Flags.CARRY, (self.a & 0x80))

        # Rotate the value to the left << one place.  Bit 0 is set to the value of the old CFlag.
        val = ((val << 1) | (0x01 if ctmp else 0)) & 0xFF

        # Write the value back to memory.
        self._memory.writebyte(address, val)

        # Update flags.
        self.setflag(Flags.ZERO, (val == 0))
        self.setflag(Flags.NEGATIVE, (val & 0x80))

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region ROR
    def handleRORaccumulator(self):

        # Capture current CFlag
        ctmp = self.getflag(Flags.CARRY)

        # Take the low bit of value and set it to Carry flag.
        self.setflag(Flags.CARRY, (self.a & 0x01))

        # Rotate the value to the right >> one place.  Bit 7 is set to the value of the old CFlag.
        self.a = (self.a >> 1) | (0x80 if ctmp else 0)

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update cycle counter.
        self.cy += 2

    def handleRORzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleRORbase(address, 1, 5)

    def handleRORzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleRORbase(address, 1, 6)

    def handleRORabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleRORbase(address, 2, 6)

    def handleRORabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleRORbase(address, 2, 7)

    def handleRORbase(self, address, pcoffset, cycles):

        # Capture current CFlag
        ctmp = self.getflag(Flags.CARRY)

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Take the low bit of value and set it to Carry flag.
        self.setflag(Flags.CARRY, (val & 0x01))

        # Rotate the value to the right >> one place.  Bit 7 is set to the value of the old CFlag.
        val = (val >> 1) | (0x80 if ctmp else 0)

        # Write the value back to memory.
        self._memory.writebyte(address, val)

        # Update flags.
        self.setflag(Flags.ZERO, (val == 0))
        self.setflag(Flags.NEGATIVE, (val & 0x80))

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region RTI
    def handleRTI(self):

        # Restore the stack pointer from stack.
        self.pf = self.popstack8()

        # Restor the program counter form stack.
        self.pc = self.popstack16()

    # endregion

    # region RTS
    def handleRTS(self):

        # Restore the pc from stack.
        self.pc = self.popstack16()

    # endregion

    # region SBC
    def handleSBCimmediate(self):

        # Perform operation.
        self.handleSBCbase(self.pc, 1, 2)

    def handleSBCzeropage(self):

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleSBCbase(address, 1, 3)

    def handleSBCzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleSBCbase(address, 1, 4)

    def handleSBCabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleSBCbase(address, 2, 4)

    def handleSBCabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleSBCbase(address, 2, 4)

    def handleSBCabsolutey(self):

        # Get the address.
        address = self.calcuateaddress(False, self.y)

        # Perform operation.
        self.handleSBCbase(address, 2, 4)

    def handleSBCindexedindirect(self):

        # Get the address.
        address, cycle = self.calculateindexedaddress(self.x)

        # Perform operation.
        self.handleSBCbase(address, 1, 6)

    def handleSBCindirectindexed(self):

        # Get the address.
        address, cycle = self.calculateindirectaddress(self.y)

        # Perform operation.
        self.handleSBCbase(address, 1, (5 + cycle))

    def handleSBCbase(self, address, pcoffset, cycles):

        # Get the value at that address.
        val = self._memory.readbyte(address)

        # Update accumulator with result.
        self.a = self.subtractvalues(self.a, val)

        # Update flags.
        self.setflag(Flags.ZERO, (self.a == 0))
        self.setflag(Flags.NEGATIVE, (self.a & 0x80))

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

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

        # Get the address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleSTAbase(address, 1, 3)

    def handleSTAzeropagex(self):

        # Get the address.
        address = self.calcuateaddress(True, self.x)

        # Perform operation.
        self.handleSTAbase(address, 1, 4)

    def handleSTAabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleSTAbase(address, 2, 4)

    def handleSTAabsolutex(self):

        # Get the address.
        address = self.calcuateaddress(False, self.x)

        # Perform operation.
        self.handleSTAbase(address, 2, 5)

    def handleSTAabsolutey(self):

        # Get the address.
        address = self.calcuateaddress(False, self.y)

        # Perform operation.
        self.handleSTAbase(address, 2, 5)

    def handleSTAindexedindirect(self):

        # Get the address.
        address, cycle = self.calculateindexedaddress(self.x)

        # Perform operation.
        self.handleSTAbase(address, 1, 6)

    def handleSTAindirectindexed(self):

        # Get the address.
        address, cycle = self.calculateindirectaddress(self.y)

        # Perform operation.
        self.handleSTAbase(address, 1, 6)

    def handleSTAbase(self, address, pcoffset, cycles):

        # Store the accumulator with value.
        self._memory.writebyte(address, self.a)

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region STX
    def handleSTXzeropage(self):

        # Get address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleSTXbase(address, 1, 3)

    def handleSTXzeropagey(self):

        # Get address.
        address = self.calcuateaddress(True, self.y)

        # Perform operation.
        self.handleSTXbase(address, 1, 4)

    def handleSTXabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleSTXbase(address, 2, 4)

    def handleSTXbase(self, address, pcoffset, cycles):

        # Store value to x register.
        self._memory.writebyte(address, self.x)

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

    # endregion

    # region STY
    def handleSTYzeropage(self):

        # Get address.
        address = self.calcuateaddress(True, 0)

        # Perform operation.
        self.handleSTYbase(address, 1, 3)

    def handleSTYzeropagex(self):

        # Get address.
        address = self.calcuateaddress(True, self.y)

        # Perform operation.
        self.handleSTYbase(address, 1, 4)

    def handleSTYabsolute(self):

        # Get the address.
        address = self.calcuateaddress(False, 0)

        # Perform operation.
        self.handleSTYbase(address, 2, 4)

    def handleSTYbase(self, address, pcoffset, cycles):

        # Store value to x register.
        self._memory.writebyte(address, self.y)

        # Update program and cycle counters.
        self.pc += pcoffset
        self.cy += cycles

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

    # endregion

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
            0x00: self.handleBRK,
            0x01: self.handleORAindexedindirect,
            0x05: self.handleORAzeropage,
            0x06: self.handleASLzeropage,
            0x08: self.handlePHP,
            0x09: self.handleORAimmediate,
            0x0A: self.handleASLaccumulator,
            0x0D: self.handleORAabsolute,
            0x0E: self.handleASLabsolute,
            0x10: self.handleBPL,
            0x11: self.handleORAindirectindexed,
            0x15: self.handleORAzeropagex,
            0x16: self.handleASLzeropagex,
            0x18: self.handleCLC,
            0x19: self.handleORAabsolutey,
            0x1D: self.handleORAabsolutex,
            0x1E: self.handleASLabsolutex,
            0x20: self.handleJSR,
            0x21: self.handleANDindexedindirect,
            0x24: self.handleBITzeropage,
            0x25: self.handleANDzeropage,
            0x26: self.handleROLzeropage,
            0x28: self.handlePLP,
            0x29: self.handleANDimmediate,
            0x2A: self.handleROLaccumulator,
            0x2C: self.handleBITabsolute,
            0x2D: self.handleANDabsolute,
            0x2E: self.handleROLabsolute,
            0x30: self.handleBMI,
            0x31: self.handleANDindirectindexed,
            0x35: self.handleANDzeropagex,
            0x36: self.handleROLzeropagex,
            0x38: self.handleSEC,
            0x39: self.handleANDabsolutey,
            0x3D: self.handleANDabsolutex,
            0x3E: self.handleROLabsolutex,
            0x41: self.handleEORindexedindirect,
            0x45: self.handleEORzeropage,
            0x46: self.handleLSRzeropage,
            0x48: self.handlePHA,
            0x49: self.handleEORimmediate,
            0x4A: self.handleLSRaccumulator,
            0x4C: self.handleJMPabsolute,
            0x4D: self.handleEORabsolute,
            0x4E: self.handleLSRabsolute,
            0x50: self.handleBVC,
            0x51: self.handleEORindirectindexed,
            0x55: self.handleEORzeropagex,
            0x56: self.handleLSRzeropagex,
            0x58: self.handleCLI,
            0x59: self.handleEORabsolutey,
            0x5A: self.handlePHY,
            0x5D: self.handleEORabsolutex,
            0x5E: self.handleLSRabsolutex,
            0x60: self.handleRTS,
            0x61: self.handleADCindexedindirect,
            0x65: self.handleADCzeropage,
            0x66: self.handleRORzeropage,
            0x68: self.handlePLA,
            0x69: self.handleADCimmediate,
            0x6A: self.handleRORaccumulator,
            0x6C: self.handleJMPindirect,
            0x6D: self.handleADCabsolute,
            0x6E: self.handleRORabsolute,
            0x70: self.handleBVS,
            0x71: self.handleADCindirectindexed,
            0x75: self.handleADCzeropagex,
            0x76: self.handleRORzeropagex,
            0x78: self.handleSEI,
            0x79: self.handleADCabsolutey,
            0x7A: self.handlePLY,
            0x7D: self.handleADCabsolutex,
            0x7E: self.handleRORabsolutex,
            0x81: self.handleSTAindexedindirect,
            0x84: self.handleSTYzeropage,
            0x85: self.handleSTAzeropage,
            0x86: self.handleSTXzeropage,
            0x88: self.handleDEY,
            0x8A: self.handleTXA,
            0x8C: self.handleSTYabsolute,
            0x8D: self.handleSTAabsolute,
            0x8E: self.handleSTXabsolute,
            0x90: self.handleBCC,
            0x91: self.handleSTAindirectindexed,
            0x94: self.handleSTYzeropagex,
            0x95: self.handleSTAzeropagex,
            0x96: self.handleSTXzeropagey,
            0x98: self.handleTYA,
            0x99: self.handleSTAabsolutey,
            0x9A: self.handleTXS,
            0x9D: self.handleSTAabsolutex,
            0xA0: self.handleLDYimmediate,
            0xA1: self.handleLDAindexedindirect,
            0xA2: self.handleLDXimmediate,
            0xA4: self.handleLDYzeropage,
            0xA5: self.handleLDAzeropage,
            0xA6: self.handleLDXzeropage,
            0xA8: self.handleTAY,
            0xA9: self.handleLDAimmediate,
            0xAA: self.handleTAX,
            0xAC: self.handleLDYabsolute,
            0xAD: self.handleLDAabsolute,
            0xAE: self.handleLDXabsolute,
            0xB0: self.handleBCS,
            0xB1: self.handleLDAindirectindexed,
            0xB4: self.handleLDYzeropagex,
            0xB5: self.handleLDAzeropagex,
            0xB6: self.handleLDXzeropagey,
            0xB8: self.handleCLV,
            0xB9: self.handleLDAabsolutey,
            0xBA: self.handleTSX,
            0xBC: self.handleLDYabsolutex,
            0xBD: self.handleLDAabsolutex,
            0xBE: self.handleLDXabsolutey,
            0xC0: self.handleCPYimmediate,
            0xC1: self.handleCMPindexedindirect,
            0xC4: self.handleCPYzeropage,
            0xC5: self.handleCMPzeropage,
            0xC6: self.handleDECzeropage,
            0xC8: self.handleINY,
            0xC9: self.handleCMPimmediate,
            0xCA: self.handleDEX,
            0xCC: self.handleCPYabsolute,
            0xCD: self.handleCMPabsolute,
            0xCE: self.handleDECabsolute,
            0xD0: self.handleBNE,
            0xD1: self.handleCMPindirectindexed,
            0xD5: self.handleCMPzeropagex,
            0xD6: self.handleDECzeropagex,
            0xD8: self.handleCLD,
            0xD9: self.handleCMPabsolutey,
            0xDA: self.handlePHX,
            0xDD: self.handleCMPabsolutex,
            0xDE: self.handleDECabsolutex,
            0xE0: self.handleCPXimmediate,
            0xE1: self.handleSBCindexedindirect,
            0xE4: self.handleCPXzeropage,
            0xE5: self.handleSBCzeropage,
            0xE6: self.handleINCzeropage,
            0xE8: self.handleINX,
            0xE9: self.handleSBCimmediate,
            0xEA: self.handleNOP,
            0xEC: self.handleCPXabsolute,
            0xED: self.handleSBCabsolute,
            0xEE: self.handleINCabsolute,
            0xF0: self.handleBEQ,
            0xF1: self.handleSBCindirectindexed,
            0xF5: self.handleSBCzeropagex,
            0xF6: self.handleINCzeropagex,
            0xF8: self.handleSED,
            0xF9: self.handleSBCabsolutey,
            0xFA: self.handlePLX,
            0xFD: self.handleSBCabsolutex,
            0xFE: self.handleINCabsolutex
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
