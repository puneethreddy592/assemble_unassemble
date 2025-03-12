import sys
import subprocess
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTextEdit,
                             QPushButton, QLabel, QComboBox, QTabWidget)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import sys

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS  # Extracted folder for PyInstaller
else:
    base_path = os.path.dirname(os.path.abspath(__file__))


class SimpleRiscGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("SimpleRisc Assembler & Disassembler")
        self.setGeometry(100, 100, 800, 500)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.createAssembleTab(), "Assemble")
        self.tabs.addTab(self.createDisassembleTab(), "Disassemble")
        self.tabs.addTab(self.createGuideTab(), "Guide")
        
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)
    
    def createAssembleTab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        self.input_label = QLabel("Enter Assembly Code:")
        layout.addWidget(self.input_label)
        
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)
        
        self.option_label = QLabel("Select Output Format:")
        layout.addWidget(self.option_label)
        
        self.option_box = QComboBox()
        self.option_box.addItems(["Tokens (-t)", "Encoded (-e)", "Binary File (-tb)", "Hex File (-th)", "Binary (-b)", "Hex (-hh)"])
        layout.addWidget(self.option_box)
        
        self.run_button = QPushButton("Assemble")
        self.run_button.clicked.connect(self.runAssembler)
        layout.addWidget(self.run_button)
        
        self.output_label = QLabel("Output:")
        layout.addWidget(self.output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
        
        tab.setLayout(layout)
        return tab
    
    def createDisassembleTab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        self.unasm_label = QLabel("Enter Binary Instructions:")
        layout.addWidget(self.unasm_label)
        
        self.unasm_text_edit = QTextEdit()
        layout.addWidget(self.unasm_text_edit)
        
        self.unasm_option_label = QLabel("Select Output Format:")
        layout.addWidget(self.unasm_option_label)
        
        self.unasm_option_box = QComboBox()
        self.unasm_option_box.addItems(["Include Binary (-i)", "Default Output"])
        layout.addWidget(self.unasm_option_box)
        
        self.unasm_run_button = QPushButton("Disassemble")
        self.unasm_run_button.clicked.connect(self.runDisassembler)
        layout.addWidget(self.unasm_run_button)
        
        self.unasm_output_label = QLabel("Output:")
        layout.addWidget(self.unasm_output_label)
        
        self.unasm_output_text = QTextEdit()
        self.unasm_output_text.setReadOnly(True)
        layout.addWidget(self.unasm_output_text)
        
        tab.setLayout(layout)
        return tab
    
    def createGuideTab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        guide_text = ("<b>Assembly Guide:</b><br><br>"
                      "<b>Assemble Usage:</b><br>"
                      "- Tokens (-t) and Encoded (-e) do not generate files & are for debugging -t provides the labels and the instructions while -e provides with address and the encoded instructions.<br>"
                      "- Binary File (-tb) generates a .txt file with binary output.<br>"
                      "- Hex File (-th) generates a .txt file with hex output.<br>"
                      "- Binary (-b) generates a .bin file.<br>"
                      "- Hex (-hh) generates a .hex file.<br><br>"
                      "<b>Disassemble Usage:</b><br>"
                      "- Generates a .txt file with disassembled output.<br>"
                      "- You can choose to include instructions using the -i flag.<br><br>"
                      "- Optionally, one may use labels like .start, .org, .main and can give an address starting with 0x (example: 0xc000) and end with :<br>"
                      "- Do not use capital letters for labels.<br>"
                      "- Use .label example: b .loop.<br>"
                      "- You can give immediate values as int, 0b (binary), or 0x (hex).<br>"
                      "- Use ; for comments.<br>"
                      "- For ld and store, use this format: ld r1, 24[r2].<br>"
                      "- Use hlt to stop (it is a pseudo-instruction).<br><br>"
                      "For more details, visit: <a href='https://puneethreddy592.github.io/assemble_unassemble/guide.html'>Click here for the full guide</a>")
        
        guide_label = QLabel()
        guide_label.setTextFormat(Qt.TextFormat.RichText)
        guide_label.setText(guide_text)
        guide_label.setWordWrap(True)
        guide_label.setFont(QFont("Arial", 10))
        guide_label.setOpenExternalLinks(True)
        layout.addWidget(guide_label)
        
        tab.setLayout(layout)
        return tab
    
    def runAssembler(self):
        assemble_path = os.path.join(base_path, "assemble.py")
        with open("assembly.txt", "w") as f:
            f.write(self.text_edit.toPlainText())
        
        option_map = {"Tokens (-t)": "-t", "Encoded (-e)": "-e", "Binary File (-tb)": "-tb", "Hex File (-th)": "-th", "Binary (-b)": "-b", "Hex (-hh)": "-hh"}
        selected_option = option_map[self.option_box.currentText()]
        
        result = subprocess.run(["python", assemble_path, "-f", "assembly.txt", selected_option], capture_output=True, text=True)
        output_text = result.stdout if result.stdout else result.stderr
        
        if selected_option in ["-tb", "-th"]:
            output_filename = "outputbin.txt" if selected_option == "-tb" else "outputhex.txt"
            try:
                with open(output_filename, "r") as f:
                    output_text = f.read()
            except FileNotFoundError:
                output_text = "Error: Output file not found."
        
        self.output_text.setText(output_text)
    
    def runDisassembler(self):
        disassemble_path = os.path.join(base_path, "unassemble.py")
        with open("binary.txt", "w") as f:
            f.write(self.unasm_text_edit.toPlainText())
        
        output_file = "disassembled_output.txt"
        option_map = {"Include Binary (-i)": "-i", "Default Output": ""}
        selected_option = option_map[self.unasm_option_box.currentText()]
        
        command = ["python", disassemble_path, "-f", "binary.txt", "-o", output_file]
        if selected_option:
            command.append(selected_option)
        
        subprocess.run(command, capture_output=True, text=True)
        
        try:
            with open(output_file, "r") as f:
                output_text = f.read()
        except FileNotFoundError:
            output_text = "Error: disassembled_output.txt not found."
        
        self.unasm_output_text.setText(output_text)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleRiscGUI()
    window.show()
    sys.exit(app.exec())
