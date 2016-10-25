import re


class ISA():
    def __init__(self, sym_table_names, sym_table_labels):
        self.sym_table_labels = sym_table_labels
        self.sym_table_names = sym_table_names
        self.reg_table = self.build_reg_table()
        self.op_table = self.build_op_table()

    def translate_instruction(self, pc, inst):
        inst_name = inst[0].upper().strip()
        assert (inst_name == ".WORD" or inst_name in self.op_table)
        inst_type = self.op_table.get(inst_name).get('type') if inst_name in self.op_table else None
        inst_opcode = int(self.op_table.get(inst_name).get('opcode'), 2) if inst_name in self.op_table else None

        if inst_name == ".WORD":
            asm = "%08x" % (self.parse_imm(inst[1]),)
        elif inst_type == "ALU-R" or inst_type == "CMP-R":
            # OP FUN RD RS1 RS2
            rd = self.reg_table[inst[1]]
            rs1 = self.reg_table[inst[2]]
            rs2 = self.reg_table[inst[3]]
            asm = "%02x%01x%01x%01x%03x" % (inst_opcode, rd, rs1, rs2, 0)
        elif inst_type == "ALU-I" or inst_type == "CMP-I":
            # OP FUN RD RS1 IMM
            rd = self.reg_table[inst[1]]
            rs1 = self.reg_table[inst[2]] if inst_name != "MVHI" else 0
            imm = self.parse_imm(inst[3]) if inst_name != "MVHI" else (self.parse_imm(inst[2]) >> 16)
            asm = "%02x%01x%01x%s" % (inst_opcode, rd, rs1, self.twocompl_to_hex(imm, 16))
        elif inst_type == "LDSW" or inst_name == "JAL":
            # OP FUN RMEM RS1 IMM
            rmem = self.reg_table[inst[1]]
            r = re.match(r'^(.+)\((.+)\)$', inst[2])
            rs1 = self.reg_table[r.group(2)]
            imm = self.parse_imm(r.group(1))
            asm = "%02x%01x%01x%s" % (inst_opcode, rmem, rs1, self.twocompl_to_hex(imm, 16))
        elif inst_type == "BRANCH":
            # OP FUN RD RS1 IMM
            zero_rs1 = ["BEQZ", "BLTZ", "BLTEZ", "BNEZ", "BGTZ", "BGTEZ"]
            rd = self.reg_table[inst[1]]
            rs1 = self.reg_table[inst[2]] if inst_name not in zero_rs1 else 0
            imm = self.parse_imm(inst[3]) if inst_name not in zero_rs1 else self.parse_imm(inst[2])
            asm = "%02x%01x%01x%s" % (inst_opcode, rd, rs1, self.twocompl_to_hex(imm - (pc + 1), 16))
        elif inst_type == "PSEUDO":
            if inst_name == "BR":
                rd = self.reg_table['r6']
                rs1 = self.reg_table['r6']
                imm = self.parse_imm(inst[1])
                asm = "%02x%01x%01x%s" % (inst_opcode, rd, rs1, self.twocompl_to_hex(imm - (pc + 1), 16))
            elif inst_name == "NOT":
                rd = self.reg_table[inst[1]]
                rs1 = self.reg_table[inst[2]]
                rs2 = rs1
                asm = "%02x%01x%01x%01x%03x" % (inst_opcode, rd, rs1, rs2, 0)
            elif inst_name == "CALL": # imm(RS1) -> JAL RA,imm(RS1)
                rmem = self.reg_table['ra']
                r = re.match(r'^(.+)\((.+)\)$', inst[1])
                rs1 = self.reg_table[r.group(2)]
                imm = self.parse_imm(r.group(1))
                asm = "%02x%01x%01x%s" % (inst_opcode, rmem, rs1, self.twocompl_to_hex(imm, 16))
            elif inst_name == "RET": # JAL R9,0(RA)
                rmem = self.reg_table['r9']
                rs1 = self.reg_table['ra']
                imm = 0
                asm = "%02x%01x%01x%s" % (inst_opcode, rmem, rs1, self.twocompl_to_hex(imm, 16))
            elif inst_name == "JMP": # "JAL R9,imm(RS1)"
                rmem = self.reg_table['r9']
                r = re.match(r'^(.+)\((.+)\)$', inst[1])
                rs1 = self.reg_table[r.group(2)]
                imm = self.parse_imm(r.group(1))
                asm = "%02x%01x%01x%s" % (inst_opcode, rmem, rs1, self.twocompl_to_hex(imm, 16))
            else:
                asm = ""
        else:
            asm = ""

        comment = "-- @ 0x{} : {}".format((format((int(pc * 4)), 'x')).zfill(8), self.reconstruct_inst(inst).upper())
        asm_line = "{} : {};".format(format(int(pc), 'x').zfill(8), asm)
        return comment + "\n" + asm_line

    def parse_imm(self, imm):
        if (imm in self.sym_table_names):
            parsed_imm = self.sym_table_names[imm]
        elif (imm in self.sym_table_labels):
            parsed_imm = self.sym_table_labels[imm]
        else:
            parsed_imm = int(imm, 0)

        return parsed_imm

    @staticmethod
    def tokenize_symbol_line(l):
        def parse_literal(num):
            return int(num, 0)

        s = l.strip()
        m = re.match(r'^.NAME\s*(.*)\s*=\s*(.*)\s*$', s)
        if m:
            return "NAME", [m.group(1), parse_literal(m.group(2))]
        m = re.match(r'^.ORIG\s*(.*)\s*$', s)
        if m:
            return "ORIG", [parse_literal(m.group(1))]
        m = re.match(r'^.WORD\s*(.*)\s*$', s)
        if m:
            return "WORD", [".WORD " + m.group(1)]
        m = re.match(r'^\s*([^\s]+)\s*:\s*(.+)\s*$', s)
        if m:
            return "LABELOP", [m.group(1), m.group(2)]
        m = re.match(r'^\s*([^\s]+)\s*:\s*$', s)
        if m:
            return "LABEL", [m.group(1)]
        return "OP", [l]

    @staticmethod
    def reconstruct_inst(inst):
        orig = inst[0]
        if (len(inst) > 1):
            orig = orig + " " + inst[1]
            for a in range(2, len(inst)):
                orig = orig + "," + inst[a]
        return orig

    @staticmethod
    def twocompl_to_hex(n, nbits):
        if n >= 0:
            return (format(n, 'x')).zfill(nbits >> 2)
        else:
            mask = (1 << nbits) - 1
            return format((((abs(n) ^ mask) + 1) & mask), 'x')

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
    @staticmethod
    def build_reg_table():
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

    @staticmethod
    def build_op_table():
        return {
            'ADD': {'type': 'ALU-R', 'opcode': '11000111', 'class': 'IMM'},
            'SUB': {'type': 'ALU-R', 'opcode': '11000110', 'class': 'IMM'},
            'AND': {'type': 'ALU-R', 'opcode': '11000000', 'class': 'IMM'},
            'OR': {'type': 'ALU-R', 'opcode': '11000001', 'class': 'IMM'},
            'XOR': {'type': 'ALU-R', 'opcode': '11000010', 'class': 'IMM'},
            'NAND': {'type': 'ALU-R', 'opcode': '11001000', 'class': 'IMM'},
            'NOR': {'type': 'ALU-R', 'opcode': '11001001', 'class': 'IMM'},
            'XNOR': {'type': 'ALU-R', 'opcode': '11001010', 'class': 'IMM'},
            'ADDI': {'type': 'ALU-I', 'opcode': '01000111', 'class': 'IMM'},
            'SUBI': {'type': 'ALU-I', 'opcode': '01000110', 'class': 'IMM'},
            'ANDI': {'type': 'ALU-I', 'opcode': '01000000', 'class': 'IMM'},
            'ORI': {'type': 'ALU-I', 'opcode': '01000001', 'class': 'IMM'},
            'XORI': {'type': 'ALU-I', 'opcode': '01000010', 'class': 'IMM'},
            'NANDI': {'type': 'ALU-I', 'opcode': '01001000', 'class': 'IMM'},
            'NORI': {'type': 'ALU-I', 'opcode': '01001001', 'class': 'IMM'},
            'XNORI': {'type': 'ALU-I', 'opcode': '01001010', 'class': 'IMM'},
            'MVHI': {'type': 'ALU-I', 'opcode': '01001111', 'class': 'IMM'},
            'LW': {'type': 'LDSW', 'opcode': '01110000'},
            'SW': {'type': 'LDSW', 'opcode': '00110000'},
            'F': {'type': 'CMP-R', 'opcode': '11010011', 'class': 'IMM'},
            'EQ': {'type': 'CMP-R', 'opcode': '11010110', 'class': 'IMM'},
            'LT': {'type': 'CMP-R', 'opcode': '11011001', 'class': 'IMM'},
            'LTE': {'type': 'CMP-R', 'opcode': '11011100', 'class': 'IMM'},
            'T': {'type': 'CMP-R', 'opcode': '11010000', 'class': 'IMM'},
            'NE': {'type': 'CMP-R', 'opcode': '11010101', 'class': 'IMM'},
            'GTE': {'type': 'CMP-R', 'opcode': '11011010', 'class': 'IMM'},
            'GT': {'type': 'CMP-R', 'opcode': '11011111', 'class': 'IMM'},
            'FI': {'type': 'CMP-I', 'opcode': '01010011', 'class': 'IMM'},
            'EQI': {'type': 'CMP-I', 'opcode': '01010110', 'class': 'IMM'},
            'LTI': {'type': 'CMP-I', 'opcode': '01011001', 'class': 'IMM'},
            'LTEI': {'type': 'CMP-I', 'opcode': '01011100', 'class': 'IMM'},
            'TI': {'type': 'CMP-I', 'opcode': '01010000', 'class': 'IMM'},
            'NEI': {'type': 'CMP-I', 'opcode': '01010101', 'class': 'IMM'},
            'GTEI': {'type': 'CMP-I', 'opcode': '01011010', 'class': 'IMM'},
            'GTI': {'type': 'CMP-I', 'opcode': '01011111', 'class': 'IMM'},
            'BF': {'type': 'BRANCH', 'opcode': '00100011'},
            'BEQ': {'type': 'BRANCH', 'opcode': '00100110'},
            'BLT': {'type': 'BRANCH', 'opcode': '00101001'},
            'BLTE': {'type': 'BRANCH', 'opcode': '00101100'},
            'BEQZ': {'type': 'BRANCH', 'opcode': '00100010'},
            'BLTZ': {'type': 'BRANCH', 'opcode': '00101101'},
            'BLTEZ': {'type': 'BRANCH', 'opcode': '00101000'},
            'BT': {'type': 'BRANCH', 'opcode': '00100000'},
            'BNE': {'type': 'BRANCH', 'opcode': '00100101'},
            'BGTE': {'type': 'BRANCH', 'opcode': '00101010'},
            'BGT': {'type': 'BRANCH', 'opcode': '00101011'},
            'BNEZ': {'type': 'BRANCH', 'opcode': '00100001'},
            'BGTEZ': {'type': 'BRANCH', 'opcode': '00101110'},
            'BGTZ': {'type': 'BRANCH', 'opcode': '00101111'},
            'JAL': {'type': 'BRANCH', 'opcode': '01100000'},
            'BR': {'type': 'PSEUDO', 'opcode': '00100110'},
            'NOT': {'type': 'PSEUDO', 'opcode': '11001000'},
            'BLE': {'type': 'PSEUDO', 'opcode': '00100001'},
            'BGE': {'type': 'PSEUDO', 'opcode': '00100001'},
            'CALL': {'type': 'PSEUDO', 'opcode': '01100000'},
            'RET': {'type': 'PSEUDO', 'opcode': '01100000'},
            'JMP': {'type': 'PSEUDO', 'opcode': '01100000'},
        }
