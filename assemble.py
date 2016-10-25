import argparse
import re

from isa import ISA


class Assembler():
    def __init__(self, filename, filename_out):
        # 1. read in file
        contents = self.read_and_clean_asm(filename)
        # 2. make symbol tables
        (inst_toks, sym_table_names, sym_table_labels) = self.build_sym_table(contents)
        self.isa = ISA(sym_table_names, sym_table_labels)
        # 3. translate to bytecode
        asm_str_list = self.assemble_2ndpass(inst_toks)
        # 4. write to file
        self.write_asm(filename_out, asm_str_list)

    @staticmethod
    def read_and_clean_asm(filename):
        with open(filename, 'r') as f:
            data = f.readlines()
        # strip whitespace
        data = map(lambda x: x.strip(), data)
        # strip comments
        data = map(lambda x: x.split(';', 1)[0], data)
        # filter empty lines
        data = filter(lambda x: x is not None, data)
        # filter empty lines
        data = filter(lambda x: len(x) > 0, data)
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', metavar="<input_file>", help="The input file to be assembled", required=True)
    parser.add_argument('-o', metavar="<output_file>", help="The output file", required=True)
    args = parser.parse_args()
    Assembler(args.i, args.o)


if __name__ == "__main__":
    main()
