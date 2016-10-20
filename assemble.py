import argparse


class Assembler():
    def __init__(self):
        self.op_table = {"ADD": 0x00000000} # todo fill table

    def assemble(self, filename):
        # 1. read in file
        # 2. make symbol tables
        # 3. translate
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', metavar="<input_file>", help="The input file to \
                        be assembled", required=True) # todo output_file
    args = parser.parse_args()

    assembler = Assembler()
    out = assembler.assemble(args.i)

if __name__ == "__main__":
    main()