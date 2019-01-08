

class Memory(object):

    def __init__(self, maximum):

        # -1 means uninitialized memory.  64k allocated.
        self._memmap = [0] * maximum

    def readbyte(self, address):

        # Retrive value from memory address.
        return self._memmap[address]

    def writebyte(self, address, value):

        # Assign value to memory.
        self._memmap[address] = value

    def load(self, address, sourcelines):

        # The memory offset.
        offset = 0

        # Check to see that we have a valid start address.
        if (address is not None) and (-1 < address < 65535):

            # Loop through program.
            for data in sourcelines:

                # Loop through data.
                for value in data:

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

    def dump(self, address, length):

        stringtoprint = []
        factor = 0

        # Check to see that we have a valid start address.
        if (address is not None) and (-1 < address < 65535):

            # Loop through range.
            for cell in self._memmap[address:(address + length)]:

                # Check to see if this is a new line.
                if factor % 16 == 0:
                    # Print current row.
                    print(''.join(stringtoprint))

                    # Clear buffer.
                    stringtoprint.clear()

                    # Start a new row.
                    stringtoprint.append("%04x: %02x " % ((address + (16 * factor)), cell))

                else:
                    # Append value to current row.
                    stringtoprint.append("%02x " % cell)

                # Increment factor.
                factor += 1

