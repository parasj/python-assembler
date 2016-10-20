import argparse
import re


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
        (sym_table, contents) = self.build_sym_table(contents)
        contents = self.split_ops(contents)
        contents = self.substitute_symbols(contents, sym_table)
        print("\n".join(map(lambda x: str(x), contents)))
        bc = self.translate_asm(contents)
        return bc

    def read_and_clean_asm(self, filename):
        with open(filename, 'r') as f:
            data = f.readlines()
        data = map(lambda x: x.strip(), data)                   # strip whitespace
        data = map(lambda x: x.split(';', 1)[0], data)          # strip comments
        data = filter(lambda x: x is not None, data)            # filter empty lines
        data = filter(lambda x: len(x) > 0, data)               # filter empty lines
        return data

    def build_sym_table(self, lines):
        symbols = {}
        toks = map(self.tokenize_symbol_line, lines)

        annotated_toks = []

        pc = 0
        for n in range(0, len(toks)):
            (type, data) = toks[n]

            if type is "NAME":
                symbols[data[0]] = data[1]
            elif type is "ORIG":
                pc = data[0]
            elif type.startswith("LABEL"):
                symbols[data[0]] = pc

            if type is "WORD" or type.endswith("OP"):
                annotated_toks.append((pc, type, data))
                pc += 1

        print("PASS ONE: {}".format(str(symbols)))
        for l in annotated_toks:
            print("\t{:4d} {:10s} {}".format(l[0], l[1], l[2]))

        return symbols, annotated_toks

    def split_ops(self, contents):
        inst_re = re.compile(r'[\s,]+')
        for (pc, type, data) in contents:
            inst = filter(lambda x: len(x) > 0, inst_re.split(data[0]))
            yield (pc, type, inst)

    def substitute_symbols(self, contents, sym_table):
        for (pc, type, data) in contents:
            yield (pc, type, data)

    def translate_asm(self, sub_contents):
        return []

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
        regs = {"R{0}".format(i): i for i in range(0, 16)}
        regs.update({"A{0}".format(i): regs["R{0}".format(i)] for i in range(0, 3)})
        regs.update({"RV": regs["R3"]})
        regs.update({"T{0}".format(i): regs["R{0}".format(i + 4)] for i in range(0, 1)})
        regs.update({"S{0}".format(i): regs["R{0}".format(i + 6)] for i in range(0, 2)})
        regs.update({"GP": regs["R12"]})
        regs.update({"FP": regs["R13"]})
        regs.update({"SP": regs["R14"]})
        regs.update({"RA": regs["R15"]})
        return regs

    def build_op_table(self):
        # todo fill table
        return {"ADD": 0x00000000}

    def parse_literal(self, num):
        return int(num, 0)

    def tokenize_symbol_line(self, l):
        s = l.strip()
        m = re.match(r'^.NAME\s*(.*)\s*=\s*(.*)\s*$', s)
        if m:
            return "NAME", [m.group(1), self.parse_literal(m.group(2))]

        m = re.match(r'^.ORIG\s*(.*)\s*$', s)
        if m:
            return "ORIG", [self.parse_literal(m.group(1))]

        m = re.match(r'^.WORD.*', s)
        if m:
            return "WORD", []  # todo

        m = re.match(r'^\s*([^\s]+)\s*:\s*(.+)\s*$', s)
        if m:
            return "LABELOP", [m.group(1), m.group(2)]

        m = re.match(r'^\s*([^\s]+)\s*:\s*$', s)
        if m:
            return "LABEL", [m.group(1)]

        return "OP", [l]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', metavar="<input_file>", help="The input file to \
                        be assembled", required=True) # todo output_file
    args = parser.parse_args()

    assembler = Assembler()
    out = assembler.assemble(args.i)

if __name__ == "__main__":
    main()