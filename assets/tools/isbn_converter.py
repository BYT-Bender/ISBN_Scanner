from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox, QTextEdit, QFrame
from PyQt5.QtCore import Qt
import sys

class ISBNConverter(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ISBN Converter")
        self.setGeometry(100, 100, 500, 200)

        title_label = QLabel("ISBN Converter", self)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        self.isbn_input = QLineEdit(self)
        self.isbn_input.setFixedHeight(30)
        self.isbn_input.setPlaceholderText("Enter ISBN-10 or ISBN-13")
        self.isbn_input.textChanged.connect(self.update_char_count)

        self.char_count_text = QLineEdit(self)
        self.char_count_text.setReadOnly(True)
        self.char_count_text.setFixedHeight(self.isbn_input.height())
        self.char_count_text.setFixedWidth(self.isbn_input.height())
        self.char_count_text.setAlignment(Qt.AlignCenter)
        self.char_count_text.selectionChanged.connect(lambda: self.char_count_text.setSelection(0, 0))

        self.convert_button = QPushButton("Convert", self)
        self.convert_button.clicked.connect(self.convert_isbn)

        self.result_text = QTextEdit(self)
        self.result_text.setReadOnly(True)
        self.result_text.setFixedHeight(30)

        self.copy_button = QPushButton("Copy", self)
        self.copy_button.clicked.connect(self.copy_to_clipboard)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.isbn_input)
        input_layout.addWidget(self.char_count_text)
        input_layout.addWidget(self.convert_button)
        input_layout.setAlignment(Qt.AlignLeft)

        result_layout = QHBoxLayout()
        result_layout.addWidget(self.result_text)
        result_layout.addWidget(self.copy_button)

        layout = QVBoxLayout()
        layout.addWidget(title_label)
        layout.addLayout(input_layout)
        layout.addLayout(result_layout)

        self.setLayout(layout)

    def update_char_count(self):
        char_count = len(self.isbn_input.text())
        self.char_count_text.setText(str(char_count))

    def convert_isbn(self):
        isbn = self.isbn_input.text().replace("-", "")
        if len(isbn) == 10:
            converted_isbn = self.isbn10_to_isbn13(isbn)
        elif len(isbn) == 13:
            converted_isbn = self.isbn13_to_isbn10(isbn)
        else:
            self.result_text.setDisabled(True)
            self.result_text.setText("Invalid ISBN length")
            return

        if converted_isbn:
            self.result_text.setDisabled(False)
            self.result_text.setText(f"{converted_isbn}")
        else:
            self.result_text.setDisabled(True)
            self.result_text.setText("Invalid ISBN format")

    def isbn10_to_isbn13(self, isbn10):
        if len(isbn10) != 10:
            return None

        isbn13 = '978' + isbn10[:-1]
        check_digit = 0
        for i, char in enumerate(isbn13):
            check_digit += int(char) * (1 if i % 2 == 0 else 3)
        check_digit = (10 - (check_digit % 10)) % 10

        return isbn13 + str(check_digit)

    def isbn13_to_isbn10(self, isbn13):
        if len(isbn13) != 13 or not isbn13.startswith('978'):
            return None

        isbn10 = isbn13[3:-1]
        check_digit = 0
        for i, char in enumerate(isbn10):
            check_digit += int(char) * (10 - i)
        check_digit = (11 - (check_digit % 11)) % 11
        check_digit = 'X' if check_digit == 10 else str(check_digit)

        return isbn10 + check_digit

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.result_text.toPlainText())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    converter = ISBNConverter()
    converter.show()
    sys.exit(app.exec_())
