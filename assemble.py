import argparse
import re
from isa import ISA

class Assembler():
    def __init__(self, filename, filename_out):
        # 1. read in file
        # 2. make symbol tables
        # 3. substitute symbol table
        # 4. translate to bytecode
        contents = self.read_and_clean_asm(filename)
        (inst_toks, sym_table_names, sym_table_labels) = self.build_sym_table(contents)
        self.isa = ISA(sym_table_names, sym_table_labels)
        asm_str_list = self.assemble_2ndpass(inst_toks)
        self.write_asm(filename_out, asm_str_list)

    @staticmethod
    def read_and_clean_asm(filename):
        with open(filename, 'r') as f:
            data = f.readlines()
        data = map(lambda x: x.strip(), data)           # strip whitespace
        data = map(lambda x: x.split(';', 1)[0], data)  # strip comments
        data = filter(lambda x: x is not None, data)    # filter empty lines
        data = filter(lambda x: len(x) > 0, data)       # filter empty lines
        return data

    def build_sym_table(self, lines):
        names = {}
        labels = {}
        toks = list(map(ISA.tokenize_symbol_line, lines))

        annotated_toks = []

        pc = 0
        for n in range(0, len(toks)):
            (inst_type, data) = toks[n]

            if inst_type is "NAME":
                names[data[0].strip()] = data[1]
            elif inst_type is "ORIG":
                pc = data[0] >> 2
            elif inst_type.startswith("LABEL"):
                labels[data[0].strip()] = pc

            if inst_type is "WORD" or inst_type.endswith("OP"):
                annotated_toks.append((pc, inst_type, data))
                pc += 1

        return self.split_ops(annotated_toks), names, labels

    @staticmethod
    def split_ops(contents):
        inst_re = re.compile(r'[\s,]+')
        for (pc, type, data) in contents:
            inst = filter(lambda x: len(x) > 0, inst_re.split(data[0]))
            yield (pc, type, inst)

    def assemble_2ndpass(self, contents):
        for (pc, type, inst) in contents:
            yield self.isa.translate_instruction(pc, inst)

    def write_asm(self, filename_out, asm_str_list):
        with open(filename_out, 'w+') as f:
            f.write("WIDTH=32;\nDEPTH=2048;\nADDRESS_RADIX=HEX;\nDATA_RADIX=HEX;\nCONTENT BEGIN\n")
            f.write("\n".join(asm_str_list))
            f.write("\nEND;\n")


    def substitute_symbols_nick(self, contents, sym_table):
        for (pc, type, data) in contents:
            data = list(data)
            copy = data[:]
            data = [str(sym_table[n]) if n in sym_table.keys() else n for n in data]
            data = [str(self.reg_table[n]) if n in self.reg_table.keys() else n for n in data]
            op_entry = list(filter(lambda instr: instr['instr'] == data[0].upper(), self.op_table))[0]
            if "(" and ")" in data[-1]:
                data[-1] = [", ".join(x.split()) for x in re.split(r'[()]', data[-1]) if x.strip()]
                data[-1] = [str(sym_table[n]) if n in sym_table.keys() else n for n in data[-1]]
                data[-1] = [str(self.reg_table[n]) if n in self.reg_table.keys() else n for n in data[-1]]
                data.append(data[-1][0])
                data[-2] = data[-2][1]
                print(data)
            if op_entry['type'] == 'BRANCH':
                if op_entry['instr'] != 'JAL':
                    data[-1] = str((int(data[-1]) - (int(pc) + 4)) // 4 & 0xffff)
            if op_entry['instr'] == 'JMP' or op_entry['instr'] == 'CALL' or op_entry['instr'] == 'JAL':
                data[-1] = str((int(data[-1]) // 4))
            if "x" in data[-1]:
                data[-1] = int(data[-1], 16)
            data.append(copy)
            yield (pc, type, data)

    def translate_asm_nick(self, contents):
        for (pc, type, data) in contents:
            opcode = data[0]
            entry = list(filter(lambda instr: instr['instr'] == opcode.upper(), self.op_table))[0]
            if entry['type'] == 'ALU-R':
                machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]) << 16) + (int(data[3]) << 12)
            elif entry['type'] == 'ALU-I':
                if entry['instr'] == 'MVHI':
                    machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + ((int(data[2]) & 0xffff0000) >> 16)
                else:
                    machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]) << 16) + (int(data[3]) & 0xffff)
            elif entry['type'] == 'LDSW':
                machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]) << 16) + (int(data[3]) & 0xffff)
            elif entry['type'] == 'CMP-R':
                machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]) << 16) + (int(data[3]) << 12)
            elif entry['type'] == 'CMP-I':
                machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]) << 16) + (int(data[3]) & 0xffff)
            elif entry['type'] == 'BRANCH':
                if "Z" in entry['instr'] or "z" in entry['instr']:
                    machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]))
                else:
                    machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]) << 16) + (int(data[3]) & 0xffff)
            elif entry['type'] == 'PSEUDO':
                if entry['instr'] == 'BR':
                    machine = (int(entry['opcode'], 2) << 24) + (6 << 20) + (6 << 16) + (int(data[1]) & 0xffff)
                elif entry['instr'] == 'NOT':
                    machine = (int(entry['opcode'], 2) << 24) + (int(data[1]) << 20) + (int(data[2]) << 16) + (int(data[2]) << 12)
                elif entry['instr'] == 'BLE':
                    machine = 0
                elif entry['instr'] == 'BGE':
                    machine = 0
                elif entry['instr'] == 'CALL':
                    machine = (int(entry['opcode'], 2) << 24) + (15 << 20) + (int(data[1]) << 16) + (int(data[2]) & 0xffff)
                elif entry['instr'] == 'RET':
                    machine = (int(entry['opcode'], 2) << 24) + (9 << 20) + (15 << 16)
                else:
                    machine = (int(entry['opcode'], 2) << 24) + (9 << 20) + (int(data[1]) << 16) + (int(data[2]) & 0xffff)
            data.append(format(machine, 'x'))
            yield (pc, type, data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', metavar="<input_file>", help="The input file to be assembled", required=True)
    parser.add_argument('-o', metavar="<output_file>", help="The output file", required=True)
    args = parser.parse_args()

    assembler = Assembler(args.i, args.o)


if __name__ == "__main__":
    main()
