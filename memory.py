class Memory(object):

    def __init__(self, maximum):

        # -1 means uninitialized memory.  64k allocated.
        self._memmap = [0] * maximum

    def readbyte(self, address):

        # Retrive value from memory address.
        return self._memmap[address]

    def readtwobytes(self, address):

        # Retrive the contents of address and address + 1.
        return self._memmap[address] + (0x100 * self._memmap[address + 1])

    def writebyte(self, address, value):

        # Assign value to memory.
        self._memmap[address] = value

    def load(self, address, sourcelines, counterinfile):

        # The memory offset.
        offset = 0

        # Check to see that we have a valid start address.
        if (address is not None) and (-1 < address < 65535):

            # Loop through program.
            for data in sourcelines:

                # Split into parts based on spaces.
                lineparts = data.split()

                # Loop through data.
                for idx, value in enumerate(lineparts):

                    # Check to see if we should skip the program counter.
                    if counterinfile is False or idx > 0:

                        # Convert to int.
                        intval = int(value, 16)

                        # Check to make sure we have a valid value.
                        if value is not None and -1 < intval < 256:

                            # Check to see if we have overflowed memory.
                            if address + offset < 65535:

                                # Load memory with data.
                                self._memmap[address + offset] = intval

                                # increment counter.
                                offset += 1

                            else:
                                print("ERROR: Memory overflow.")
                                break
                        else:
                            print("ERROR: Invalid value at address 0x" + str(self._memmap[address + offset]))
                            break
        else:
            print("ERROR: Invalid starting address 0x" + str(address))

        return address + offset

    def clear(self):

        # Clear out all memory.
        self._memmap = [0] * 65536

    def dump(self, address, length, verbose=False, output=None):

        stringtoprint = []
        factor = 0

        # Check to see that we have a valid start address.
        if (address is not None) and (-1 < address < 65535):

            # Loop through range.
            for cell in self._memmap[address:(address + length + 1)]:

                # Check to see if this is a new line.
                if factor % 16 == 0:

                    # Print current row.
                    print(''.join(stringtoprint))

                    # Check to see if we should be logging to file.
                    if verbose and output is not None:

                        # Append a CR to the line.
                        stringtoprint += "\n"

                        # Write line to output file.
                        output.write(stringtoprint)

                    # Clear buffer.
                    stringtoprint.clear()

                    # Start a new row.
                    stringtoprint.append("%04x: %02x " % ((address + factor), cell))

                else:
                    # Append value to current row.
                    stringtoprint.append("%02x " % cell)

                # Increment factor.
                factor += 1

            # Print the final row.
            print(''.join(stringtoprint))

            # Check to see if we should be logging to file.
            if verbose and output is not None:

                # Append a CR to the line.
                stringtoprint += "\n"

                # Write line to output file.
                output.write(stringtoprint)
