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
        print(sym_table['WIDTH'])
        contents = self.split_ops(contents)
        contents = self.substitute_symbols(contents, sym_table)
        contents = self.translate_asm(contents)
        for c in contents:
            print("{:5d} {:5s} {}".format(c[0], c[1], list(c[2])))
        return contents

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
        toks = list(map(self.tokenize_symbol_line, lines))

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

        return symbols, annotated_toks

    def split_ops(self, contents):
        inst_re = re.compile(r'[\s,]+')
        for (pc, type, data) in contents:
            inst = filter(lambda x: len(x) > 0, inst_re.split(data[0]))
            yield (pc, type, inst)

    def substitute_symbols(self, contents, sym_table):
        for (pc, type, data) in contents:
            data = list(data)
            data = [str(sym_table[n]) if n in sym_table.keys() else n for n in data]
            data = [str(self.reg_table[n]) if n in self.reg_table.keys() else n for n in data]
            if "(" and ")" in data[-1]:
                data[-1] = [", ".join(x.split()) for x in re.split(r'[()]',data[-1]) if x.strip()]
                data[-1] = [str(sym_table[n]) if n in sym_table.keys() else n for n in data[-1]]
                data[-1] = [str(self.reg_table[n]) if n in self.reg_table.keys() else n for n in data[-1]]
                data.append(data[-1][0])
                data[-2] = data[-2][1]#wrong
            if "x" in data[-1]:
                data[-1] = int(data[-1], 16)
            yield (pc, type, data)

    def translate_asm(self, contents):
        for (pc, type, data) in contents:
            opcode = data[0]
            entry = list(filter(lambda instr: instr['instr'] == opcode, self.op_table))[0]
            print(entry)
            if entry['type'] == 'ALU-R':
                machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]) << 16) + (int(data[3]) << 12)
                print(hex(machine))
            elif entry['type'] == 'ALU-I':
                if entry['instr'] == 'MVHI':
                    machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]))   
                else:
                    machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]) << 16) + (int(data[3]))
                print(hex(machine))
            elif entry['type'] == 'LDSW':
                machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]) << 16) + (int(data[3]))
                print(hex(machine))
            elif entry['type'] == 'CMP-R':
                machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]) << 16) + (int(data[3]) << 12)
                print(hex(machine))
            elif entry['type'] == 'CMP-I':
                machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]) << 16) + (int(data[3]))
            elif entry['type'] == 'BRANCH':
                if "Z" in entry['instr'] or "z" in entry['instr']:
                    machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]))   
                else:
                    machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]) << 16) + (int(data[3]))
                    print(1)
                print(hex(machine))
            elif entry['type'] == 'PSEUDO':
                print(1 )
            yield (pc, type, data)
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
        regs.update({"A{0}".format(i): regs["R{0}".format(i)] for i in range(0, 4)})
        regs.update({"RV": regs["R3"]})
        regs.update({"T{0}".format(i): regs["R{0}".format(i + 4)] for i in range(0, 2)})
        regs.update({"S{0}".format(i): regs["R{0}".format(i + 6)] for i in range(0, 3)})
        regs.update({"GP": regs["R12"]})
        regs.update({"FP": regs["R13"]})
        regs.update({"SP": regs["R14"]})
        regs.update({"RA": regs["R15"]})
        regs.update({key.lower(): regs[key] for key in regs.keys()})
        return regs

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

    def build_op_table(self):
        opcodes = [
            {'instr': 'ADD', 'type': 'ALU-R', 'opcode' : "11000111" },
            {'instr': 'SUB', 'type': 'ALU-R', 'opcode' : "11000110" },
            {'instr': 'AND', 'type': 'ALU-R', 'opcode' : "11000000" },
            {'instr': 'OR', 'type': 'ALU-R', 'opcode' : "11000001" },
            {'instr': 'XOR', 'type': 'ALU-R', 'opcode' : "11000010" },
            {'instr': 'NAND', 'type': 'ALU-R', 'opcode' : "11001000" },
            {'instr': 'NOR', 'type': 'ALU-R', 'opcode' : "11001001" },
            {'instr': 'XNOR', 'type': 'ALU-R', 'opcode' : "11001010" },
            {'instr': 'ADDI', 'type': 'ALU-I', 'opcode' : '01000111'},
            {'instr': 'SUBI', 'type': 'ALU-I', 'opcode' : '01000110'},
            {'instr': 'ANDI', 'type': 'ALU-I', 'opcode' : '01000000'},
            {'instr': 'ORI', 'type': 'ALU-I', 'opcode' : '01000001'},
            {'instr': 'XORI', 'type': 'ALU-I', 'opcode' : '01000010'},
            {'instr': 'NANDI', 'type': 'ALU-I', 'opcode' : '01001000'},
            {'instr': 'NORI', 'type': 'ALU-I', 'opcode' : '01001001'},
            {'instr': 'XNORI', 'type': 'ALU-I', 'opcode' : '01001010'},
            {'instr': 'MVHI', 'type': 'ALU-I', 'opcode' : '01001111'},
            {'instr': 'LW', 'type': 'LDSW', 'opcode': '01110000'},
            {'instr': 'SW', 'type': 'LDSW', 'opcode': '00110000'},
            {'instr': 'F', 'type': 'CMP-R', 'opcode': '11010011'},
            {'instr': 'EQ', 'type': 'CMP-R', 'opcode': '11010110'},
            {'instr': 'LT', 'type': 'CMP-R', 'opcode': '11011001'},
            {'instr': 'LTE', 'type': 'CMP-R', 'opcode': '11011100'},
            {'instr': 'T', 'type': 'CMP-R', 'opcode': '11010000'},
            {'instr': 'NE', 'type': 'CMP-R', 'opcode': '11010101'},
            {'instr': 'GTE', 'type': 'CMP-R', 'opcode': '11011010'},
            {'instr': 'GT', 'type': 'CMP-R', 'opcode': '11011111'},
            {'instr': 'FI', 'type': 'CMP-I', 'opcode' : '01010011'},
            {'instr': 'EQI', 'type': 'CMP-I', 'opcode' : '01010110'},
            {'instr': 'LTI', 'type': 'CMP-I', 'opcode' : '01011001'},
            {'instr': 'LTEI', 'type': 'CMP-I', 'opcode' : '01011100'},
            {'instr': 'TI', 'type': 'CMP-I', 'opcode' : '01010000'},
            {'instr': 'NEI', 'type': 'CMP-I', 'opcode' : '01010101'},
            {'instr': 'GTEI', 'type': 'CMP-I', 'opcode' : '01011010'},
            {'instr': 'GTI', 'type': 'CMP-I', 'opcode' : '01011111'},
            {'instr': 'BF', 'type': 'BRANCH', 'opcode': '00100011'},
            {'instr': 'BEQ', 'type': 'BRANCH', 'opcode': '00100110'},
            {'instr': 'BLT', 'type': 'BRANCH', 'opcode': '00101001'},
            {'instr': 'BLTE', 'type': 'BRANCH', 'opcode': '00101100'},
            {'instr': 'BEQZ', 'type': 'BRANCH', 'opcode': '00100010'},
            {'instr': 'BLTZ', 'type': 'BRANCH', 'opcode': '00101101'},
            {'instr': 'BLTEZ', 'type': 'BRANCH', 'opcode': '00101000'},
            {'instr': 'BT', 'type': 'BRANCH', 'opcode': '00100000'},
            {'instr': 'BNE', 'type': 'BRANCH', 'opcode': '00100101'},
            {'instr': 'BGTE', 'type': 'BRANCH', 'opcode': '00101010'},
            {'instr': 'BGT', 'type': 'BRANCH', 'opcode': '00101011'},
            {'instr': 'BNEZ', 'type': 'BRANCH', 'opcode': '00100001'},
            {'instr': 'BGTEZ', 'type': 'BRANCH', 'opcode': '00101110'},
            {'instr': 'BGTZ', 'type': 'BRANCH', 'opcode': '00101111'},
            {'instr': 'JAL', 'type': 'BRANCH', 'opcode': '01100000'},
            {'instr': 'BR', 'type': 'PSEUDO', 'opcode': '00100110'},
            {'instr': 'NOT', 'type': 'PSEUDO', 'opcode': '11001000'},
            {'instr': 'BLE', 'type': 'PSEUDO', 'opcode': '00100001'},
            {'instr': 'BGE', 'type': 'PSEUDO', 'opcode': '00100001'},
            {'instr': 'CALL', 'type': 'PSEUDO', 'opcode': '01100000'},
            {'instr': 'RET', 'type': 'PSEUDO', 'opcode': '01100000'},
            {'instr': 'JMP', 'type': 'PSEUDO', 'opcode': '01100000'},
        ]
        return opcodes

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', metavar="<input_file>", help="The input file to \
                        be assembled", required=True) # todo output_file
    args = parser.parse_args()

    assembler = Assembler()
    out = assembler.assemble(args.i)

if __name__ == "__main__":
    main()