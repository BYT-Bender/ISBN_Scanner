from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout, QFrame, QListWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from datetime import datetime
from PyQt5.QtWidgets import QComboBox, QLineEdit
from PyQt5.QtWidgets import QMenuBar, QAction, QFileDialog, QMainWindow
import subprocess
import sys
import csv
import cv2
from pyzbar.pyzbar import decode, ZBarSymbol
import requests
import winsound


def get_book_details(ISBN):
    def fetch_from_google_books(ISBN):
        URL = "https://www.googleapis.com/books/v1/volumes?q=isbn:" + str(ISBN)
        try:
            Response = requests.get(URL)
            Response.raise_for_status()
            BookData = Response.json()
            if BookData["totalItems"] == 0:
                return None
            else:
                volume_info = BookData["items"][0]["volumeInfo"]
                identifiers = volume_info.get("industryIdentifiers", [])
                isbn_13 = None
                for identifier in identifiers:
                    if identifier["type"] == "ISBN_13":
                        isbn_13 = identifier["identifier"]
                        break
                if not isbn_13:
                    return None  # If no ISBN-13 is found, return None

                title = volume_info.get("title", "N/A")
                authors = volume_info.get("authors", ["N/A"])
                author = authors[0] if authors else "N/A"
                publisher = volume_info.get("publisher", "N/A")
                publishedDate = volume_info.get("publishedDate", "N/A")
                description = volume_info.get("description", "N/A")
                pageCount = volume_info.get("pageCount", "N/A")
                categories = volume_info.get("categories", ["N/A"])
                category = categories[0] if categories else "N/A"
                language = volume_info.get("language", "N/A")

                book_details = {
                    "ISBN-13": isbn_13,
                    "Title": title,
                    "Author": author,
                    "Publisher": publisher,
                    "Edition": publishedDate,
                    "Description": description,
                    "Pages": pageCount,
                    "Genre": category,
                    "Language": language
                }
                return book_details
        except requests.exceptions.RequestException as e:
            print(f"Error fetching book details from Google Books: {e}")
            return None

    def fetch_from_open_library(ISBN):
        URL = f"https://openlibrary.org/api/books?bibkeys=ISBN:{ISBN}&format=json&jscmd=data"
        try:
            Response = requests.get(URL)
            Response.raise_for_status()
            BookData = Response.json()
            if not BookData:
                return None
            else:
                book_data = BookData.get(f"ISBN:{ISBN}", {})
                if not book_data:
                    return None

                isbn_13 = ISBN
                title = book_data.get("title", "N/A")
                authors = book_data.get("authors", [{"name": "N/A"}])
                author = authors[0]["name"] if authors else "N/A"
                publisher = book_data.get("publishers", [{"name": "N/A"}])[0]["name"]
                publishedDate = book_data.get("publish_date", "N/A")
                description = book_data.get("notes", "N/A")
                pageCount = book_data.get("number_of_pages", "N/A")
                categories = book_data.get("subjects", [{"name": "N/A"}])
                category = categories[0]["name"] if categories else "N/A"
                language = book_data.get("languages", [{"key": "/languages/eng"}])[0]["key"].split('/')[-1]

                book_details = {
                    "ISBN-13": isbn_13,
                    "Title": title,
                    "Author": author,
                    "Publisher": publisher,
                    "Edition": publishedDate,
                    "Description": description,
                    "Pages": pageCount,
                    "Genre": category,
                    "Language": language
                }
                return book_details
        except requests.exceptions.RequestException as e:
            print(f"Error fetching book details from Open Library: {e}")
            return None

    book_details = fetch_from_google_books(ISBN)
    if not book_details:
        book_details = fetch_from_open_library(ISBN)
    
    return book_details


class ISBNScanner(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ISBN Scanner")
        self.setGeometry(100, 100, 1000, 600)

        # Create central widget and set layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.layout = QHBoxLayout(central_widget)
        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        # Create menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New', self)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        import_action = QAction('Import', self)
        import_action.triggered.connect(self.import_file)
        file_menu.addAction(import_action)
        
        export_action = QAction('Export', self)
        export_action.triggered.connect(self.export_file)
        file_menu.addAction(export_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        isbn_converter_action = QAction('ISBN Converter', self)
        isbn_converter_action.triggered.connect(self.open_isbn_converter)
        tools_menu.addAction(isbn_converter_action)

        # Other UI components
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(640, 480)
        self.video_label.setAlignment(Qt.AlignCenter)

        self.details_text = QTextEdit(self)
        self.details_text.setReadOnly(True)

        self.quit_button = QPushButton("Quit", self)
        self.quit_button.clicked.connect(self.close)

        self.delete_button = QPushButton("Delete", self)
        self.delete_button.clicked.connect(self.delete_selected_book)

        self.isbn_type_dropdown = QComboBox(self)
        self.isbn_type_dropdown.addItems(["ISBN-10", "ISBN-13"])

        self.isbn_input = QLineEdit(self)
        self.isbn_input.setPlaceholderText("Enter ISBN")
        self.isbn_input.textChanged.connect(self.update_isbn_info)
        self.isbn_input.returnPressed.connect(self.add_isbn)

        self.char_count_label = QLabel("0", self)

        self.add_button = QPushButton("Add", self)
        self.add_button.clicked.connect(self.add_isbn)

        self.toggle_dark_theme_button = QPushButton("Toggle Dark Theme", self)
        self.toggle_dark_theme_button.clicked.connect(self.toggle_dark_theme)

        self.toggle_camera_button = QPushButton("Toggle Camera", self)
        self.toggle_camera_button.clicked.connect(self.toggle_camera)

        self.dark_theme_enabled = False
        self.camera_on = True

        self.status_label = QLabel("Ready", self)
        self.status_label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.status_label.setAlignment(Qt.AlignLeft)

        self.process_list = QListWidget(self)
        self.book_list = QListWidget(self)
        self.book_list.itemClicked.connect(self.display_selected_book_details_wrapper)

        self.left_layout.addWidget(self.video_label)
        self.left_layout.addWidget(self.status_label)

        self.isbn_entry_layout = QHBoxLayout()
        self.isbn_entry_layout.addWidget(self.isbn_type_dropdown)
        self.isbn_entry_layout.addWidget(self.isbn_input)
        self.isbn_entry_layout.addWidget(self.char_count_label)
        self.isbn_entry_layout.addWidget(self.add_button)

        self.button_layout.addWidget(self.toggle_dark_theme_button)
        self.button_layout.addWidget(self.toggle_camera_button)

        self.left_layout.addLayout(self.button_layout)
        self.left_layout.insertLayout(2, self.isbn_entry_layout)

        self.right_layout.addWidget(self.details_text)
        self.right_layout.addWidget(self.book_list)
        self.right_layout.addWidget(self.process_list)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.addWidget(self.delete_button)
        self.bottom_layout.addWidget(self.quit_button)
        self.right_layout.addLayout(self.bottom_layout)

        self.layout.addLayout(self.left_layout)
        self.layout.addLayout(self.right_layout)
        central_widget.setLayout(self.layout)

        self.scanned_books = []
        self.load_scanned_books()

        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(10)

        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self.reset_flash)
        self.flash_timer.setSingleShot(True)

    
    def new_file(self):
        # Clear the current list and details
        self.scanned_books.clear()
        self.book_list.clear()
        self.details_text.clear()
        self.update_status("New file created", "green")

    def import_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Import CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            # Load scanned books from the selected file
            try:
                with open(file_name, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    self.scanned_books.clear()
                    self.book_list.clear()
                    for row in reader:
                        self.scanned_books.append({
                            'isbn': row['isbn'],
                            'details': {
                                'Title': row['title'],
                                'Author': row['author'],
                                'Publisher': row['publisher'],
                                'Edition': row['publish_date'],
                                'Description': row['description'],
                                'Pages': row['pages'],
                                'Genre': row['genre'],
                                'Language': row['language']
                            },
                            'timestamp': row['timestamp']
                        })
                        self.book_list.addItem(f"{row['isbn']} - {row['title']}")
                self.update_status("Imported file successfully", "green")
            except IOError as e:
                print(f"Error importing file: {e}")
                self.update_status("Error importing file", "red")

    def export_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Export CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            # Save scanned books to the selected file
            try:
                with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['isbn', 'title', 'author', 'publisher', 'publish_date', 'description', 'pages', 'genre', 'language', 'timestamp']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for book in self.scanned_books:
                        writer.writerow({
                            'isbn': book['isbn'],
                            'title': book['details']['Title'],
                            'author': book['details']['Author'],
                            'publisher': book['details']['Publisher'],
                            'publish_date': book['details']['Edition'],
                            'description': book['details']['Description'],
                            'pages': book['details']['Pages'],
                            'genre': book['details']['Genre'],
                            'language': book['details']['Language'],
                            'timestamp': book['timestamp']
                        })
                self.update_status("Exported file successfully", "green")
            except IOError as e:
                print(f"Error exporting file: {e}")
                self.update_status("Error exporting file", "red")

    def open_isbn_converter(self):
        try:
            subprocess.Popen(["python", "assets/tools/isbn_converter.py"])
            self.update_status("ISBN Converter opened", "green")
        except Exception as e:
            print(f"Error opening ISBN Converter: {e}")
            self.update_status("Error opening ISBN Converter", "red")

    def add_isbn(self):
        isbn_type = self.isbn_type_dropdown.currentText()
        isbn = self.isbn_input.text()

        if isbn:
            if isbn_type == "ISBN-10" and len(isbn) != 10:
                self.update_status("Invalid ISBN-10 length", "red")
            elif isbn_type == "ISBN-13" and len(isbn) != 13:
                self.update_status("Invalid ISBN-13 length", "red")
            else:
                book_details = get_book_details(isbn)
                if book_details:
                    isbn_13 = book_details["ISBN-13"]
                    if any(book['isbn'] == isbn_13 for book in self.scanned_books):
                        self.update_status("Entry already exists", "yellow")
                        self.play_sound("status_change")
                        self.flash_status("yellow")
                    else:
                        self.show_book_details(isbn_13, book_details, "MANUAL ENTRY")
                        self.scanned_books.append({
                            'isbn': isbn_13,
                            'details': book_details,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        self.save_scanned_books()
                        self.update_status("Book added successfully", "green")
                        self.play_sound("scan_success")
                        self.flash_status("green")
                        self.isbn_input.clear()
                else:
                    self.update_status("Invalid ISBN or no book found", "red")
                    self.play_sound("scan_error")
                    self.flash_status("red")
        else:
            self.update_status("Please enter an ISBN", "red")
            self.flash_status("red")

    def update_isbn_info(self):
        isbn = self.isbn_input.text()
        char_count = len(isbn)
        self.char_count_label.setText(str(char_count))
        
        if char_count > 10:
            self.isbn_type_dropdown.setCurrentText("ISBN-13")
        else:
            self.isbn_type_dropdown.setCurrentText("ISBN-10")

    def toggle_dark_theme(self):
        self.dark_theme_enabled = not self.dark_theme_enabled
        self.apply_theme()

    def apply_theme(self):
        if self.dark_theme_enabled:
            style_sheet = """
                background-color: #2b2b2b;
                color: #ffffff;
            """
        else:
            style_sheet = "" 

        self.setStyleSheet(style_sheet)

    def decode_barcodes(self, frame):
        try:
            return decode(frame, symbols=[ZBarSymbol.EAN13])
        except Exception as e:
            print(f"Error decoding barcodes: {e}")
            return []

    def toggle_camera(self):
        self.camera_on = not self.camera_on
        if self.camera_on:
            self.cap.open(0)
            self.timer.start(10)
            self.video_label.clear()
        else:
            self.cap.release()
            self.timer.stop()
            self.show_camera_off_icon()

    def show_camera_off_icon(self):
        pixmap = QPixmap('assets/images/camera_off.png')
        self.video_label.setPixmap(pixmap)
        self.video_label.setAlignment(Qt.AlignCenter)

    def update_frame(self):
        if not self.camera_on:
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            barcodes = self.decode_barcodes(frame)

            for barcode in barcodes:
                (x, y, w, h) = barcode.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                barcode_data = barcode.data.decode('utf-8')
                barcode_type = barcode.type

                if barcode_type != "EAN13":
                    continue

                text = f"{barcode_data} ({barcode_type})"

                if any(book['isbn'] == barcode_data for book in self.scanned_books):
                    self.update_status("Entry already exists")
                    self.play_sound("status_change")
                    self.flash_status("yellow")
                else:
                    book_details = get_book_details(barcode_data)
                    if book_details:
                        self.show_book_details(barcode_data, book_details)
                        self.scanned_books.append({
                            'isbn': barcode_data,
                            'details': book_details,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        self.save_scanned_books()
                        self.play_sound("scan_success")
                        self.flash_status("green")
                    else:
                        self.update_status("Invalid barcode")
                        self.play_sound("scan_error")
                        self.flash_status("red")

                cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            img = QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
            pix = QPixmap.fromImage(img)
            self.video_label.setPixmap(pix)


    def flash_status(self, color):
        if color == "green":
            self.status_label.setStyleSheet("background-color: green; color: black;")
        elif color == "yellow":
            self.status_label.setStyleSheet("background-color: yellow; color: black;")
        elif color == "red":
            self.status_label.setStyleSheet("background-color: red; color: black;")
        self.flash_timer.start(500)


    def reset_flash(self):
        self.status_label.setStyleSheet("")


    def show_book_details(self, isbn, book_details, source="SCANNED"):
        self.details_text.clear()
        self.details_text.append(f"Title: {book_details['Title']}")
        self.details_text.append(f"Author: {book_details['Author']}")
        self.details_text.append(f"Publisher: {book_details['Publisher']}")
        self.details_text.append(f"Published Date: {book_details['Edition']}")
        self.details_text.append(f"Description: {book_details['Description']}")
        self.details_text.append(f"Pages: {book_details['Pages']}")
        self.details_text.append(f"Genre: {book_details['Genre']}")
        self.details_text.append(f"Language: {book_details['Language']}")

        self.book_list.addItem(f"{isbn} - {book_details['Title']}")
        self.process_list.addItem(f"{source}: {isbn} - {book_details['Title']}")

    def display_selected_book_details(self, isbn):
        book = next((book for book in self.scanned_books if book['isbn'] == isbn), None)
        if book:
            self.details_text.clear()
            self.details_text.append(f"Title: {book['details']['Title']}")
            self.details_text.append(f"Author: {book['details']['Author']}")
            self.details_text.append(f"Publisher: {book['details']['Publisher']}")
            self.details_text.append(f"Published Date: {book['details']['Edition']}")
            self.details_text.append(f"Description: {book['details']['Description']}")
            self.details_text.append(f"Pages: {book['details']['Pages']}")
            self.details_text.append(f"Genre: {book['details']['Genre']}")
            self.details_text.append(f"Language: {book['details']['Language']}")

    def update_status(self, message, color=""):
        self.status_label.setText(message)
        self.flash_status(color)

    def delete_selected_book(self):
        selected_item = self.book_list.currentItem()
        if not selected_item:
            self.update_status("No book selected")
            self.flash_status("red")
            return

        isbn = selected_item.text().split(' - ')[0]
        self.scanned_books = [book for book in self.scanned_books if book['isbn'] != isbn]
        self.save_scanned_books()

        self.book_list.takeItem(self.book_list.row(selected_item))
        self.details_text.clear()
        self.update_status(f"Deleted book with ISBN: {isbn}")
        self.flash_status("green")

    def save_scanned_books(self):
        try:
            with open('assets/data/scanned_books.csv', 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['isbn', 'title', 'author', 'publisher', 'publish_date', 'description', 'pages', 'genre', 'language', 'timestamp']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for book in self.scanned_books:
                    writer.writerow({
                        'isbn': book['isbn'],
                        'title': book['details']['Title'],
                        'author': book['details']['Author'],
                        'publisher': book['details']['Publisher'],
                        'publish_date': book['details']['Edition'],
                        'description': book['details']['Description'],
                        'pages': book['details']['Pages'],
                        'genre': book['details']['Genre'],
                        'language': book['details']['Language'],
                        'timestamp': book['timestamp']
                    })
        except IOError as e:
            print(f"Error saving scanned books: {e}")

    def load_scanned_books(self):
        try:
            with open('assets/data/scanned_books.csv', 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    self.scanned_books.append({
                        'isbn': row['isbn'],
                        'details': {
                            'Title': row['title'],
                            'Author': row['author'],
                            'Publisher': row['publisher'],
                            'Edition': row['publish_date'],
                            'Description': row['description'],
                            'Pages': row['pages'],
                            'Genre': row['genre'],
                            'Language': row['language']
                        },
                        'timestamp': row['timestamp']
                    })
                    self.book_list.addItem(f"{row['isbn']} - {row['title']}")
        except FileNotFoundError:
            pass
        except IOError as e:
            print(f"Error loading scanned books: {e}")

    def display_selected_book_details_wrapper(self, item):
        isbn = item.text().split(' - ')[0]
        self.display_selected_book_details(isbn)

    def play_sound(self, sound_type):
        if sound_type == "scan_success":
            winsound.Beep(1000, 200)
        elif sound_type == "scan_error":
            winsound.Beep(500, 400)
        elif sound_type == "status_change":
            winsound.Beep(800, 300)
        else:
            print(f"Unknown sound type: {sound_type}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    scanner = ISBNScanner()
    scanner.show()
    sys.exit(app.exec_())
