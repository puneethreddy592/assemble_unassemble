import argparse

class Disassembler:
    opcodes = {
        "00000": "add", "00001": "sub", "00010": "mul", "00011": "div", "00100": "mod", "00101": "cmp",
        "00110": "and", "00111": "or", "01000": "not", "01001": "mov", "01010": "lsl", "01011": "lsr",
        "01100": "asr", "01101": "nop", "01110": "ld", "01111": "st",
        "10000": "beq", "10001": "bgt", "10010": "b", "10011": "call", "10100": "ret", "11111": "hlt"
    }
    
    def __init__(self, filename):
        self.filename = filename
        self.instructions = []
    
    def bin_to_int(self, binary, signed=False):
        value = int(binary, 2)
        if signed and binary[0] == "1":  # Handle sign extension for negative numbers
            value -= 2 ** len(binary)
        return value
    
    def reg_from_bin(self, bin_val):
        return f"r{int(bin_val, 2)}"
    
    def disassemble(self):
        try:
            with open(self.filename, "r") as f:
                address = 0x0000
                for line in f:
                    binary_instr = line.strip()
                    if len(binary_instr) != 32:
                        continue  # Skip invalid lines
                    
                    opcode = binary_instr[:5]
                    imm_flag = binary_instr[5]
                    rd = binary_instr[6:10]
                    rs1 = binary_instr[10:14]
                    mod = binary_instr[14:16]
                    imm_or_rs2 = binary_instr[16:]
                    
                    if opcode in self.opcodes:
                        mnemonic = self.opcodes[opcode]
                        
                        if mnemonic in ["nop", "ret", "hlt"]:
                            self.instructions.append(f"{binary_instr}  # {mnemonic}")
                        elif mnemonic in ["b", "beq", "bgt", "call"]:
                            offset = self.bin_to_int(binary_instr[5:], signed=True)
                            self.instructions.append(f"{binary_instr}  # {mnemonic} 0x{format(address + offset, 'X')}")
                        elif mnemonic in ["not", "mov"]:
                            if imm_flag == "1":
                                imm = self.bin_to_int(imm_or_rs2, signed=True)
                                self.instructions.append(f"{binary_instr}  # {mnemonic} {self.reg_from_bin(rd)}, {imm}")
                            else:
                                self.instructions.append(f"{binary_instr}  # {mnemonic} {self.reg_from_bin(rd)}, {self.reg_from_bin(binary_instr[14:18])}")
                        elif mnemonic == "cmp":
                            if imm_flag == "1":
                                imm = self.bin_to_int(imm_or_rs2, signed=True)
                                self.instructions.append(f"{binary_instr}  # {mnemonic} {self.reg_from_bin(rs1)}, {imm}")
                            else:
                                self.instructions.append(f"{binary_instr}  # {mnemonic} {self.reg_from_bin(rs1)}, {self.reg_from_bin(rs1)}")
                        elif mnemonic in ["add", "sub", "mul", "div", "mod", "and", "or", "lsl", "lsr", "asr"]:
                            if imm_flag == "1":
                                imm = self.bin_to_int(imm_or_rs2, signed=(mod != "00"))
                                modifier = "u" if mod == "01" else "h" if mod == "10" else ""
                                self.instructions.append(f"{binary_instr}  # {mnemonic}{modifier} {self.reg_from_bin(rd)}, {self.reg_from_bin(rs1)}, {imm}")
                            else:
                                self.instructions.append(f"{binary_instr}  # {mnemonic} {self.reg_from_bin(rd)}, {self.reg_from_bin(rs1)}, {self.reg_from_bin(imm_or_rs2[:4])}")
                        elif mnemonic in ["ld", "st"]:
                            imm = self.bin_to_int(imm_or_rs2, signed=True)
                            self.instructions.append(f"{binary_instr}  # {mnemonic} {self.reg_from_bin(rd)}, {imm}[{self.reg_from_bin(rs1)}]")
                    else:
                        self.instructions.append(f"{binary_instr}  # UNKNOWN")
                    
                    address += 4
        except FileNotFoundError:
            print(f"Error: File '{self.filename}' not found.")
            return
    
    def save_to_file(self, output_file, include_binary):
        with open(output_file, "w") as f:
            for instr in self.instructions:
                disassembled_part = instr.split("#")[-1].strip()
                f.write((instr if include_binary else disassembled_part) + "\n")
        print(f"Disassembled binary saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="SimpleRisc Disassembler")
    parser.add_argument("-f", "--file", required=True, help="Input text file with binary instructions")
    parser.add_argument("-o", "--output", required=True, help="Output text file to save disassembled binary")
    parser.add_argument("-i", "--include-binary", action="store_true", help="Include binary instructions in output")
    
    args = parser.parse_args()
    disassembler = Disassembler(args.file)
    disassembler.disassemble()
    disassembler.save_to_file(args.output, args.include_binary)

if __name__ == "__main__":
    main()

def runDisassembler(self):
    disassemble_path = "unassemble.py"

    # Write input binary to a file
    with open("binary.txt", "w") as f:
        f.write(self.unasm_text_edit.toPlainText())

    output_file = "disassembled_output.txt"
    option_map = {"Include Binary (-i)": "-i", "Default Output": ""}
    selected_option = option_map[self.unasm_option_box.currentText()]

    command = ["python", disassemble_path, "-f", "binary.txt", "-o", output_file]
    if selected_option:
        command.append(selected_option)

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            output_text = f"Error: {result.stderr}"
        else:
            # Read output from the disassembled file
            try:
                with open(output_file, "r") as f:
                    output_text = f.read()
            except FileNotFoundError:
                output_text = "Error: disassembled_output.txt not found."

    except Exception as e:
        output_text = f"Exception: {str(e)}"

    self.unasm_output_text.setText(output_text)