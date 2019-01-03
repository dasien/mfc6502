class AssemblerInstruction(object):

    def __init__(self, immediate, zp, zpx, zpy, absolute, absx, absy, indirect, indx, indy, accumulator, relative, implied):

        # Assign values
        self.__immediate = immediate
        self.__zp = zp
        self.__zpx = zpx
        self.__zpy = zpy
        self.__absolute = absolute
        self.__absx = absx
        self.__absy = absy
        self.__indirect = indirect
        self.__indx = indx
        self.__indy = indy
        self.__accumulator = accumulator
        self.__relative = relative
        self.__implied = implied

    def gethexvalueandlength(self, opcode, operand):

        # The return value.
        hexcode = None
        length = 0

        # Check for implied addressing.
        if operand is None:
            hexcode = self.__implied
            length = 1

        # Deal with branch instructions.
        elif opcode in ["BRL", "BMI", "BVC", "BVS", "BCC", "BCS", "BNE", "BEQ"]:
            hexcode = self.__relative
            length = 2

        # Check to see if this is immediate.
        elif operand[0] == "#" or operand[0:2] == "#$":
            hexcode = self.__immediate
            length = 2

        # Check for zero page.
        elif operand[0] == "$" and len(operand) == 3:
            hexcode = self.__zp
            length = 2

        # This can be either zero page or absolute (two byte)
        elif operand[0] == "$" and len(operand) == 5:
            hexcode = self.__absolute
            length = 3

            # Check for zero page, x.
            if operand[3:5] == ",X":
                hexcode = self.__zpx
                length = 2

            # Check for zero page, x.
            if operand[3:5] == ",Y":
                hexcode = self.__zpy
                length = 2

        # Check for absolute with x or y.
        elif operand[0] == "$" and len(operand) == 7:

            length = 3

            # Check for absolute, x.
            if operand[5:7] == ",X":
                hexcode = self.__absx

            # Check for absolute, y.
            if operand[5:7] == ",Y":
                hexcode = self.__absy

        # Check for indirect.
        elif operand[0] == "(" and len(operand) == 7:
            hexcode = self.__indirect
            length = 3

            # Check for indirect, x.
            if operand[4:7] == ",X)":
                hexcode = self.__indx
                length = 2

            # Check for indirect, y.
            if operand[4:7] == "),Y":
                hexcode = self.__indy
                length = 2

        # Check for accumumlator.
        elif operand[0] == "A":
            hexcode = self.__accumulator
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
