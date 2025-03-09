import os
import argparse
import sys
import re

class Assembler:
    opcodes = {
        "add": "00000", "sub": "00001", "mul": "00010", "div": "00011", "mod": "00100", "cmp": "00101",
        "and": "00110", "or": "00111", "not": "01000", "mov": "01001", "lsl": "01010", "lsr": "01011",
        "asr": "01100", "nop": "01101", "ld": "01110", "st": "01111",
        "beq": "10000", "bgt": "10001", "b": "10010", "call": "10011", "ret": "10100", "hlt": "11111"
    }
    
    mod_opcodes = {"add", "sub", "mul", "div", "mod", "and", "or", "lsl", "lsr", "asr"}

    def __init__(self, filename):
        self.filename = filename
        self.instructions = []
        self.labels = {}
        self.start_address = 0x0000
        self.tokenized_instructions = []
        self.instruction_encoded = []

    def int_27b_binary(self,value):
        if not (-67108864 <= value <= 67108863):
            raise ValueError("Value out of range for 27-bit signed integer")
        binary_27bit = bin(value & 0x7FFFFFF)[2:].zfill(27)  
        return binary_27bit
   
    def int_to_bin(self,value, size, mode="s"):
        if mode not in ("s", "u"):
            raise ValueError("Mode must be 's' for signed or 'u' for unsigned")

        if mode == "u":  
            if not (0 <= value < 2**size):
                raise ValueError(f"Unsigned {size}-bit overflow: {value}")
        else:  
            if not (-2**(size-1) <= value < 2**(size-1)):
                raise ValueError(f"Signed {size}-bit overflow: {value}")

        bin_value = bin(value & (2**size - 1))[2:].zfill(size)  
        return bin_value
      
    def reg_to_bin(self,register):
        if not register.startswith("r") or not register[1:].isdigit():
            raise ValueError("Invalid register format. Expected 'r0' to 'r15'.")

        reg_num = int(register[1:])  

        if not (0 <= reg_num <= 15):  
            raise ValueError(f"Register {register} out of range (must be r0 to r15).")

        return format(reg_num, "04b")  
      
    def to_int(self,value):
        if isinstance(value, int):  
             return value  

        if isinstance(value, str):
            try:
                if value.startswith(("0b", "0B")):  
                    return int(value, 2)
                elif value.startswith(("0x", "0X")):  
                    return int(value, 16)
                else:  
                    return int(value)
            except ValueError:
                return None  
    
        return None  

    def parse_data(self):
        try:
            with open(self.filename, "r") as file:
                address = self.start_address
                for line in file:
                    clean_line = line.split(";")[0].strip()
                    if not clean_line:
                        continue
                    if clean_line.startswith(".") and clean_line.endswith(":"):
                        label_parts = clean_line[:-1].split()
                        label = label_parts[0]
                        if label in {".start", ".main", ".org"} and len(label_parts) == 2 and label_parts[1].startswith("0x"):
                            self.start_address = int(label_parts[1], 16)
                        else:
                            self.labels[label] = address
                        continue
                    self.instructions.append((address, clean_line))
                    address += 4
        except FileNotFoundError:
            print(f"Error: File '{self.filename}' not found.")
            sys.exit(1)

    def update_addresses(self):
        if self.start_address != 0x0000:
            offset = self.start_address - 0x0000
            self.instructions = [(addr + offset, instr) for addr, instr in self.instructions]
            self.labels = {lbl: (addr + offset if addr is not None else None) for lbl, addr in self.labels.items()}
    
    def tokenize_instructions(self):
        for address, instruction in self.instructions:
            tokens = None  

            if instruction[:2] in ("ld", "st"):
                match = re.match(r'(\w+)\s+(\w+)\.(0x[0-9a-fA-F]+|0b[01]+|\d+)\[(\w+)\]', instruction)
                if match:
                    mnemonic, rd, imm, rs1 = match.groups()
                    tokens = [mnemonic, rd, rs1, imm]  

            if tokens is None:
                tokens = instruction.replace(" ", ",").split(",")
                tokens = list(filter(None, tokens))

            if not tokens:
                continue

            mnemonic = tokens[0]
            modifier = "00"  

            if mnemonic.endswith("u") or mnemonic.endswith("h"):
                base_mnemonic = mnemonic[:-1]
                if base_mnemonic in self.mod_opcodes:
                    modifier = "01" if mnemonic[-1] == "u" else "10"
                    mnemonic = base_mnemonic
                else:
                    print(f"Error: Modifier 'u' or 'h' cannot be used with instruction '{mnemonic}'")
                    sys.exit(1)

            if mnemonic not in self.opcodes:
                print(f"Error: Invalid instruction '{mnemonic}'")
                sys.exit(1)

            self.tokenized_instructions.append((address, [mnemonic] + tokens[1:], modifier))
    
    def encode_tokens(self):
        for address,instr,modifer in self.tokenized_instructions:
            if instr[0] in ['nop','ret','hlt']:
                self.instruction_encoded.append((address,self.opcodes[instr[0]]+27*"0"))
            elif instr[0] in ['b','beq','bgt','call']:
                if instr[1] in self.labels.keys():
                    self.instruction_encoded.append((address,self.opcodes[instr[0]]+self.int_27b_binary(self.labels[instr[1]]-address)))
            elif instr[0] in ['not','mov']:
                if self.to_int(instr[2]) != None:
                    self.instruction_encoded.append((address,self.opcodes[instr[0]]+"1"+self.reg_to_bin(instr[1])+"0000"+"00"+self.int_to_bin(self.to_int(instr[2]),16,"s")))
                else: 
                    self.instruction_encoded.append((address,self.opcodes[instr[0]]+"0"+self.reg_to_bin(instr[1])+"0000"+self.reg_to_bin(instr[2])+self.int_to_bin(0,14,"s")))
            elif instr[0] in ['cmp']:
                if self.to_int(instr[2]) != None:
                    self.instruction_encoded.append((address,self.opcodes[instr[0]]+"1"+"0000"+self.reg_to_bin(instr[1])+"00"+self.int_to_bin(self.to_int(instr[2]),16,"s")))
                else: 
                    self.instruction_encoded.append((address,self.opcodes[instr[0]]+"0"+"0000"+self.reg_to_bin(instr[1])+self.reg_to_bin(instr[2])+self.int_to_bin(0,14,"s")))
            elif instr[0] in ['add', 'sub', 'mul', 'div', 'mod', 'and', 'or', 'lsl', 'lsr', 'asr']:
                if modifer == "00":
                    if self.to_int(instr[3]) != None:
                        self.instruction_encoded.append((address,self.opcodes[instr[0]]+"1"+self.reg_to_bin(instr[1])+self.reg_to_bin(instr[2])+"00"+self.int_to_bin(self.to_int(instr[3]),16,"s")))
                    else: 
                        self.instruction_encoded.append((address,self.opcodes[instr[0]]+"0"+self.reg_to_bin(instr[1])+self.reg_to_bin(instr[2])+self.reg_to_bin(instr[3])+self.int_to_bin(0,14,"s")))
                if modifer == "01":
                    if self.to_int(instr[3]) != None:
                        self.instruction_encoded.append((address,self.opcodes[instr[0]]+"1"+self.reg_to_bin(instr[1])+self.reg_to_bin(instr[2])+"01"+self.int_to_bin(self.to_int(instr[3]),16,"u")))
                    else: 
                        self.instruction_encoded.append((address,self.opcodes[instr[0]]+"0"+self.reg_to_bin(instr[1])+self.reg_to_bin(instr[2])+self.reg_to_bin(instr[3])+self.int_to_bin(0,14,"s")))
                if modifer == "10":
                    if self.to_int(instr[3]) != None:
                        self.instruction_encoded.append((address,self.opcodes[instr[0]]+"1"+self.reg_to_bin(instr[1])+self.reg_to_bin(instr[2])+"10"+self.int_to_bin(self.to_int(instr[3]),16,"s")))
                    else: 
                        self.instruction_encoded.append((address,self.opcodes[instr[0]]+"0"+self.reg_to_bin(instr[1])+self.reg_to_bin(instr[2])+self.reg_to_bin(instr[3])+self.int_to_bin(0,14,"s")))
            elif instr[0] in ['ld','st']:
                if self.to_int(instr[3]) != None:
                    self.instruction_encoded.append((address,self.opcodes[instr[0]]+"1"+self.reg_to_bin(instr[1])+self.reg_to_bin(instr[2])+"00"+self.int_to_bin(self.to_int(instr[3]),16,"s")))
                else: 
                    print(f"The instruction requires you to pass immediate value not two registers.")
            else:
                print(f"The Instruction {instr} with the modifer : {modifer} is in valid.")


    def print_encoded(self):
        for address, binval in self.instruction_encoded:
            print(f"{format(address, 'X')}: {binval}")
    import os

    def print_bin(self):
        with open("output.bin", "wb") as f:
            for _, binval in self.instruction_encoded:
                f.write(int(binval, 2).to_bytes(4, byteorder='big'))
        print("File size:", os.path.getsize("output.bin"), "bytes")

    def print_txt(self):
    	with open("output.txt", "w") as f:
            for addr, binval in self.instruction_encoded:
                f.write(f"{binval}\n")
    	print("File size:", os.path.getsize("output.txt"), "bytes")    


    def print_tokenized_data(self):
        for address, tokens, modifier in self.tokenized_instructions:
            print(f"{format(address, 'X')}: {tokens} {modifier}")
        print(self.labels)
        print(self.instruction_encoded)

def main():
    parser = argparse.ArgumentParser(description="SimpleRisc Assembler")
    parser.add_argument("-f", "--file", required=True, help="Assembly file to parse")
    parser.add_argument("-t", "--tokens", action="store_true", help="Print tokenized instructions")
    parser.add_argument("-e", "--encode", action="store_true", help="Print encoded instructions")
    parser.add_argument("-b", "--bin", action="store_true", help="Generate binary output")
    parser.add_argument("-x", "--txt", action="store_true", help="Generate text output")

    args = parser.parse_args()
    assembler = Assembler(args.file)
    assembler.parse_data()
    assembler.update_addresses()
    assembler.tokenize_instructions()
    assembler.encode_tokens()

    if args.tokens:
        assembler.print_tokenized_data()
    if args.encode:
        assembler.print_encoded()
    if args.bin:
        assembler.print_bin()
    if args.txt:
        assembler.print_txt()

if __name__ == "__main__":
    main()

