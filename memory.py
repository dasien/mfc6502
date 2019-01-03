

class Memory(object):

    def __init__(self, max):

        # -1 means uninitialized memory.  64k allocated.
        self._memmap = [-1] * max

    def readbyte(self, address):

        # Retrive value from memory address.
        return self._memmap[address]

    def writebyte(self, address, value):

        # Assign value to memory.
        self._memmap[address] = value

    #TODO: handle overflow where address + the amount of data is greater than 65535
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

                        # Load memory with data.
                        self._memmap[address + offset] = intval

                        # increment counter.
                        offset += 1

                    else:
                        print("ERROR: Invalid value at address 0x" + str(self._memmap[address + offset]))
        else:
            print("ERROR: Invalid starting address 0x" + str(address))

    def clear(self):

        # Clear out all memory.
        self._memmap = [-1] * 65536

    def dump(self, address, range):
        pass