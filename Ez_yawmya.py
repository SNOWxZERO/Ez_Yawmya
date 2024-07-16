import subprocess
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QListWidget, QDateEdit, QDialog, QCompleter
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtCore import QDate, Qt, QLocale
from reportlab.lib.pagesizes import letter , A4
from reportlab.lib.colors import red,black
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import arabic_reshaper
from bidi.algorithm import get_display
import pandas as pd
import os
import ast

class FirstDayDataDialog(QDialog):
    '''
    A dialog window for entering the initial data.

    This dialog allows the user to enter the initial network credit and cash balance for the day.

    Attributes:
        credit_label (QLabel): The label for the network credit input field.
        credit_entry (QLineEdit): The input field for entering the network credit.
        cash_label (QLabel): The label for the cash balance input field.
        cash_entry (QLineEdit): The input field for entering the cash balance.
        submit_button (QPushButton): The button for submitting the data.

    Methods:
        __init__(self, parent=None): Initializes the dialog window.
        initUI(self): Sets up the user interface of the dialog window.
        get_data(self): Retrieves the entered credit and cash values.
        
    '''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setObjectName('FirstDayDataDialog')
        self.setWindowTitle('إدخال البيانات الأولية')

        layout = QVBoxLayout()

        self.credit_label = QLabel('رصيد الشبكة في اليوم السابق:')
        self.credit_entry = QLineEdit('0.00')
        layout.addWidget(self.credit_label)
        layout.addWidget(self.credit_entry)

        self.cash_label = QLabel('رصيد النقد في اليوم السابق:')
        self.cash_entry = QLineEdit('0.00')
        layout.addWidget(self.cash_label)
        layout.addWidget(self.cash_entry)

        self.submit_button = QPushButton('إدخال البيانات')
        self.submit_button.clicked.connect(self.accept)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)
        self.setStyleSheet('''
            QWidget#FirstDayDataDialog {
                background-color: #092635;
            }
        ''')

    def get_data(self):
        '''
        Retrieves the entered credit and cash values.

        Returns:
            tuple: A tuple containing the credit and cash values entered by the user.

        '''
        try:
            credit =  float(self.credit_entry.text())
            cash = float(self.cash_entry.text())
        except ValueError:
            credit = 0.0
            cash = 0.0
        return credit, cash

class RestaurantFinanceApp(QWidget):
    """
    A class representing the finance management application for a restaurant.

    This class provides functionality for managing daily expenses, income, and generating financial reports.

    Attributes:
        all_expanses (set): A set to store all the expenses.
        expenses (list): A list to store the daily expenses.
        today_date (str): The current date in the format 'yyyy-MM-dd'.
        today_cash (int): The total cash income for the current day.
        today_credit (int): The total credit income for the current day.
        today_credit_withdraw (int): The total credit withdrawal for the current day.
        last_day_credit (int): The total credit income from the previous day.
        last_day_cash (int): The total cash income from the previous day.
        excel_file (str): The file path of the Excel file used for data storage.
        suggestions_file (str): The file path of the suggestions file.

    Methods:
        initUI(): Initializes the user interface of the application.
        load_suggestions(): Loads the suggestions from the suggestions file.
        load_data(date: str): Loads the data for the specified date.
        on_date_changed(): Handles the date change event.
        calculate_totals(): Calculates and displays the total sellings, credit, and cash.
        save_daily_data(): Saves the daily data to the Excel file.
    """  
    def __init__(self):
        
        super().__init__()
        
        # This is for Auto-Complete in expense name field
        self.all_expanses = set()
        
        # Day Data
        self.expenses = []
        self.today_date = QDate.currentDate().toString('yyyy-MM-dd')
        self.today_cash = 0
        self.today_credit = 0
        self.today_credit_withdraw = 0

        # Last Day Data
        self.last_day_credit = 0
        self.last_day_cash = 0

        # App-data files
        self.excel_file = 'data/restaurant_finance.xlsx'
        self.suggestions_file = 'data/suggestions.txt'
        
        self.load_suggestions()
        self.initUI()
        self.load_data(self.today_date)
            
    def initUI(self):
        '''
        Initializes the user interface of the application.      
        '''
        self.setObjectName('MainWindow')
        self.setWindowTitle('مدير المالية لمطعم الأسماك')
        self.resize(800, 600)
        
        # Load custom font
        font_id = QFontDatabase.addApplicationFont("data/Rubik-Regular.ttf")
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                custom_font = QFont(font_families[0], 15)  # Set the font size here
                QApplication.setFont(custom_font)    
        
        # Styling the App
        app.setStyleSheet('''
            /* Styling for QMessageBox */
            QMessageBox {
            background-color: #092635;
            }
            
            /* Styling for horizontal QScrollBar */
            QScrollBar:horizontal 
            {
            background-color: #092635;
            height: 15px;
            margin: 3px 15px 3px 15px;
            border: 1px transparent #092635;
            border-radius: 4px;
            }               
            /* Styling for vertical QScrollBar */
            QScrollBar
            {
            background-color: #092635;
            width: 15px;
            margin: 15px 3px 15px 3px;
            border: 1px transparent #092635;
            border-radius: 4px;
            }

            /* Styling for QScrollBar handle */
            QScrollBar::handle
            {
            background-color: #74E291;         
            min-height: 5px;
            border-radius: 4px;
            }

            /* Styling for QScrollBar up arrow */
            QScrollBar::sub-line
            {
            margin: 3px 0px 3px 0px;
            border-image: url(:/qss_icons/rc/up_arrow_disabled.png);
            height: 10px;
            width: 10px;
            subcontrol-position: top;
            subcontrol-origin: margin;
            }

            /* Styling for QScrollBar down arrow */
            QScrollBar::add-line
            {
            margin: 3px 0px 3px 0px;
            border-image: url(:/qss_icons/rc/down_arrow_disabled.png);
            height: 10px;
            width: 10px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
            }

            /* Styling for QScrollBar up arrow on hover or click */
            QScrollBar::sub-line:hover,QScrollBar::sub-line:on
            {
            border-image: url(:/qss_icons/rc/up_arrow.png);
            height: 10px;
            width: 10px;
            subcontrol-position: top;
            subcontrol-origin: margin;
            }

            /* Styling for QScrollBar down arrow on hover or click */
            QScrollBar::add-line:hover, QScrollBar::add-line:on
            {
            height: 10px;
            width: 10px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
            }

            /* Styling for QScrollBar up and down arrows */
            QScrollBar::up-arrow, QScrollBar::down-arrow
            {
            background: none;
            }

            /* Styling for QScrollBar add and sub pages */
            QScrollBar::add-page, QScrollBar::sub-page
            {
            background: none;
            } 
            
            /* Styling for QWidget */
            QWidget {
            font-family: Rubik;
            color: #9EC8B9;
            }
            
            /* Styling for QLabel */
            QLabel {
            font-size: 20px;
            }
            
            /* Styling for QLineEdit */
            QLineEdit {
            background-color: #5C8374;
            color: #FDFFE2;
            border-radius: 5px;
            padding: 3px;
            }
            
            /* Styling for QLineEdit on hover */
            QLineEdit::hover 
            {
            background-color: #6F9484;
            }
            
            /* Styling for QLineEdit on focus */
            QLineEdit::focus 
            {
            border: 3px solid #74E291;
            }
            
            /* Styling for QListView */
            QListView {
            background-color: #9EC8B9;
            color: #092635 ;
            font-size: 20px;
            border-radius: 5px;
            padding: 5px;
            }

            /* Styling for QListView item */
            QListView::item {
            height: 30px;
            }

            /* Styling for selected QListView item */
            QListView::item:selected {
            background-color: #9AD0C2;
            color: #092635;
            }
            
            /* Styling for QPushButton */
            QPushButton {
            background-color: #F1FADA;
            color: #1B4242;
            padding: 5px;
            border-radius: 5px;
            }
            
            /* Styling for QPushButton on hover */
            QPushButton:hover {
            background-color: #9AD0C2;
            color: #F1FADA;
            }
            
            /* Styling for QPushButton on press */
            QPushButton:pressed {
            background-color: #2D9596;
            color: #F1FADA;
            }
            
            /* Styling for QListWidget */
            QListWidget {
            background-color: #5C8374;
            color: #FDFFE2;
            font: Rubik;
            font-size: 18px;
            padding: 5px;
            border-radius: 5px;
            }
            
            /* Styling for QDateEdit */
            QDateEdit {
            background-color: #9EC8B9;
            border-radius: 10px;
            border: 2px solid #5C8374;
            padding: 2px;
            color: #092635;
            }
            
            /* Styling for QDateEdit drop-down button */
            QDateEdit:drop-down {
            width: 37px;
            height: 37px;
            position: absolute;
            right: 5px;
            border-radius: 15px;
            }
            
            /* Styling for QDateEdit drop-down arrow */
            QDateEdit::down-arrow {
            image: url('data/calendar_icon.png');
            width: 37px;
            height: 37px;
            }
            
            /* Styling for QDateEdit calendar widget */
            QDateEdit::calendarWidget {
            background-color: #9EC8B9;
            color: #092635;
            font-size: 25px;
            }
        ''')
        
        main_layout = QHBoxLayout()
        # Create left layout for totals
        left_layout = QVBoxLayout()
        
        # Increase left layout size
        left_layout.setSpacing(10)  # Increase spacing between components
        # Increase right layout size
        main_layout.setSpacing(10)  # Increase spacing between components
        main_layout.setContentsMargins(10, 10, 10, 10)  # Increase margins


        # Date picker
        self.date_picker_label = QLabel('اختر التاريخ:')
        self.date_picker = QDateEdit(calendarPopup=True)
        self.date_picker.calendarWidget().setStyleSheet('background-color: #9EC8B9; color: #092635; font-size: 23px;')
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setDisplayFormat('yyyy-MM-dd')
        self.date_picker.dateChanged.connect(self.on_date_changed)

        left_layout.addWidget(self.date_picker_label)
        left_layout.addWidget(self.date_picker)

        # Create input fields for income
        self.cash_label = QLabel('دخل نقدي:')
        self.cash_entry = QLineEdit()
        self.cash_entry.setAlignment(Qt.AlignRight)

        self.credit_label = QLabel('دخل الشبكة:')
        self.credit_entry = QLineEdit()
        self.credit_entry.setAlignment(Qt.AlignRight)

        self.credit_withdraw_label = QLabel('سحب الشبكة:')
        self.credit_withdraw_entry = QLineEdit()
        self.credit_withdraw_entry.setAlignment(Qt.AlignRight)

        # Create Button to calculate totals and show them
        self.calculate_button = QPushButton('احسب الإجماليات')
        self.calculate_button.setStyleSheet('''
            QPushButton {
            background-color: #74E291;
            color: #092635;
            }
            QPushButton:hover {
            background-color: #9AD0C2;
            color: #F1FADA;
            }
            QPushButton:pressed {
            background-color: #1B4242;
            color: #F1FADA;
            }''')
        self.calculate_button.clicked.connect(self.calculate_totals)

        left_layout.addWidget(self.cash_label)
        left_layout.addWidget(self.cash_entry)
        left_layout.addWidget(self.credit_label)
        left_layout.addWidget(self.credit_entry)
        left_layout.addWidget(self.credit_withdraw_label)
        left_layout.addWidget(self.credit_withdraw_entry)
        left_layout.addWidget(self.calculate_button)

        # Create labels to display results
        self.total_sellings_label = QLabel('إجمالي المبيعات:')
        self.total_sellings_result = QLabel('')
        self.total_sellings_result.setAlignment(Qt.AlignRight)

        self.total_credit_label = QLabel('إجمالي الشبكة:')
        self.total_credit_result = QLabel('')
        self.total_credit_result.setAlignment(Qt.AlignRight)

        self.total_cash_label = QLabel('إجمالي النقد:')
        self.total_cash_result = QLabel('')
        self.total_cash_result.setAlignment(Qt.AlignRight)

        left_layout.addWidget(self.total_sellings_label)
        left_layout.addWidget(self.total_sellings_result)
        left_layout.addWidget(self.total_credit_label)
        left_layout.addWidget(self.total_credit_result)
        left_layout.addWidget(self.total_cash_label)
        left_layout.addWidget(self.total_cash_result)

        # Create button to save data
        self.save_data_button = QPushButton('احفظ بيانات اليومية')
        self.save_data_button.clicked.connect(self.save_daily_data)
        left_layout.addWidget(self.save_data_button)

        # Create button to save report as a PDF
        self.save_pdf_button = QPushButton('احفظ التقرير كملف PDF')
        self.save_pdf_button.setStyleSheet('''  
            QPushButton {
            background-color: #EE1E4E;
            color: #F6EEC9;
            border: 2px solid #F6EEC9;
            border-style: outset;
            }
            QPushButton:hover {
            background-color: #F6EFD9;
            color: #EE4E4E;
            border: 2px solid #EE4E4E;
            border-style: inset;
            }
            QPushButton:pressed {
            background-color: #EE4E4E;
            color: #F6EEC9;
            }
        ''')
        self.save_pdf_button.clicked.connect(self.save_report_as_pdf)
        left_layout.addWidget(self.save_pdf_button)

        main_layout.addLayout(left_layout)

        # Create right layout for expenses
        right_layout = QVBoxLayout()
        
        self.expense_name_label = QLabel('اسم المصروف:')
        self.expense_name_entry = QLineEdit()
        completer = QCompleter(list(self.all_expanses))
        self.expense_name_entry.setCompleter(completer)

        self.expense_amount_label = QLabel('مبلغ المصروف:')
        self.expense_amount_entry = QLineEdit()
        self.expense_amount_entry.setAlignment(Qt.AlignRight)

        self.add_expense_button = QPushButton('أضف المصروف')
        self.add_expense_button.setStyleSheet('''
            QPushButton {
            background-color: #74E291;
            color: #092635;
            }
            QPushButton:hover {
            background-color: #9AD0C2;
            color: #F1FADA;
            }
            QPushButton:pressed {
            background-color: #1B4242;
            color: #F1FADA;
            }''')
        self.add_expense_button.clicked.connect(self.add_expense)

        right_layout.addWidget(self.expense_name_label)
        right_layout.addWidget(self.expense_name_entry)
        right_layout.addWidget(self.expense_amount_label)
        right_layout.addWidget(self.expense_amount_entry)
        right_layout.addWidget(self.add_expense_button)

        # Create list to display expenses
        self.expense_list = QListWidget()
        self.expense_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.expense_list.itemClicked.connect(self.on_expense_selected)
        right_layout.addWidget(self.expense_list)

        # Create label to display total expenses
        self.total_expenses_label = QLabel('إجمالي المصروفات:')
        self.total_expenses_result = QLabel('0.00')
        self.total_expenses_result.setAlignment(Qt.AlignRight)

        right_layout.addWidget(self.total_expenses_label)
        right_layout.addWidget(self.total_expenses_result)

        # Add edit and delete buttons
        self.edit_expense_button = QPushButton('تعديل المصروف')
        self.edit_expense_button.clicked.connect(self.edit_expense)
        right_layout.addWidget(self.edit_expense_button)

        self.delete_expense_button = QPushButton('حذف المصروف')
        self.delete_expense_button.clicked.connect(self.delete_expense)
        self.delete_expense_button.setStyleSheet('''  
            QPushButton {
            background-color: #EE1E4E;
            color: #F6EEC9;
            border: 2px solid #F6EEC9;
            border-style: outset;
            }
            QPushButton:hover {
            background-color: #F6EFD9;
            color: #EE4E4E;
            border: 2px solid #EE4E4E;
            border-style: inset;
            }
            QPushButton:pressed {
            background-color: #EE4E4E;
            color: #F6EEC9;
            }
        ''')
        right_layout.addWidget(self.delete_expense_button)

        
        
        main_layout.addLayout(right_layout)

        self.setLayout(main_layout)
        # Setting background for the application to be dark
        self.setStyleSheet('''
            QWidget#MainWindow 
            {
            background-color: #092635;
            }
        ''')
    
    # Initiation Functions :
   
    def show_first_day_dialog(self):
        '''
        Display a dialog to get the initial data for the first day.
        
        This dialog is shown in 4 cases :
            - The first app initiation ( Excel file that contains the DataFrame does not exist )
            - The DataFrame exists but Empty
            - Idx of the selected Date == 0
            - Idx of the selected Date does not exist and the date is earlier than first date --( that has idx of 0 )--

        This method shows a dialog to the user where they can enter the initial data for the first day.
        If the user accepts the dialog, the entered data is stored in the variables `last_day_credit` and `last_day_cash`.
        If the user cancels the dialog, the variables `last_day_credit` and `last_day_cash` are set to 0.
        A warning message is displayed if no data is entered, and the default value of 0 is used.

        After getting the initial data, an initial row is added to the DataFrame with the following columns:
        - Date: The date of the previous day.
        - Cash: 0.
        - Credit: 0.
        - Credit Withdraw: 0.
        - Total Sellings: 0.
        - Total Credit: The value of `last_day_credit`.
        - Total Cash: The value of `last_day_cash`.
        - Total Expenses: 0.
        - Expenses: 'لا توجد مصروفات' (or whatever default value you want).

        The initial row is then saved using the `save_data` method, and the totals are calculated using the `calculate_totals` method.
        '''
        # Display dialog to get initial data for the first day
        dialog = FirstDayDataDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Get data from dialog if accepted
            self.last_day_credit, self.last_day_cash = dialog.get_data()
        else:
            # Set default values if dialog is canceled
            self.last_day_credit, self.last_day_cash = 0, 0
            QMessageBox.warning(self, 'تحذير', 'لم يتم إدخال البيانات الأولية. يتم استخدام القيمة الافتراضية 0.')

        # Get the date of the previous day
        first_date = self.date_picker.date().addDays(-1).toString('yyyy-MM-dd')

        # Add initial row to DataFrame
        initial_row = {
            'Date': first_date,
            'Cash': 0,
            'Credit': 0,
            'Credit Withdraw': 0,
            'Total Sellings': 0,
            'Total Credit': self.last_day_credit,
            'Total Cash': self.last_day_cash,
            'Total Expenses': 0,
            'Expenses': 'لا توجد مصروفات'  # Or whatever default value you want
        }

        # Save initial row to data
        self.save_data(initial_row)

        # Calculate totals
        self.calculate_totals()

    # This is for Auto-Complete in expense name field
    def load_suggestions(self):
        # Check if the suggestions file exists
        if os.path.exists(self.suggestions_file):
            # If it exists, load the suggestions from the file
            with open(self.suggestions_file, 'r', encoding='utf-8') as file:
                self.all_expanses = set(file.read().splitlines())
        else:
            # If it doesn't exist, create an empty file
            with open(self.suggestions_file, 'w', encoding='utf-8') as file:
                file.write('')
                file.close()
    def save_suggestions(self):
        # Save the suggestions to the file
        with open(self.suggestions_file, 'w', encoding='utf-8') as file:
            file.write('\n'.join(self.all_expanses))
    def update_suggestions(self):
        # Update the suggestions in the completer
        completer = QCompleter(list(self.all_expanses))
        self.expense_name_entry.setCompleter(completer)        
    
    # Loading Data Functions :
                          
    def on_date_changed(self):
        # Get the selected date from the date picker and update data shown in the UI
        selected_date = self.date_picker.date().toString('yyyy-MM-dd')
        self.load_data(selected_date)

    def clear_data(self):
        '''
            Clearing the UI elements and Mainly Used Variables
            To get it ready to show new data
        '''
        self.expenses = []
        self.expense_list.clear()
        self.total_expenses_result.setText('0.00')
        self.total_cash_result.setText('0.00')
        self.total_credit_result.setText('0.00')
        self.total_sellings_result.setText('0.00')
        self.cash_entry.setText('0.00')
        self.credit_entry.setText('0.00')
        self.credit_withdraw_entry.setText('0.00')
        self.last_day_cash = 0
        self.last_day_credit = 0
        
    def load_data(self, selected_date):
        """
        Load data from an Excel file and populate the GUI with the corresponding values for the selected date.
        
        Behaviour:
        - If the Excel file exists, read the data from the file.
        - If the Excel file doesn't exist, create a new DataFrame open first day dialog and append a new row with the initial data.
        - If the DataFrame is empty show the first day dialog again (happens in case of app failure in first day dialog)
        
            - After this is the cases when the df exists in good condition for data addition and loading -
        
        - Cheking for date if it exists get the idx of the row if it == 0 show the first day dialog to get last day data (because it is needed)    
        - If it != 0 and the date exists Get the data from the row and apply it to the UI
        - If the Date does not exist and the date is earlier than The first date --(with idx of 0)-- show the first day dialog
        - Else locate where it should be placed and get the last day data from the idx before and show data with last day credit and cash
        
        Parameters:
        - selected_date (str): The selected date in the format 'YYYY-MM-DD'.

        Returns:
        - None

        """
        # Clear previous data
        self.clear_data()
        
        # Check if the Excel file exists
        if os.path.exists(self.excel_file):
            # Read the Excel file
            df = pd.read_excel(self.excel_file)
        else:
            # Create a new DataFrame if the file doesn't exist
            df = pd.DataFrame(columns=['Date', 'Cash', 'Credit', 'Credit Withdraw', 'Total Sellings', 'Total Credit', 'Total Cash', 'Total Expenses', 'Expenses'])
            df.to_excel(self.excel_file, index=False)
            
            # Show the first day dialog to get initial data
            self.show_first_day_dialog()
            
            # Read the Excel file after creating it
            df = pd.read_excel(self.excel_file)
              
        if df.empty:
            # If the DataFrame is empty, show the first day dialog
            self.show_first_day_dialog()
            return      
        
        # Check if the selected date exists in the DataFrame
        date_exists = df['Date'].astype(str).str.contains(selected_date).any()
        
        if date_exists:
            # If the selected date exists, retrieve the data for that date
            idx = df.index[df['Date'].astype(str) == selected_date].tolist()[0]
            
            # Check if the selected date is the first day
            if idx == 0 :
                # If it is the first day, show the first day dialog
                self.show_first_day_dialog()
                return
            
            # Get the data for the selected date and the previous day
            today_data = df.iloc[idx]
            last_day_data = df.iloc[idx-1]
            self.last_day_credit = last_day_data['Total Credit']
            self.last_day_cash = last_day_data['Total Cash']
            
            # Set the values in the UI elements :
            
                # Cash and Credit Totals
            self.cash_entry.setText(f"{today_data['Cash']}")
            self.credit_entry.setText(f"{today_data['Credit']}")
            self.credit_withdraw_entry.setText(f"{today_data['Credit Withdraw']}")
            
            self.total_sellings_result.setText(f"{today_data['Total Sellings']}")
            self.total_credit_result.setText(f"{today_data['Total Credit']}")
            self.total_cash_result.setText(f"{today_data['Total Cash']}")
            
                # Getting expanses
            if today_data['Expenses'] == 'لا توجد مصروفات':
                # No Expanses
                self.expenses = []
            else:
                # Turning Expanses String into a List of tubles of ( name , amount )
                self.expenses = ast.literal_eval(today_data['Expenses'])
                
                # Adding expenses to the UI element
            for name, amount in self.expenses:
                self.expense_list.addItem(f"{name}: {amount:.2f}")
        else:
            # If the selected date doesn't exist, find the first date before the selected date
            last_day_data = df.iloc[0]
            selected_timestamp = pd.Timestamp(selected_date)
            
            # Check if the selected date is before the first date in the DataFrame
            if selected_timestamp < pd.Timestamp(df.iloc[0]['Date']):
                # If it is before the first date, show the first day dialog
                self.show_first_day_dialog()
                return
            
            # Loop through the DataFrame starting from the selected date and go backwards
            for idx in range(len(df) - 1, -1, -1):
                date_in_df = df.iloc[idx]['Date']
                if pd.Timestamp(date_in_df) < selected_timestamp:
                    # Found the first date before the selected date
                    last_day_data = df.iloc[idx]
                    break
            
            # Getting last day data    
            self.last_day_credit = last_day_data['Total Credit']
            self.last_day_cash = last_day_data['Total Cash']
            
            # Set the values in the UI elements
            self.cash_entry.setText('')
            self.credit_entry.setText('')
            self.credit_withdraw_entry.setText('')
            self.total_sellings_result.setText('')
            self.total_credit_result.setText(str(self.last_day_credit))
            self.total_cash_result.setText(str(self.last_day_cash))
            self.total_expenses_result.setText('0.00')
    
    def calculate_totals(self):
        """
        Calculate the totals for cash, credit, credit withdrawal, total expenses, total sellings,
        total credit, total cash, and return the data as a dictionary.

        Returns:
            dict: A dictionary containing the calculated totals and other relevant data.
        """
        try:
            # Getting Main data for equations
            cash = float(self.cash_entry.text()) if self.cash_entry.text() else 0
            credit = float(self.credit_entry.text()) if self.credit_entry.text() else 0
            credit_withdraw = float(self.credit_withdraw_entry.text()) if self.credit_withdraw_entry.text() else 0
            
            # Getting sum of expanses
            total_expenses = sum(amount for _, amount in self.expenses)
            
            # Main Equations
            total_sellings = cash + credit
            total_credit = self.last_day_credit + credit - credit_withdraw
            total_cash = self.last_day_cash + cash + credit_withdraw - total_expenses

            # Settings UI elemnts with the new calculated values
            self.total_expenses_result.setText(f"{total_expenses}")
            self.total_sellings_result.setText(f"{total_sellings}")
            self.total_credit_result.setText(f"{total_credit}")
            self.total_cash_result.setText(f"{total_cash}")
            
            # Returning the data as a dicitonary
            data = {
                'Date': self.date_picker.date().toString('yyyy-MM-dd'),
                'Cash': cash,
                'Credit': credit,
                'Credit Withdraw': credit_withdraw,
                'Total Expenses': total_expenses,
                'Total Sellings': total_sellings,
                'Total Credit': total_credit,
                'Total Cash': total_cash,
                'Expenses': self.expenses if self.expenses else 'لا توجد مصروفات' 
            }
            
            return data
        except ValueError:
            QMessageBox.critical(self, 'خطأ', 'يرجى إدخال مبالغ صالحة للدخل وسحب الشبكة.')

    def save_data(self, data):
        """
        Saves the provided data to an Excel file.
        
        Behaviour:
        - Load DataFrame and check for date existence
        - If DataFrame is empty concat the new data to it and save the file --(In case of first day dialog failure)--
        - If the date does not exist then we are adding a new row of data, sort the DataFrame 
          and saving it then loading it again to change the next days totals values
        -   

        Parameters:
        - data (dict): A dictionary containing the data to be saved. The keys represent the column names and the values represent the corresponding values.

        Returns:
        None
        """

        # Load the existing data
        df = pd.read_excel(self.excel_file)
        
        # Check if the selected date exists in the DataFrame
        date_exists = df['Date'].astype(str).str.contains(data['Date']).any()

        if df.empty:
            # Appending new row
            df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
            df.to_excel(self.excel_file, index=False)
            return

        if not date_exists:
            # Appending new row
            df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
            df.sort_values('Date', inplace=True)
            df.to_excel(self.excel_file, index=False)
            
            # Get the index of the newly added row
            df = pd.read_excel(self.excel_file)
            idx = df.index[df['Date'].astype(str) == data['Date']].tolist()[0]

            if idx == 0:
                # If the new row is the first row, update the totals based on the next row
                current_credit = df.at[1, 'Total Credit']
                current_cash = df.at[1, 'Total Cash']
                credit_difference = data['Total Credit'] - current_credit
                cash_difference = data['Total Cash'] - current_cash
                df.iloc[1:, df.columns.get_loc('Total Credit')] += credit_difference
                df.iloc[1:, df.columns.get_loc('Total Cash')] += cash_difference

            # Update the totals based on credit and cash difrences (in case of idx == 0 diffrences will be 0)
            idx += 1
            credit_difference = data['Credit'] - data['Credit Withdraw']
            cash_difference = data['Cash'] + data['Credit Withdraw'] - data['Total Expenses']

            df.iloc[idx:, df.columns.get_loc('Total Credit')] += credit_difference
            df.iloc[idx:, df.columns.get_loc('Total Cash')] += cash_difference

        else:
            # Getting idx of existing row, Total credit and Total cash
            idx = df.index[df['Date'].astype(str) == data['Date']].tolist()[0]

            current_credit = df.at[idx, 'Total Credit']
            current_cash = df.at[idx, 'Total Cash']

            # Calculating the diffrences
            credit_difference = data['Total Credit'] - current_credit
            cash_difference = data['Total Cash'] - current_cash

            # Update the totals for the next days
            df.iloc[idx:, df.columns.get_loc('Total Credit')] += credit_difference
            df.iloc[idx:, df.columns.get_loc('Total Cash')] += cash_difference

            # Editting the data
            for column in data.keys():
                df.at[idx, column] = data[column]

        # Sort and save the data
        df.sort_values('Date', inplace=True)
        df.to_excel(self.excel_file, index=False)
    
    def save_daily_data(self):
        """
        Saves the daily data by calculating the totals and saving the data.

        Raises:
            ValueError: If all the data is not entered correctly.

        Returns:
            None
        """
        try:
            data = self.calculate_totals() 
            self.save_data(data)
            QMessageBox.information(self, 'نجاح', 'تم حفظ البيانات بنجاح.')
        except ValueError:
            QMessageBox.critical(self, 'خطأ', 'يرجى إدخال جميع البيانات بشكل صحيح.')

    # Expenses List Functions :       

    def on_expense_selected(self, item):
        """
        Updates the expense name and amount entries based on the selected expense item.

        Parameters:
        - item: The selected expense item.

        Returns:
        None
        """
        selected_expense = item.text().split(': ')
        self.expense_name_entry.setText(selected_expense[0])
        self.expense_amount_entry.setText(selected_expense[1])

    def add_expense(self):
        """
        Adds an expense to the expenses list and updates the UI.

        This method retrieves the expense name and amount from the input fields,
        adds the expense to the expenses list, updates the suggestions, adds the
        expense to the list widget, clears the input fields, and calculates the totals.

        Raises:
            ValueError: If the expense amount is not a valid float.

        Returns:
            None
        """
        try:
            expense_name = self.expense_name_entry.text()
            expense_amount = float(self.expense_amount_entry.text())
            self.expenses.append((expense_name, expense_amount))
            
            # This is for adding Sugestions to the Auto Complete Method
            self.all_expanses.add(expense_name)
            self.update_suggestions()

            # Add to list widget
            self.expense_list.addItem(f"{expense_name}: {expense_amount:.2f}")

            # Clear input fields
            self.expense_name_entry.clear()
            self.expense_amount_entry.clear()

            # Update the totals
            self.calculate_totals()
        except ValueError:
            QMessageBox.critical(self, 'خطأ', 'يرجى إدخال مبلغ صالح.')
    
    def edit_expense(self):
        """
        Edit the selected expense in the expense list.

        This method retrieves the selected expense from the expense list and allows the user to edit its name and amount.
        The updated expense is then saved back to the expenses list and the expense list item is updated accordingly.
        The method also updates the suggestions, calculates the totals, and handles any potential errors.

        Raises:
            ValueError: If an invalid amount is entered.

        """
        try:
            current_item = self.expense_list.currentItem()
            if current_item is not None:
                # Getting data of the selected Expense
                selected_expense = current_item.text().split(': ')
                expense_name = self.expense_name_entry.text()
                expense_amount = float(self.expense_amount_entry.text())

                # Finding the Expense in the list to update it inplace
                for i, (name, amount) in enumerate(self.expenses):
                    if name == selected_expense[0] and float(amount) == float(selected_expense[1]):
                        self.expenses[i] = (expense_name, expense_amount)
                        break
                
                # Editting the Expense in the list viewed
                self.expense_list.currentItem().setText(f"{expense_name}: {expense_amount:.2f}")
                self.calculate_totals()
                
                # This is for adding Sugestions to the Auto Complete Method
                self.all_expanses.add(expense_name)
                self.update_suggestions()
                
            else:
                QMessageBox.critical(self, 'خطأ', 'يرجى اختيار مصروف من القائمة.')
        except ValueError:
            QMessageBox.critical(self, 'خطأ', 'يرجى إدخال مبلغ صالح.')

    def delete_expense(self):
        """
        Deletes the selected expense from the expense list.

        This method retrieves the currently selected expense from the expense list,
        and then searches for a matching expense in the `self.expenses` list. If a
        match is found, the expense is removed from the list. The method also updates
        the expense list and recalculates the totals.

        Raises:
            ValueError: If an invalid expense is selected.

        """
        try:
            current_item = self.expense_list.currentItem()
            if current_item is not None:
                # Getting data of the selected Expense
                selected_expense = current_item.text().split(': ')

                # Finding the Expense in the list to remove it inplace
                for i, (name, amount) in enumerate(self.expenses):
                    if name == selected_expense[0] and float(amount) == float(selected_expense[1]):
                        del self.expenses[i]
                        break
                
                # Rmoving the Expense in the list viewed
                self.expense_list.takeItem(self.expense_list.row(current_item))
                self.calculate_totals()
                
            else:
                QMessageBox.critical(self, 'خطأ', 'يرجى اختيار مصروف من القائمة.')
        except ValueError:
            QMessageBox.critical(self, 'خطأ', 'يرجى اختيار مصروف صالح.')

    # Reports Saving Function
    def save_report_as_pdf(self):
        """
        Saves the report as a PDF file.

        This method generates a PDF report based on the selected date and expenses data.
        The report includes information about expenses, income, and totals.
        Margins and Co-ordinates of the shown data was tested for multible data cases and were correctly shown
        The PDF file is saved in a specified directory and can be opened after saving.

        Raises:
            Exception: If there is an error while saving the report.

        Returns:
            None
        """
        
        try:
            # Load Arabic font
            pdfmetrics.registerFont(TTFont('IBM', 'data/IBMPlexSansArabic-Regular.ttf'))
            pdfmetrics.registerFont(TTFont('IBM-Bold', 'data/IBMPlexSansArabic-Bold.ttf'))

            # Create a PDF document
            date = self.date_picker.date()
            locale = QLocale(QLocale.Arabic)
            
            # Save directory making
            save_dir = f'Pdf reports for {date.toString("yyyy")}/{date.toString("MM")} {date.toString("MMMM")} - {locale.monthName(date.month())}'
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            filename = f"تقرير_مالية_المطعم_{date.toString('yyyy-MM-dd')}.pdf"
            save_dir = save_dir + '/' + filename
            c = canvas.Canvas(save_dir, pagesize=A4)
            width, height = letter
            
            # Helper function to handle Arabic text with wrapping
            def draw_arabic_text(c, text, x, y, font="IBM", size=14, align="right", max_width=None):
                """
                Draw Arabic text on a canvas.

                Args:
                    c (Canvas): The canvas object to draw on.
                    text (str): The Arabic text to be drawn.
                    x (int): The x-coordinate of the starting position.
                    y (int): The y-coordinate of the starting position.
                    font (str, optional): The font to be used for the text. Defaults to "IBM".
                    size (int, optional): The font size. Defaults to 14.
                    align (str, optional): The alignment of the text. Can be "left", "center", or "right". Defaults to "right".
                    max_width (int, optional): The maximum width of each line. If specified, the text will be wrapped accordingly. Defaults to None.

                Returns:
                    tuple: A tuple containing the updated x-coordinate, y-coordinate, and the number of lines written.
                """
                
                reshaped_text = arabic_reshaper.reshape(text)
                bidi_text = get_display(reshaped_text)

                # Seperating String into lines in case of max width is specified
                if max_width:
                    words = bidi_text.split()
                    lines = []
                    current_line = ""
                    for word in words:
                        if pdfmetrics.stringWidth(word, font, size) >= max_width:
                            word = word[:6] + "....." + word[-8:]
                        if pdfmetrics.stringWidth(current_line + " " + word, font, size) <= max_width:
                            current_line += " " + word
                        else:
                            lines.append(current_line.strip())
                            current_line = word
                    
                    if current_line:
                        lines.append(current_line.strip())
                else:
                    lines = [bidi_text]
                # Because of arabic show properties differ from english
                lines.reverse()
                lines_written = len(lines)
                for line in lines:
                    text_width = pdfmetrics.stringWidth(line, font, size)
                    c.setFont(font, size)
                    
                    if align == "left":
                        c.drawString(x, y, line)
                    elif align == "center":
                        c.drawString(x - text_width / 2, y, line)
                    elif align == "right":
                        c.drawString(x - text_width, y, line)
                    
                    y -= 20  # Move to the next line
                
                #to get Current Coordinates    
                return x,y,lines_written

            # Title
            draw_arabic_text(c, "تقرير المالية للمطعم", width / 2, height - 20, "IBM-Bold", 20, "center")

            # Date
            selected_date = self.date_picker.date()
            locale = QLocale(QLocale.Arabic)
            weekday_name = locale.dayName(selected_date.dayOfWeek())
            draw_arabic_text(c, f"{selected_date.toString('yyyy-MM-dd')} {weekday_name}", width / 2, height - 45, "IBM", 16, "center")

            # Line Seperator
            draw_arabic_text(c, '---' * 30, width / 2, height - 60, "IBM-Bold", 12, "center")

            # Expenses
            draw_arabic_text(c, "المصروفات:", width - 60, height - 80, "IBM-Bold", 16)
            y = height - 110
            x = width - 70

            if self.expenses:
                max_expense_with_amount_width = (width-160)/2
                max_expanse_amount_width = pdfmetrics.stringWidth("99999.99", "IBM", 14)
                max_expense_width = max_expense_with_amount_width - max_expanse_amount_width
                i_expense = 0
                full_line_flag = False
        
                for expense in self.expenses:      
                    if i_expense <= 20:
                        _,y,lines_written = draw_arabic_text(c, expense[0], x, y, max_width=max_expense_width)
                        i_expense += lines_written
                    else:
                        i_expense = 1
                        full_line_flag = True
                        y = height - 110
                        x = width/2 - 10
                        _,y,lines_written = draw_arabic_text(c, expense[0], x, y, max_width=max_expense_width)
                
                    # Print the expense amount at the correct height
                    draw_arabic_text(c, f"{expense[1]}", x - max_expense_width, y + 20)

                # Expense Seperator
                c.line(width/2 , height - 100, width/2, 262+20 if full_line_flag else y+20)
            else:
                draw_arabic_text(c, 'لا توجد مصروفات', x, y)

            # Total Expenses
            y = 262
            draw_arabic_text(c, "إجمالي المصروفات :", width - 60, y - 10)
            line_width = pdfmetrics.stringWidth("إجمالي المصروفات :", "IBM", 14)
            
            c.setFillColor(red)
            draw_arabic_text(c, self.total_expenses_result.text(), width - 40 - line_width, y - 10, "IBM-Bold", 14)
            c.setFillColor(black)
            
            # Line Seperator
            draw_arabic_text(c, '---' * 30, width / 2, y - 30, "IBM-Bold", 12, "center")

            # Income and Totals
            draw_arabic_text(c, "الدخل والإجماليات:", width / 2, y - 60, "IBM-Bold", 16, "center")
            y -= 10
            x = int(width - 120)
            draw_arabic_text(c, "دخل نقدي : ", width - 60, y - 80)
            draw_arabic_text(c, self.cash_entry.text(), width - 60, y - 100, "IBM-Bold", 14)
            draw_arabic_text(c, "دخل الشبكة : ", width - 60, y - 120)
            draw_arabic_text(c, self.credit_entry.text(), width - 60, y - 140, "IBM-Bold", 14)
            draw_arabic_text(c, "إجمالي المبيعات : ", width - 60, y - 160)
            draw_arabic_text(c, self.total_sellings_result.text(), width - 60, y - 180, "IBM-Bold", 14)
            draw_arabic_text(c, "سحب الشبكة : ", width - 60, y - 200)
            
            c.setFillColor(red)
            draw_arabic_text(c, self.credit_withdraw_entry.text(), width - 60, y - 220, "IBM-Bold", 14)
            c.setFillColor(black)

            credit = float(self.total_credit_result.text())
            cash = float(self.total_cash_result.text())

            draw_arabic_text(c, "إجمالي الشبكة : ", x / 3, y - 80, "IBM-Bold", 16)
            draw_arabic_text(c, str(credit), x / 3, y - 105, "IBM-Bold", 14)
            draw_arabic_text(c, "إجمالي النقد : ", x / 3, y - 125, "IBM-Bold", 16)
            draw_arabic_text(c, str(cash), x / 3, y - 150, "IBM-Bold", 14)
            draw_arabic_text(c, "الإجمالي : ", x / 3, y - 170, "IBM-Bold", 16)
            draw_arabic_text(c, str(credit + cash), x / 3, y - 195, "IBM-Bold", 14)

            # Save the PDF
            c.save()
            QMessageBox.information(self, 'نجاح', f'تم حفظ التقرير باسم {filename}')
            
            # Open the PDF file
            subprocess.Popen([save_dir], shell=True)

        except Exception as e:
            QMessageBox.critical(self, 'خطأ', f'فشل في حفظ التقرير: {e}')

    # App closing Event
    def closeEvent(self, event):
        """
        This method is called when the window is being closed.

        It saves the suggestions and accepts the close event.

        Args:
            event (QCloseEvent): The close event object.

        Returns:
            None
        """
        # This is for saving Sugestions for the Auto Complete Method 
        self.save_suggestions()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RestaurantFinanceApp()
    window.show()
    sys.exit(app.exec_())
    
    """
    - Hey there, This code is a simple finance manager for a fist restaurant,
      it allows the user to enter the daily income and expenses and save them in an excel file,
      the user can also generate a PDF report for the daily finance.
      
    - All normal cases are handled correctly and tested
    
    - The code is not well organized tbh but it works fine. xD
    
    - I tried to document as much as I can ( This is my first app documentaion ever :D)
    
    - I hope you find this app helpful it might not be helpful for using 
      --(as its made for a particular needing in a fist restaurant xD )--
      but you can find alot of helpful things in this app and u can alter however you want to match your needings
    
    and these comments were only to get to 1269 lines of code :3   
    Hope you like it and have a nice day. <3
    SNOWY 
    """