import sys
from os import *
from PySide2.QtGui import *
from PySide2.QtSql import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
import pandas as pd
import CustomWidgets


class Scheduler(QMainWindow):
    def __init__(self):
        super(Scheduler, self).__init__()

        self.setWindowTitle("Scheduler 2.0")

        _path = 'OldResources/Resources.db'
        self.db = QSqlDatabase.addDatabase('QSQLITE')

        # Check for database file and connection
        if self.databaseExists(_path):
            self.db.setDatabaseName(_path)
            if self.db.open():
                self.showMaximized()
                self.messageBox("Information", "Connected to database.")
            else:
                self.messageBox("Warning", "Couldn't connect to the database!")
                sys.exit()
        else:
            self.messageBox("Warning", "Database does not exist!")
            sys.exit()

        self.menu = QMenuBar()
        self.initMenu()

        self.calendar = CustomWidgets.QCustomCalendar(self.db)  # Calendar Widget; Central Widget
        self.setCentralWidget(self.calendar)

        self.tableModel = QSqlRelationalTableModel(db=self.db)

        self.bottomDock = QDockWidget()
        self.tableView = CustomWidgets.QCustomTableView()
        self.table_edit_delegate = CustomWidgets.TableEditDelegates(self.tableView)
        self.tableView.setModel(self.tableModel)
        self.tableView.setItemDelegate(self.table_edit_delegate)
        self.configureTable()
        self.setInitialModel()

        self.pairTableWithDock()

        self.tableView.keyPressed.connect(self.tableKeyed)
        self.tableView.commit_data.connect(self.tableChanged)
        self.calendar.selectionChanged.connect(self.dateChanged)

        self.setMenuBar(self.menu)
        self.showMaximized()

    def configureTable(self):
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.setEditTriggers(QAbstractItemView.DoubleClicked)

    def configureTableModel(self, date):
        self.tableModel.setTable("Deliveries")
        self.tableModel.setFilter(f"delivery_date like '{date}'")

        self.tableModel.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.tableModel.setRelation(self.tableModel.fieldIndex("vcc"), QSqlRelation("Vcc", "id", "vcc"))
        self.tableModel.setRelation(self.tableModel.fieldIndex("county"), QSqlRelation("Counties", "id", "county"))
        self.tableModel.setRelation(self.tableModel.fieldIndex("driver"), QSqlRelation("Aes_Employees", "id", "name"))
        self.tableModel.setRelation(self.tableModel.fieldIndex("printer"), QSqlRelation("Printers", "id", "printer"))
        self.tableModel.setRelation(self.tableModel.fieldIndex("vehicle"), QSqlRelation("Vehicles", "id", "vehicle"))
        self.tableModel.setRelation(self.tableModel.fieldIndex("site"), QSqlRelation("Sites", "id", "site"))

        self.tableModel.select()

    def pairTableWithDock(self):
        event_button = QPushButton()
        event_button.setFixedWidth(30)
        event_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        button_title_add = QLabel("Add")
        button_title_add.setContentsMargins(0, 0, 0, 0)
        button_title_add.setAlignment(Qt.AlignHCenter)
        button_title_event = QLabel("Event")
        button_title_event.setContentsMargins(0, 0, 0, 0)
        button_title_event.setAlignment(Qt.AlignHCenter)
        button_title_add.setStyleSheet("color: red;"
                                       "font-weight: bold;")
        button_title_event.setStyleSheet("color: red;"
                                         "font-weight: bold;")
        button_title_add.setFixedWidth(30)
        button_title_event.setFixedWidth(30)

        button_layout = QVBoxLayout()
        button_layout.addWidget(button_title_add)
        button_layout.addWidget(button_title_event)
        button_layout.addWidget(event_button)
        button_layout.addSpacing(1000)

        table_layout = QHBoxLayout()
        table_layout.addLayout(button_layout)
        table_layout.addWidget(self.tableView)

        dock_widget = QWidget()
        dock_widget.setLayout(table_layout)

        self.bottomDock.setWidget(dock_widget)
        self.bottomDock.setWindowTitle(QDate.currentDate().toString("dddd, MMMM d, yyyy"))
        self.bottomDock.setMinimumHeight(50)
        self.bottomDock.setMaximumHeight(150)
        self.bottomDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottomDock)

        event_button.clicked.connect(self.addDeliveryDialog)

    def setInitialModel(self):
        date = QDate.currentDate().toString("M/d/yyyy")
        self.configureTableModel(date)

    def dateChanged(self):
        # Method to query data from the selected date
        # Date like date("M/d/yyyy")
        title_date = self.calendar.selectedDate().toString("dddd, MMMM d, yyyy")
        date = self.calendar.selectedDate().toString("M/d/yyyy")

        # set bottom dock title to the selected date
        self.bottomDock.setWindowTitle(title_date)

        self.configureTableModel(date)

    def initMenu(self):
        # File Menu
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.triggered.connect(lambda: self.close())
        file = self.menu.addMenu("File")
        file.addAction(exitAction)

        sitesAction = QAction(QIcon(), "&Sites", self)
        sitesAction.triggered.connect(lambda: SitesDialog())

        countyAction = QAction(QIcon(), "&Counties", self)
        countyAction.triggered.connect(lambda: CountyDialog())

        vehicleAction = QAction(QIcon(), "&Vehicles", self)
        vehicleAction.triggered.connect(lambda: VehicleDialog())

        printerAction = QAction(QIcon(), "&Printers", self)
        printerAction.triggered.connect(lambda: PrinterDialog())

        employeeAction = QAction(QIcon(), "&Employees", self)
        employeeAction.triggered.connect(lambda: EmployeesDialog())

        exportAction = QAction(QIcon(), "&Export", self)
        exportAction.triggered.connect(lambda: self.export())

        clearDeliveriesAction = QAction(QIcon(), "&Clear Deliveries", self)
        clearDeliveriesAction.triggered.connect(lambda: self.clearDeliveries())

        edit = self.menu.addMenu("Edit")
        edit.addAction(clearDeliveriesAction)

        options = self.menu.addMenu("Options")
        options.addAction(sitesAction)
        options.addAction(countyAction)
        options.addAction(vehicleAction)
        options.addAction(printerAction)
        options.addAction(employeeAction)

        file.addAction(exportAction)

    def addDeliveryDialog(self):
        delivery_variables = DeliveryDialog(self.calendar.selectedDate()).closeDialog()

        try:
            record = self.tableModel.record()
            record.setGenerated('id', True)

            record.setValue('icon', delivery_variables['icon'])
            record.setValue('color', delivery_variables['color'])
            record.setValue('vcc', delivery_variables['vcc'])
            record.setValue('county', delivery_variables['county'])
            record.setValue('site', delivery_variables['site'])
            record.setValue('name', delivery_variables['driver'])
            record.setValue('printer', delivery_variables['printer'])
            record.setValue('quantity', delivery_variables['quantity'])
            record.setValue('delivery_date', delivery_variables['delivery_date'])
            record.setValue('vehicle', delivery_variables['vehicle'])
            record.setValue('notes', delivery_variables['notes'])

            self.tableModel.insertRowIntoTable(record)
            self.tableModel.select()

            # repaint calendar to show events
            self.calendar.repaint()
            self.calendar.setFocus()
        except TypeError:
            pass

    def tableKeyed(self):
        row = self.tableView.selectionModel().selectedRows()
        for index in sorted(row):
            self.tableModel.removeRow(index.row())

        self.tableModel.select()
        # repaint calendar to remove events; set focus or else repaint event doesn't appear to trigger
        self.calendar.repaint()
        self.calendar.setFocus()

    def tableChanged(self):
        self.tableModel.select()
        self.calendar.repaint()
        self.calendar.setFocus()

    def closeEvent(self, event):
        # If window closes, close the database connection
        self.db.close()
        super(Scheduler, self).closeEvent(event)

    def messageBox(self, title, message):
        box = QMessageBox()
        box.setText(message)
        box.setWindowTitle(title)
        box.setStandardButtons(QMessageBox.Ok)
        box.exec_()

    def databaseExists(self, _path):
        if path.exists(_path):
            return True
        return False

    def clearDeliveries(self):
        delete_deliveries = QSqlQuery(db=self.db)
        delete_deliveries.exec_("delete from Deliveries;")
        self.calendar.repaint()
        self.tableModel.select()

    def export(self):
        file = QFileDialog.getSaveFileName(self, "Save File", "C:\\", "Excel File (*.xlsx)")

        if "" or None in file:
            return

        filepath = file[0]
        file_ext = file[1]

        sql_table = QSqlQuery(db=self.db)
        # TODO: FINISH THIS SQL STATEMENT
        sql_table.exec_(f"""select B.vcc, C.county, D.site, name, printer, quantity, delivery_date, vehicle, notes 
                        from Deliveries A
                        Join A.vcc on B.id
                        Join B
                        on """)

        while sql_table.next():
            # turn fkeys to text
            vcc = sql_table.value("vcc")
            county = sql_table.value("county")  # fkey
            site = sql_table.value("site")  # fkey
            name = sql_table.value("name")  # fkey
            printer = sql_table.value("printer")  # fkey
            quantity = sql_table.value("quantity")
            delivery_date = sql_table.value("delivery_date")
            vehicle = sql_table.value("vehicle")
            notes = sql_table.value("notes")


class DeliveryDialog(QDialog):
    def __init__(self, selected_date):
        super(DeliveryDialog, self).__init__()
        self.selected_date = selected_date
        self.selected_date_text = QDate.toString(selected_date, "M/d/yyyy")

        self.vehicle_icon = None
        self.color = None
        self.vcc = None
        self.county = None
        self.site = None
        self.driver = None
        self.printer = None
        self.quantity = None
        self.date = None
        self.vehicle = None
        self.notes = None

        self.setWindowTitle('Add A Delivery Event')
        self.setWindowFlags(Qt.WindowCloseButtonHint)

        # Labels
        color_label = QLabel("Color")
        vehicle_label = QLabel("Vehicle")
        icon_label = QLabel("Icon")
        date_label = QLabel("Date")
        vcc_label = QLabel("Vcc")
        driver_label = QLabel("Driver")
        printer_label = QLabel("Printer")
        quantity_label = QLabel("Quantity")
        county_label = QLabel("County")
        site_label = QLabel("Site")
        notes_label = QLabel("Notes")

        # Color Picker (Button to a Color Dialog)
        color_pick = QPushButton("Color")

        # Vehicle Picker
        vehicle = QComboBox()
        vehicle_model = QSqlTableModel()
        taken_vehicles = []
        taken_vehicles_query = QSqlQuery(
            f"SELECT vehicle FROM Deliveries WHERE delivery_date = '{self.selected_date_text}'")
        while taken_vehicles_query.next():
            taken_vehicles.append(taken_vehicles_query.value(0))

        taken_vehicles_text = str(taken_vehicles).lstrip('[').rstrip(']')  # Remove brackets so the Filter will work
        vehicle_model.setTable("Vehicles")
        vehicle_model.setFilter(f"id not in ({taken_vehicles_text})")
        vehicle_model.setSort(vehicle_model.fieldIndex('vehicle'), Qt.AscendingOrder)
        vehicle_model.select()

        vehicle.setModel(vehicle_model)
        vehicle.setModelColumn(vehicle_model.fieldIndex('vehicle'))

        # Icon Picker
        icon = QPushButton("Icon")

        # Date Editor
        date_edit = CustomWidgets.QCustomDateEdit()
        date_edit.setDisplayFormat('M/d/yyyy')
        date_edit.setDate(self.selected_date)

        # Driver Picker
        driver = QComboBox()
        driver_model = QSqlTableModel()
        driver_model.setTable('Aes_Employees')
        driver_model.setSort(driver_model.fieldIndex('name'), Qt.AscendingOrder)
        driver_model.select()

        driver.setModel(driver_model)
        driver.setModelColumn(driver_model.fieldIndex('name'))

        # Vcc ComboBox
        vcc = QComboBox()
        vcc_model = QSqlTableModel()
        vcc_model.setTable('Vcc')
        vcc_model.setSort(vcc_model.fieldIndex('vcc'), Qt.AscendingOrder)
        vcc_model.select()

        vcc.setModel(vcc_model)
        vcc.setModelColumn(vcc_model.fieldIndex('vcc'))

        # County ComboBox
        county = QComboBox()
        county_model = QSqlTableModel()
        county_model.setTable('Counties')
        county_model.setSort(county_model.fieldIndex('county'), Qt.AscendingOrder)
        county_model.select()

        county.setModel(county_model)
        county.setModelColumn(county_model.fieldIndex('county'))

        # Site ComboBox
        site = QComboBox()
        site_model = QSqlTableModel()
        site_model.setTable('Sites')
        site_model.setFilter(f"county like '{county.currentText()}'")
        site_model.select()

        site.setModel(site_model)
        site.setModelColumn(site_model.fieldIndex('site'))

        # Printer ComboBox
        printer = QComboBox()
        printer_model = QSqlTableModel()
        printer_model.setTable('Printers')
        printer_model.setSort(printer_model.fieldIndex('printer'), Qt.AscendingOrder)
        printer_model.select()

        printer.setModel(printer_model)
        printer.setModelColumn(printer_model.fieldIndex('printer'))

        # Quantity SpinBox
        printer_quantity = QSpinBox()
        printer_quantity_model = QSqlQuery()
        printer_quantity_model.exec_(
            f"SELECT quantity FROM Deliveries WHERE delivery_date = '{self.selected_date_text}'")
        p_quantity = printer_quantity_model.next()
        if p_quantity:
            printer_quantity.setValue(p_quantity)
        else:
            printer_quantity.setValue(0)

        # Notes Text Box
        notes = QLineEdit()

        # Add Delivery Button
        add_delivery = QPushButton("Add Delivery")

        # Dialog Layout
        main_layout = QVBoxLayout()

        delivery_layout = QGridLayout()
        delivery_layout.addWidget(date_label, 0, 1)
        delivery_layout.addWidget(date_edit, 1, 1)

        delivery_layout.addWidget(icon_label, 2, 0)
        delivery_layout.addWidget(color_label, 2, 1)
        delivery_layout.addWidget(vehicle_label, 2, 2)

        delivery_layout.addWidget(icon, 3, 0)
        delivery_layout.addWidget(color_pick, 3, 1)
        delivery_layout.addWidget(vehicle, 3, 2)

        delivery_layout.addWidget(driver_label, 4, 0)
        delivery_layout.addWidget(printer_label, 4, 1)
        delivery_layout.addWidget(quantity_label, 4, 2)

        delivery_layout.addWidget(driver, 5, 0)
        delivery_layout.addWidget(printer, 5, 1)
        delivery_layout.addWidget(printer_quantity, 5, 2)

        delivery_layout.addWidget(vcc_label, 6, 0)
        delivery_layout.addWidget(county_label, 6, 1, 1, 2)

        delivery_layout.addWidget(vcc, 7, 0)
        delivery_layout.addWidget(county, 7, 1, 1, 2)

        delivery_layout.addWidget(site_label, 8, 0, 1, 3)
        delivery_layout.addWidget(site, 9, 0, 1, 3)

        delivery_layout.addWidget(notes_label, 10, 0, 1, 3)
        delivery_layout.addWidget(notes, 11, 0, 1, 3)

        delivery_layout.addWidget(add_delivery, 12, 0, 1, 3)

        main_layout.addLayout(delivery_layout)

        # Get Initial Widget Values
        self.date = date_edit.text()
        self.driver = driver.currentText()
        self.vcc = vcc.currentText()
        self.county = county.currentText()
        self.site = site.currentText()
        self.printer = printer.currentText()
        self.quantity = printer_quantity.value()
        self.vehicle = vehicle.currentText()
        self.notes = notes.text()

        # Widget Signals
        county.currentIndexChanged.connect(lambda: site_model.setFilter(f"county like '{county.currentText()}'"))
        vcc.currentIndexChanged.connect(lambda: self.setVcc(vcc.currentText()))
        color_pick.clicked.connect(lambda: self.setColor(color_pick))
        vehicle.currentIndexChanged.connect(lambda: self.setVehicle(vehicle.currentText()))
        icon.clicked.connect(lambda: self.vehicleSelect(icon))
        date_edit.dateChanged.connect(lambda: self.setDate(date_edit.text()))
        driver.currentIndexChanged.connect(lambda: self.setDriver(driver.currentText()))
        county.currentIndexChanged.connect(lambda: self.setCounty(county.currentText()))
        site.currentIndexChanged.connect(lambda: self.setSite(site.currentText()))
        printer.currentIndexChanged.connect(lambda: self.setPrinter(printer.currentText()))
        printer_quantity.valueChanged.connect(lambda: self.setPrinterQuantity(printer_quantity.value()))
        notes.textChanged.connect(lambda: self.setNotes(notes.text()))

        add_delivery.clicked.connect(self.closeDialog)

        self.setLayout(main_layout)
        self.exec_()

    def setColor(self, button):
        self.color = QColorDialog.getColor().name()
        button.setStyleSheet(f"background-color: {self.color}")

    def setVcc(self, vcc):
        self.vcc = vcc

    def setVehicle(self, vehicle):
        self.vehicle = vehicle

    def vehicleSelect(self, button):
        vehicle_icon = VehicleIconDialog().getIcon()
        self.vehicle_icon = vehicle_icon
        button.setIcon(QIcon(vehicle_icon))

    def setDate(self, date):
        self.date = date

    def setDriver(self, driver):
        self.driver = driver

    def setCounty(self, county):
        self.county = county

    def setSite(self, site):
        self.site = site

    def setPrinter(self, printer):
        self.printer = printer

    def setPrinterQuantity(self, quantity):
        self.quantity = quantity

    def setNotes(self, notes):
        self.notes = notes

    def values_to_id(self, dialog_variables):
        # Return foreign keys
        variables_to_ids = {'icon': None, 'color': None, 'vcc': None, 'county': None, 'site': None, 'driver': None,
                            'printer': None, 'quantity': None, 'delivery_date': None, 'vehicle': None, 'notes': None}

        # Icon: Can just be passed through
        variables_to_ids['icon'] = dialog_variables['icon']

        # Color: Can just be passed through
        variables_to_ids['color'] = dialog_variables['color']

        # Vcc: select id, vcc
        vcc = dialog_variables['vcc']
        vcc_model = QSqlQueryModel()
        vcc_model.setQuery(f"SELECT id, vcc FROM Vcc WHERE vcc = '{vcc}'")
        vcc_id = int(vcc_model.data(vcc_model.index(0, 0)))
        variables_to_ids['vcc'] = vcc_id

        # County
        county = dialog_variables['county']
        county_model = QSqlQueryModel()
        county_model.setQuery(f"SELECT id, county FROM Counties WHERE county = '{county}'")
        county_id = int(county_model.data(county_model.index(0, 0)))
        variables_to_ids['county'] = county_id

        # Site
        site = dialog_variables['site']
        site_model = QSqlQueryModel()
        site_model.setQuery(f"SELECT id, site FROM Sites WHERE site = '{site}'")
        site_id = int(site_model.data(site_model.index(0, 0)))
        variables_to_ids['site'] = site_id

        # Driver
        driver = dialog_variables['driver']
        driver_model = QSqlQueryModel()
        driver_model.setQuery(f"SELECT id, name FROM Aes_Employees WHERE name = '{driver}'")
        driver_id = int(driver_model.data(driver_model.index(0, 0)))
        variables_to_ids['driver'] = driver_id

        # Printer
        printer = dialog_variables['printer']
        printer_model = QSqlQueryModel()
        printer_model.setQuery(f"SELECT id, printer FROM Printers WHERE printer = '{printer}'")
        printer_id = int(printer_model.data(printer_model.index(0, 0)))
        variables_to_ids['printer'] = printer_id

        # Quantity: Can just be passed through
        variables_to_ids['quantity'] = dialog_variables['quantity']

        # Delivery_date: Can just be passed through
        variables_to_ids['delivery_date'] = dialog_variables['delivery_date']

        # Vehicle
        vehicle = dialog_variables['vehicle']
        vehicle_model = QSqlQueryModel()
        vehicle_model.setQuery(f"SELECT id, vehicle FROM Vehicles WHERE vehicle = '{vehicle}'")
        vehicle_id = int(vehicle_model.data(vehicle_model.index(0, 0)))
        variables_to_ids['vehicle'] = vehicle_id

        # Notes: Can just be passed through
        variables_to_ids['notes'] = dialog_variables['notes']

        return variables_to_ids

    def closeDialog(self):
        dialog_variables = {'icon': self.vehicle_icon,
                            'color': self.color,
                            'vcc': self.vcc,
                            'county': self.county,
                            'site': self.site,
                            'driver': self.driver,
                            'printer': self.printer,
                            'quantity': self.quantity,
                            'delivery_date': self.date,
                            'vehicle': self.vehicle,
                            'notes': self.notes}

        dialog_variables_with_ids = self.values_to_id(dialog_variables)

        if None not in dialog_variables_with_ids.values():
            self.close()
            return dialog_variables_with_ids
        else:
            message = QMessageBox()
            message.setWindowTitle("Error")
            message.setText("One of the variables was not set!")
            message.setStandardButtons(QMessageBox.Ok)
            message.exec_()
            return None

    def closeEvent(self, arg__1: QCloseEvent):
        self.close()


class VehicleIconDialog(QDialog):
    def __init__(self):
        super(VehicleIconDialog, self).__init__()

        self.icon = None

        self.setWindowTitle("Select Vehicle Icon")
        self.setWindowFlags(Qt.WindowCloseButtonHint)

        icons = self.makeIcons()
        button_layout = self.makeButtons(icons)

        self.setLayout(button_layout)
        self.exec_()

    def makeButtons(self, icon_dictionary):
        layout = QGridLayout()
        buttons = {}
        for key in icon_dictionary:
            buttons[key] = QPushButton()
            buttons[key].setIcon(icon_dictionary[key][0])
            buttons[key].clicked.connect(lambda _=None, c=key: self.setIcon(icon_dictionary[c][-1]))
            layout.addWidget(buttons[key], 0, key)

        return layout

    def makeIcons(self):
        icon_dictionary = {}  # id: (QIcon, icon_file_path)
        icon_folder = "icons"
        icon_dir = listdir(icon_folder)
        for position, files in enumerate(icon_dir):
            if ".png" in files:
                icon_file_paths = path.join(icon_folder, files)
                icon = QIcon(icon_file_paths)
                icon_dictionary[position] = (icon, icon_file_paths)

        return icon_dictionary

    def setIcon(self, icon):
        self.icon = icon
        self.close()

    def getIcon(self):
        # Returns file path to icon
        if self.icon:
            return self.icon


class SitesDialog(QDialog):
    def __init__(self, parent=None):
        super(SitesDialog, self).__init__(parent)

        self.setWindowTitle("Add New Sites")

        self.sites_table_model = QSqlTableModel()
        self.sites_table_model.setTable("Sites")
        self.sites_table_model.select()

        self.county_model = QSqlQueryModel()
        self.county_model.setQuery("SELECT county FROM Counties")  # TODO: ADD ALPHA SORT

        self.filter_label = QLabel("Filter")
        self.filter_label.setStyleSheet("text-decoration: Bold")

        self.warning_label = QLabel("""
        WARNING: This table has direct access to the database that this application is built upon. If you do not 
        know what you are doing, please find Paul to help you edit your site data. 

        Under no circumstance should you edit the 'id' or 'county' fields in this table!\n
        Duplicate data are an unfortunate consequence of Paul's bad Master Resource Converter\n
        Inputs are not sanitized. Do not try SQL commands...TIM! (Don't @ me)\n""")
        self.warning_label.setStyleSheet("color: red")

        self.add_site_label = QLabel("New Site Name")
        self.add_site = QLineEdit()

        self.add_address_label = QLabel("New Site Address")
        self.add_address = QLineEdit()

        self.add_site_button = QPushButton("Add Site")

        self.sites_table = CustomWidgets.QCustomTableView()  # CustomWidgets
        self.sites_table.setModel(self.sites_table_model)

        self.filter_combo = QComboBox()
        self.filter_combo.setModel(self.county_model)

        # Initial Filter
        self.addFilter(self.filter_combo.currentText())

        # Signals
        self.filter_combo.currentIndexChanged.connect(lambda: self.addFilter(self.filter_combo.currentText()))
        self.add_site_button.clicked.connect(lambda: self.addSite())
        self.sites_table.keyPressed.connect(lambda: self.tableKeyed())

        warning_layout = QVBoxLayout()
        warning_layout.addWidget(self.warning_label)

        filter_layout = QGridLayout()
        filter_layout.addWidget(self.filter_label, 0, 0)
        filter_layout.addWidget(self.add_site_label, 0, 1)
        filter_layout.addWidget(self.add_address_label, 0, 2)
        filter_layout.addWidget(self.filter_combo, 1, 0)
        filter_layout.addWidget(self.add_site, 1, 1)
        filter_layout.addWidget(self.add_address, 1, 2)
        filter_layout.addWidget(self.add_site_button, 1, 3)
        filter_layout.setAlignment(Qt.AlignLeft)

        dialog_layout = QVBoxLayout()
        dialog_layout.addLayout(warning_layout)
        dialog_layout.addLayout(filter_layout)
        dialog_layout.addWidget(self.sites_table)
        self.setLayout(dialog_layout)

        self.sites_table.horizontalHeader().setStretchLastSection(True)
        self.setMinimumWidth(self.sites_table.width())
        self.setMinimumHeight(self.sites_table.height())

        self.exec_()

    def addFilter(self, fltr):
        self.sites_table_model.setFilter(f"county like '{fltr}'")
        self.sites_table_model.select()

    def addSite(self):
        site = self.add_site.text()
        address = self.add_address.text()
        county = self.filter_combo.currentText()

        if site and address:
            record = self.sites_table_model.record()
            record.setGenerated("id", True)
            record.setValue("county", county)
            record.setValue("site", site)
            record.setValue("address", address)

            self.sites_table_model.insertRowIntoTable(record)
            self.sites_table_model.select()
            self.sites_table.scrollToBottom()
        else:
            message = QMessageBox()
            message.setWindowTitle("Error")
            message.setText("One of the inputs was not set!")
            message.setStandardButtons(QMessageBox.Ok)
            message.exec_()

    def tableKeyed(self):
        row = self.sites_table.selectionModel().selectedRows()
        for index in sorted(row):
            self.sites_table_model.removeRow(index.row())
            self.sites_table_model.select()


class CountyDialog(QDialog):
    def __init__(self, parent=None):
        super(CountyDialog, self).__init__(parent)

        self.setWindowTitle("Add New County")

        self.county_table_model = QSqlTableModel()
        self.county_table_model.setTable("Counties")
        self.county_table_model.select()

        self.county_table = CustomWidgets.QCustomTableView()  # CustomWidgets
        self.county_table.setModel(self.county_table_model)

        self.new_county_label = QLabel("Add County")
        self.new_county_entry = QLineEdit()
        self.add_new_county_button = QPushButton("Enter")

        layout = QGridLayout()
        layout.addWidget(self.new_county_label, 0, 0)
        layout.addWidget(self.new_county_entry, 1, 0)
        layout.addWidget(self.add_new_county_button, 1, 2)

        layout.addWidget(self.county_table, 2, 0, 1, 3)

        self.add_new_county_button.clicked.connect(lambda: self.addCounty())
        self.county_table.keyPressed.connect(lambda: self.tableKeyed())

        self.setLayout(layout)

        self.exec_()

    def addCounty(self):
        county = self.new_county_entry.text()
        if county:
            record = self.county_table_model.record()
            record.setGenerated("id", True)
            record.setValue("county", county)

            self.county_table_model.insertRowIntoTable(record)
            self.county_table_model.select()
            self.county_table.scrollToBottom()
        else:
            message = QMessageBox()
            message.setWindowTitle("Error")
            message.setText("One of the inputs was not set!")
            message.setStandardButtons(QMessageBox.Ok)
            message.exec_()

    def tableKeyed(self):
        row = self.county_table.selectionModel().selectedRows()
        for index in sorted(row):
            self.county_table_model.removeRow(index.row())
            self.county_table_model.select()


class VehicleDialog(QDialog):
    def __init__(self, parent=None):
        super(VehicleDialog, self).__init__(parent)

        self.setWindowTitle("Add New Vehicle")

        self.vehicle_model = QSqlTableModel()
        self.vehicle_model.setTable("Vehicles")
        self.vehicle_model.select()

        self.vehicle_table = CustomWidgets.QCustomTableView()  # CustomWidgets
        self.vehicle_table.setModel(self.vehicle_model)

        self.new_vehicle_label = QLabel("Add New Vehicle")
        self.new_vehicle_entry = QLineEdit()
        self.add_new_vehicle_button = QPushButton("Enter")

        layout = QGridLayout()
        layout.addWidget(self.new_vehicle_label, 0, 0)
        layout.addWidget(self.new_vehicle_entry, 1, 0)
        layout.addWidget(self.add_new_vehicle_button, 1, 1)

        layout.addWidget(self.vehicle_table, 2, 0, 1, 3)

        self.add_new_vehicle_button.clicked.connect(lambda: self.addVehicle())
        self.vehicle_table.keyPressed.connect(lambda: self.tableKeyed())

        self.setLayout(layout)

        self.exec_()

    def addVehicle(self):
        vehicle = self.new_vehicle_entry.text()
        if vehicle:
            record = self.vehicle_model.record()
            record.setGenerated("id", True)
            record.setValue("vehicle", vehicle)

            self.vehicle_model.insertRowIntoTable(record)
            self.vehicle_model.select()
            self.vehicle_table.scrollToBottom()
        else:
            message = QMessageBox()
            message.setWindowTitle("Error")
            message.setText("One of the inputs was not set!")
            message.setStandardButtons(QMessageBox.Ok)
            message.exec_()

    def tableKeyed(self):
        row = self.vehicle_table.selectionModel().selectedRows()
        for index in sorted(row):
            self.vehicle_model.removeRow(index.row())
            self.vehicle_model.select()


class PrinterDialog(QDialog):
    def __init__(self, parent=None):
        super(PrinterDialog, self).__init__(parent)

        self.setWindowTitle("Add New Printer Type")

        self.printer_model = QSqlTableModel()
        self.printer_model.setTable("Printers")
        self.printer_model.select()

        self.printer_table = CustomWidgets.QCustomTableView()  # CustomWidgets
        self.printer_table.setModel(self.printer_model)

        self.new_printer_label = QLabel("Add New Printer")
        self.new_printer_entry = QLineEdit()
        self.add_new_printer_button = QPushButton("Enter")

        layout = QGridLayout()
        layout.addWidget(self.new_printer_label, 0, 0)
        layout.addWidget(self.new_printer_entry, 1, 0)
        layout.addWidget(self.add_new_printer_button, 1, 1)

        layout.addWidget(self.printer_table, 2, 0, 1, 3)

        self.add_new_printer_button.clicked.connect(lambda: self.addPrinter())
        self.printer_table.keyPressed.connect(lambda: self.tableKeyed())

        self.setLayout(layout)
        self.exec_()

    def addPrinter(self):
        printer = self.new_printer_entry.text()
        if printer:
            record = self.printer_model.record()
            record.setGenerated("id", True)
            record.setValue("printer", printer)

            self.printer_model.insertRowIntoTable(record)
            self.printer_model.select()
            self.printer_table.scrollToBottom()
        else:
            message = QMessageBox()
            message.setWindowTitle("Error")
            message.setText("One of the inputs was not set!")
            message.setStandardButtons(QMessageBox.Ok)
            message.exec_()

    def tableKeyed(self):
        row = self.printer_table.selectionModel().selectedRows()
        for index in sorted(row):
            self.printer_model.removeRow(index.row())
            self.printer_model.select()


class EmployeesDialog(QDialog):
    def __init__(self, parent=None):
        super(EmployeesDialog, self).__init__(parent)

        self.setWindowTitle("Add New Driver/Employee")

        self.employee_model = QSqlTableModel()
        self.employee_model.setTable("Aes_Employees")
        self.employee_model.select()

        self.employee_table = CustomWidgets.QCustomTableView()  # CustomWidgets
        self.employee_table.setModel(self.employee_model)

        self.new_employee_label = QLabel("Add New Driver/Employee")
        self.new_employee_entry = QLineEdit()
        self.add_new_employee_button = QPushButton("Enter")

        layout = QGridLayout()
        layout.addWidget(self.new_employee_label, 0, 0)
        layout.addWidget(self.new_employee_entry, 1, 0)
        layout.addWidget(self.add_new_employee_button, 1, 1)

        layout.addWidget(self.employee_table, 2, 0, 1, 3)

        self.add_new_employee_button.clicked.connect(lambda: self.addEmployee())
        self.employee_table.keyPressed.connect(lambda: self.tableKeyed())

        self.setLayout(layout)
        self.exec_()

    def addEmployee(self):
        employee = self.new_employee_entry.text()
        if employee:
            record = self.employee_model.record()
            record.setGenerated("id", True)
            record.setValue("name", employee)

            self.employee_model.insertRowIntoTable(record)
            self.employee_model.select()
            self.employee_table.scrollToBottom()
        else:
            message = QMessageBox()
            message.setWindowTitle("Error")
            message.setText("One of the inputs was not set!")
            message.setStandardButtons(QMessageBox.Ok)
            message.exec_()

    def tableKeyed(self):
        row = self.employee_table.selectionModel().selectedRows()
        for index in sorted(row):
            self.employee_model.removeRow(index.row())
            self.employee_model.select()


def main():
    app = QApplication(sys.argv)
    ex = Scheduler()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
