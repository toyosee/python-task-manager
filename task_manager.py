import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                             QListWidget, QLineEdit, QHBoxLayout, QRadioButton, QLabel, 
                             QButtonGroup, QTextEdit, QMessageBox, QListWidgetItem, QMenu)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QBrush, QColor
from datetime import datetime

class TaskManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Manager")
        self.setGeometry(100, 100, 600, 400)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Navigation Bar
        self.nav_layout = QHBoxLayout()
        self.layout.addLayout(self.nav_layout)

        self.home_button = QPushButton("Home")
        self.view_all_button = QPushButton("View All Tasks")
        self.add_task_button_nav = QPushButton("Add Task")
        self.nav_layout.addWidget(self.home_button)
        self.nav_layout.addWidget(self.view_all_button)
        self.nav_layout.addWidget(self.add_task_button_nav)

        self.home_button.clicked.connect(self.show_home)
        self.view_all_button.clicked.connect(self.show_all_tasks)
        self.add_task_button_nav.clicked.connect(self.show_add_task)

        # Home Page
        self.home_label = QLabel("Welcome to Task Manager")
        self.home_label.setAlignment(Qt.AlignCenter)
        self.home_label.setFont(QFont("Arial", 20))
        self.layout.addWidget(self.home_label)

        # Task List
        self.task_list = QListWidget()
        self.task_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.show_context_menu)
        self.task_list.itemClicked.connect(self.edit_task)
        self.layout.addWidget(self.task_list)
        self.task_list.hide()

        # Add Task Section
        self.add_task_widget = QWidget()
        self.add_task_layout = QVBoxLayout()
        self.add_task_widget.setLayout(self.add_task_layout)

        self.task_title = QLineEdit()
        self.task_title.setPlaceholderText("Task Title")
        self.add_task_layout.addWidget(self.task_title)

        self.task_body = QTextEdit()
        self.task_body.setPlaceholderText("Task Body")
        self.add_task_layout.addWidget(self.task_body)

        self.status_layout = QHBoxLayout()
        self.add_task_layout.addLayout(self.status_layout)

        self.pending_button = QRadioButton("Pending")
        self.pending_button.setChecked(True)
        self.completed_button = QRadioButton("Completed")
        self.status_group = QButtonGroup()
        self.status_group.addButton(self.pending_button)
        self.status_group.addButton(self.completed_button)
        self.status_layout.addWidget(self.pending_button)
        self.status_layout.addWidget(self.completed_button)

        self.add_task_button = QPushButton("Add Task")
        self.add_task_layout.addWidget(self.add_task_button)
        self.add_task_button.clicked.connect(self.add_task)

        self.layout.addWidget(self.add_task_widget)
        self.add_task_widget.hide()

        self.current_task_id = None  # To track the task being edited

        self.connect_db()
        self.show_home()

    def connect_db(self):
        self.conn = sqlite3.connect("tasks.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT,
                body TEXT,
                status TEXT,
                timestamp TEXT
            )
        """)
        self.conn.commit()

    def add_task(self):
        title = self.task_title.text()
        body = self.task_body.toPlainText()
        status = "Pending" if self.pending_button.isChecked() else "Completed"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if title and body:
            if self.current_task_id:  # Update existing task
                self.cursor.execute("""
                    UPDATE tasks SET title = ?, body = ?, status = ?, timestamp = ?
                    WHERE id = ?
                """, (title, body, status, timestamp, self.current_task_id))
            else:  # Add new task
                self.cursor.execute("""
                    INSERT INTO tasks (title, body, status, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (title, body, status, timestamp))
            self.conn.commit()
            self.load_tasks()
            self.clear_input_fields()
            self.current_task_id = None  # Reset after saving
        else:
            QMessageBox.warning(self, "Warning", "Title and Body cannot be empty!")

    def load_tasks(self):
        self.task_list.clear()
        self.cursor.execute("SELECT * FROM tasks ORDER BY status, timestamp")
        tasks = self.cursor.fetchall()
        for task in tasks:
            item = QListWidgetItem(f"{task[1]}\n{task[2]}\n{task[3]}\n{task[4]}")
            item.setData(Qt.UserRole, task[0])  # Store task ID in the item
            if task[3] == "Completed":
                item.setFont(QFont("", -1, QFont.StrikeOut))
                item.setForeground(QBrush(QColor("grey")))
                self.task_list.addItem(item)  # Add completed tasks to the bottom
            else:
                self.task_list.insertItem(0, item)  # Add pending tasks to the top

    def clear_input_fields(self):
        self.task_title.clear()
        self.task_body.clear()
        self.pending_button.setChecked(True)

    def show_context_menu(self, position):
        item = self.task_list.itemAt(position)
        if item:
            menu = QMenu()
            mark_completed_action = menu.addAction("Mark as Completed")
            mark_pending_action = menu.addAction("Mark as Pending")
            delete_action = menu.addAction("Delete Task")
            action = menu.exec_(self.task_list.mapToGlobal(position))
            if action == mark_completed_action:
                self.update_task_status(item, "Completed")
            elif action == mark_pending_action:
                self.update_task_status(item, "Pending")
            elif action == delete_action:
                self.delete_task(item)

    def update_task_status(self, item, status):
        task_id = item.data(Qt.UserRole)
        self.cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        self.conn.commit()
        self.load_tasks()

    def delete_task(self, item):
        task_id = item.data(Qt.UserRole)
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        self.load_tasks()

    def edit_task(self, item):
        task_id = item.data(Qt.UserRole)
        self.current_task_id = task_id
        self.cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = self.cursor.fetchone()
        if task:
            self.task_title.setText(task[1])
            self.task_body.setText(task[2])
            if task[3] == "Completed":
                self.completed_button.setChecked(True)
            else:
                self.pending_button.setChecked(True)
            self.show_add_task()

    def show_home(self):
        self.task_list.hide()
        self.add_task_widget.hide()
        self.home_label.show()

    def show_add_task(self):
        self.task_list.hide()
        self.home_label.hide()
        self.add_task_widget.show()

    def show_all_tasks(self):
        self.home_label.hide()
        self.add_task_widget.hide()
        self.task_list.show()
        self.load_tasks()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskManager()
    window.show()
    sys.exit(app.exec_())