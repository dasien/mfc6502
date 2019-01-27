import argparse
from assembler import Assembler
from disassembler import Disassembler
from processor import Processor

app_version = "1.23"

parser = argparse.ArgumentParser(usage="%(prog)s -[adegv] -i infile -o outfile [-s 0xADDR] [-c]",
                                 description="6502 Assembler/Disassembler/Simulator")
parser.add_argument("-a", "--assemble", action="store_true", dest="assemble", default=False,
                    help="Assemble the code in infile and put the assembled code in outfile")
parser.add_argument("-d", "--disassemble", action="store_true", dest="disassemble", default=False,
                    help="Disassemble the code in infile and put the disassembled code in outfile")
parser.add_argument("-e", "--execute", action="store_true", dest="execute", default=False,
                    help="Execute the assembled code in infile.  The run results will be placed in outfile.")
parser.add_argument("-g", "--debug", action="store_true", dest="debug", default=False,
                    help="Debug the code in infile and put the debug output in outfile")
parser.add_argument("-v", "--version", action="version", version="%(prog)s " + app_version)
parser.add_argument("-i", "--infile", action="store", dest="infile",
                    help="The input file to be read")
parser.add_argument("-o", "--oputfile", action="store", dest="outfile",
                    help="The output file to be written")
parser.add_argument("-s", "--startaddress", action="store", dest="startaddr", default=None,
                    help="The start address in hex for the program.")
parser.add_argument("-c", "--counter", action="store_true", dest="counter", default=False,
                    help="Output counter as part of output file.")

args = parser.parse_args()

infile = args.infile
outfile = args.outfile
startaddr = args.startaddr
intval = None

try:
    # Try to read source file.
    infile = open(args.infile, mode='r')

    # Create output file.
    outfile = open(args.outfile, mode='w')

    # Check to see what the user is trying to do.
    if args.assemble:

        # Check to see if a start address was added.
        if args.startaddr:

            # Check to see if the address is valid.
            intval = int(args.startaddr, 16)

            if intval < 1 or intval > 65535:
                raise ValueError

        # Set up assembler.
        handler = Assembler(infile, outfile, intval, args.counter)

        # Assemble file.
        handler.assemble()

    if args.disassemble:

        # Check to see if a start address was added.
        if args.startaddr:

            # Check to see if the address is valid.
            intval = int(args.startaddr, 16)

            if intval < 1 or intval > 65535:
                raise ValueError

        # Set up disassembler.
        handler = Disassembler(infile, outfile, intval, args.counter)

        # Disassemble file.
        handler.disassemble()

    if args.execute or args.debug:

        # Check to see if a start address was added.
        if args.startaddr:

            # Check to see if the address is valid.
            intval = int(args.startaddr, 16)

            if intval < 1 or intval > 65535:
                raise ValueError

        # Set up processor.
        handler = Processor(infile, outfile, intval, args.counter, args.debug)

        # Execute code.
        handler.run(args.debug)
        handler.showcpustate()

    # Close the files.
    infile.close()
    outfile.close()

except FileNotFoundError:
    print('Error: File %s not found.' % args.infile)

except PermissionError:
    print('Error: You do not have permission to read/write files in that location.')

except IOError:
    print('Error: Unspecified IO error.')

except ValueError:
    print('Invalid start address or format or value.')
