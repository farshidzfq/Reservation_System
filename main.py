import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QDialog, QLabel, QLineEdit, QFormLayout, QMessageBox
from PyQt5.QtCore import pyqtSignal

# Constants for admin credentials
ADMIN_USERNAME = "1"
ADMIN_PASSWORD = "1"

class DataManager:
    def __init__(self, db_name='travel_data.db'):
        self.db_name = db_name

    def get_data(self, table_name):
        query = f"SELECT * FROM {table_name}"
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def add_entry(self, table_name, entry_data):
        columns = self.get_table_columns(table_name)
        placeholders = ', '.join(['?'] * len(entry_data))
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(query, entry_data)
        conn.commit()
        conn.close()

    def get_table_columns(self, table_name):
        query = f"PRAGMA table_info({table_name})"
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        return columns

    def update_entry(self, table_name, item_id, entry_data):
        columns = self.get_table_columns(table_name)
        set_clause = ', '.join(f"{col} = ?" for col in columns[1:])  # Skip ID column
        query = f"UPDATE {table_name} SET {set_clause} WHERE {columns[0]} = ?"
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(query, entry_data[1:] + [item_id])  # Skip the first column (ID) in entry_data
        conn.commit()
        conn.close()

    def delete_entry(self, table_name, item_id):
        query = f"DELETE FROM {table_name} WHERE id = ?"
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(query, (item_id,))
        conn.commit()
        conn.close()

class CartManager:
    def __init__(self):
        self.cart = []

    def add_to_cart(self, item):
        self.cart.append(item)

    def remove_from_cart(self, index):
        if 0 <= index < len(self.cart):
            del self.cart[index]

    def get_cart(self):
        return self.cart

class AddEntryDialog(QDialog):
    def __init__(self, category, data_manager, item=None):
        super().__init__()
        self.category = category
        self.data_manager = data_manager
        self.item = item
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"{'Edit' if self.item else 'Add'} {self.category} Entry")
        layout = QFormLayout()
        
        self.line_edits = {}
        columns = self.data_manager.get_table_columns(self.category)
        for i, column in enumerate(columns):
            line_edit = QLineEdit()
            if self.item:
                line_edit.setText(str(self.item[i]))
            layout.addRow(column, line_edit)
            self.line_edits[column] = line_edit

        action_button = QPushButton("Edit" if self.item else "Add")
        action_button.clicked.connect(self.edit_entry if self.item else self.add_entry)
        layout.addWidget(action_button)

        self.setLayout(layout)

    def add_entry(self):
        data = [self.line_edits[column].text() for column in self.line_edits]
        try:
            self.data_manager.add_entry(self.category, data)
            QMessageBox.information(self, 'Success', 'Entry added successfully')
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, 'Error', f"An error occurred: {e}")

    def edit_entry(self):
        data = [self.line_edits[column].text() for column in self.line_edits]
        item_id = self.item[0]  # Assuming the first column is the ID
        try:
            self.data_manager.update_entry(self.category, item_id, data)
            QMessageBox.information(self, 'Success', 'Entry updated successfully')
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, 'Error', f"An error occurred: {e}")

class ListEntriesDialog(QDialog):
    item_added = pyqtSignal(tuple)  # Signal to emit the selected item as a tuple

    def __init__(self, category, data, parent=None, is_edit=False, is_delete=False, data_manager=None):
        super().__init__(parent)
        self.category = category
        self.data = data
        self.is_edit = is_edit
        self.is_delete = is_delete
        self.data_manager = data_manager
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"{self.category} List")
        layout = QVBoxLayout()

        self.buttons = []
        for entry in self.data:
            entry_str = ', '.join(str(field) for field in entry)
            button = QPushButton(entry_str)
            if self.is_edit:
                button.clicked.connect(lambda _, e=entry: self.edit_entry(e))
            elif self.is_delete:
                button.clicked.connect(lambda _, e=entry: self.delete_entry(e))
            else:
                button.clicked.connect(lambda _, e=entry: self.add_to_cart(e))  # Bind entry to lambda
            layout.addWidget(button)
            self.buttons.append(button)

        self.setLayout(layout)

    def add_to_cart(self, item):
        self.item_added.emit(item)  # Emit the selected item as a tuple
        QMessageBox.information(self, 'Added to Cart', f'{item} added to cart')
        self.accept()  # Close the dialog after adding to cart

    def edit_entry(self, item):
        dialog = AddEntryDialog(self.category, self.data_manager, item=item)
        dialog.exec_()

    def delete_entry(self, item):
        item_id = item[0]  # Assuming the first column is the ID
        self.data_manager.delete_entry(self.category, item_id)
        QMessageBox.information(self, 'Deleted', f'Entry {item} deleted successfully')
        self.accept()

class AdminLoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Admin Login')
        self.setFixedSize(300, 150)

        layout = QFormLayout()

        self.username = QLineEdit(self)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        layout.addRow(QLabel('Username:'), self.username)
        layout.addRow(QLabel('Password:'), self.password)

        self.loginButton = QPushButton('Login', self)
        self.loginButton.clicked.connect(self.handleLogin)
        layout.addWidget(self.loginButton)

        self.setLayout(layout)

    def handleLogin(self):
        if self.username.text() == ADMIN_USERNAME and self.password.text() == ADMIN_PASSWORD:
            self.accept()
        else:
            QMessageBox.warning(self, 'Error', 'Invalid username or password')

class AdminMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Admin Menu')
        self.setFixedSize(400, 400)

        layout = QVBoxLayout()

        self.flightButton = QPushButton('Manage Flights', self)
        self.trainButton = QPushButton('Manage Trains', self)
        self.hotelButton = QPushButton('Manage Hotels', self)
        self.tourButton = QPushButton('Manage Tours', self)

        self.flightButton.clicked.connect(lambda: self.manageCategory('Flight'))
        self.trainButton.clicked.connect(lambda: self.manageCategory('Train'))
        self.hotelButton.clicked.connect(lambda: self.manageCategory('Hotel'))
        self.tourButton.clicked.connect(lambda: self.manageCategory('Tour'))

        layout.addWidget(self.flightButton)
        layout.addWidget(self.trainButton)
        layout.addWidget(self.hotelButton)
        layout.addWidget(self.tourButton)

        self.setLayout(layout)

    def manageCategory(self, category):
        dialog = ManageCategoryDialog(category, self.data_manager)
        dialog.exec_()

class ManageCategoryDialog(QDialog):
    def __init__(self, category, data_manager):
        super().__init__()
        self.category = category
        self.data_manager = data_manager
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f'Manage {self.category}')
        layout = QVBoxLayout()

        self.addButton = QPushButton(f'Add {self.category}')
        self.editButton = QPushButton(f'Edit {self.category}')
        self.deleteButton = QPushButton(f'Delete {self.category}')

        self.addButton.clicked.connect(self.addEntry)
        self.editButton.clicked.connect(self.editEntry)
        self.deleteButton.clicked.connect(self.deleteEntry)

        layout.addWidget(self.addButton)
        layout.addWidget(self.editButton)
        layout.addWidget(self.deleteButton)

        self.setLayout(layout)

    def addEntry(self):
        dialog = AddEntryDialog(self.category, self.data_manager)
        dialog.exec_()

    def editEntry(self):
        data = self.data_manager.get_data(self.category)
        dialog = ListEntriesDialog(self.category, data, is_edit=True, data_manager=self.data_manager)
        dialog.exec_()

    def deleteEntry(self):
        data = self.data_manager.get_data(self.category)
        dialog = ListEntriesDialog(self.category, data, is_delete=True, data_manager=self.data_manager)
        dialog.exec_()

class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.cart_manager = CartManager()
        self.data_manager = DataManager()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Main Menu')
        self.setFixedSize(400, 400)

        layout = QVBoxLayout()

        self.flightButton = QPushButton('Book Flights', self)
        self.trainButton = QPushButton('Book Trains', self)
        self.hotelButton = QPushButton('Book Hotels', self)
        self.tourButton = QPushButton('Book Tours', self)
        self.cartButton = QPushButton('View Cart', self)
        self.adminButton = QPushButton('Admin Login', self)

        self.flightButton.clicked.connect(lambda: self.showItems('Flight'))
        self.trainButton.clicked.connect(lambda: self.showItems('Train'))
        self.hotelButton.clicked.connect(lambda: self.showItems('Hotel'))
        self.tourButton.clicked.connect(lambda: self.showItems('Tour'))
        self.cartButton.clicked.connect(self.showCart)
        self.adminButton.clicked.connect(self.adminLogin)

        layout.addWidget(self.flightButton)
        layout.addWidget(self.trainButton)
        layout.addWidget(self.hotelButton)
        layout.addWidget(self.tourButton)
        layout.addWidget(self.cartButton)
        layout.addWidget(self.adminButton)

        self.setLayout(layout)

    def showItems(self, category):
        data = self.data_manager.get_data(category)
        dialog = ListEntriesDialog(category, data)
        dialog.item_added.connect(self.cart_manager.add_to_cart)
        dialog.exec_()

    def showCart(self):
        cart_items = self.cart_manager.get_cart()
        cart_str = '\n'.join(', '.join(str(field) for field in item) for item in cart_items)
        QMessageBox.information(self, 'Cart', f"Items in Cart:\n{cart_str}")

    def adminLogin(self):
        dialog = AdminLoginDialog()
        if dialog.exec_() == QDialog.Accepted:
            self.adminMenu = AdminMenu()
            self.adminMenu.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_menu = MainMenu()
    main_menu.show()
    sys.exit(app.exec_())
