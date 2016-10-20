import argparse


class Assembler():
    def __init__(self):
        self.reg_table = self.build_reg_table()
        self.op_table =  self.build_op_table()

    def assemble(self, filename):
        # 1. read in file
        # 2. make symbol tables
        # 3. substitute symbol table
        # 4. translate to bytecode

        contents = self.read_and_clean_asm(filename)
        sym_table = self.build_sym_table(contents)
        return ""

    def read_and_clean_asm(self, filename):
        with open(filename, 'r') as f:
            data = f.readlines()
        data = map(lambda x: x.strip(), data)                   # strip whitespace
        data = filter(lambda x: not x.startswith(';'), data)    # filter comments
        data = filter(lambda x: len(x) > 0, data)               # filter empty lines
        return data

    def build_sym_table(self, lines):
        return {}

    ###
    # R0..R3 are also A0..A3 (function arguments, caller saved)
    # R3 is also RV (return value, caller saved)
    # R4..R5 are also T0..T1 (temporaries, caller saved)
    # R6..R8 are also S0..S2 (callee-saved values)
    # R9 reserved for assembler use
    # R10..R11 reserved for system use (we'll see later for what)
    # R12 is GP (global pointer)
    # R13 is FP (frame pointer)
    # R14 is SP (stack pointer), Stack grows down, SP points to lowest in-use address
    # R15 is RA (return address)
    ###
    def build_reg_table(self):
        regs = {"R%d".format(i): i for i in range(0, 15)}
        regs = regs.update({"A%d".format(i): regs["R%d".format(i)] for i in range(0, 3)})
        regs = regs.update({"RV": regs["R3"]})
        regs = regs.update({"T%d".format(i): regs["R%d".format(i + 4)] for i in range(0, 1)})
        regs = regs.update({"S%d".format(i): regs["R%d".format(i + 6)] for i in range(0, 2)})
        regs = regs.update({"GP": regs["R12"]})
        regs = regs.update({"FP": regs["R13"]})
        regs = regs.update({"SP": regs["R14"]})
        regs = regs.update({"RA": regs["R15"]})
        return regs

    def build_op_table(self):
        # todo fill table
        return {"ADD": 0x00000000}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', metavar="<input_file>", help="The input file to \
                        be assembled", required=True) # todo output_file
    args = parser.parse_args()

    assembler = Assembler()
    out = assembler.assemble(args.i)

if __name__ == "__main__":
    main()