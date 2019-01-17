

class MFCBase(object):

    def __init__(self, infile, outfile, startaddr=None, includecounter=False):

        self.__infile = infile
        self.__outfile = outfile
        self.__opcodes = dict()
        self.__sourcelines = list()
        self.__bytecount = 0
        self.__includecounter = includecounter

        if not startaddr:
            self.__pc = 0x1000
        else:
            self.__pc = startaddr

    def splitline(self, line):

        pos = 0

        # Trim line to remove tabs, etc.
        line = line.strip()

        # Convert line to upper case (in case the developer didn't).
        line = line.upper()

        # Split into parts based on spaces.
        lineparts = line.split()

        # Loop throught the line part list.
        for part in lineparts:

            # Check to see if we have an inline comment
            if part[0] == ";":

                # Remove from this token to the end of line
                del lineparts[pos:len(lineparts)]
                break

            else:
                # Increment position counter.
                pos += 1

        return lineparts

    def writeline(self, value):

        try:

            # Append a CR to the line.
            value += "\n"

            # Write line to output file.
            self.__outfile.write(value)

        except:
            raise Exception("Error writing file.")

    def parse(self):

        try:

            # Loop through file.
            for line in self.__infile:

                line = line.strip()

                # Check to see if this is a blank line.
                if not line.strip() or line[0] in ";":

                    # Skip the line.
                    continue

                else:

                    # Split the line up into parts.
                    lineparts = self.splitline(line)

                    # Loop through the line parts to make sure there are no trailing colons.
                    lineparts[0] = lineparts[0].rstrip(':')

                    # Add to source list.
                    self.__sourcelines.append(lineparts)

            # Report lines parsed.
            print("Finishing parsing %s source lines..." % len(self.__sourcelines))

        except:
            raise Exception("Error in parsing file.")

    @property
    def infile(self):
        return self.__infile

    @property
    def outfile(self):
        return self.__outfile

    @property
    def includecounter(self):
        return self.__includecounter

    @property
    def pc(self):
        return self.__pc

    @pc.setter
    def pc(self, value):
        self.__pc = value

    @property
    def sourcelines(self):
        return self.__sourcelines

    @sourcelines.setter
    def sourcelines(self, value):
        self.__sourcelines = value

    @property
    def opcodes(self):
        return self.__opcodes

    @opcodes.setter
    def opcodes(self, value):
        self.__opcodes = value

    @property
    def bytecount(self):
        return self.__bytecount

    @bytecount.setter
    def bytecount(self, value):
        self.__bytecount = value
