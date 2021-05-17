from Final.Main import *

calendar_QSS = """
QToolButton {
icon-size: 30px, 30px;
width: 80px;
height: 30px;
font: 15pt;
}

#qt_calendar_yearbutton {
width: 86px;
font-weight: bold;
}

#qt_calendar_monthbutton {
width: 256px;
font-weight: bold;
}

QToolButton#qt_calendar_nextmonth {
qproperty-icon: url(right-arrow.png);
}

QToolButton#qt_calendar_prevmonth {
qproperty-icon: url(left-arrow.png);
}
"""

radio_Disabled_QSS = """
QRadioButton:disabled {
color:black;
}

QRadioButton::indicator:disabled {
border: 1px solid black;
border-radius: 6px;
width: 10px;
height: 10px;
margin-left: 8px;
color:black;
}

QRadioButton::indicator:checked:disabled {
background-color:red;
}"""


class QCustomCalendar(QCalendarWidget):
    def __init__(self, db, parent=None):
        super(QCustomCalendar, self).__init__(parent)
        self.pen = QPen()
        self.pen.setColor(Qt.black)
        self.setStyleSheet(calendar_QSS)
        self.setGridVisible(True)
        self.setSelectionMode(QCalendarWidget.SingleSelection)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)  # Turn Off Week Numbers
        self.setHorizontalHeaderFormat(QCalendarWidget.LongDayNames)  # Long Day Names in Horizontal Header e.g., "Monday"

        self.db = db
        # Now returning 2D List with dictionary as first dimension
        # Dates in date_list
        self.date_list = self.dateQuery()

    def paintCell(self, painter, rect, date):
        # TODO: Fix colors and shit
        pen = QPen()
        pen.setColor(Qt.black)
        painter.setPen(pen)
        painter.save()

        for i, elements in enumerate(self.date_list):  # 2D List of dictionaries
            for element in elements:  # Dictionary
                qdate = QDate.fromString(element["delivery_date"], "M/d/yyyy")
                if date == qdate:
                    self.paintEventInDay(painter, rect, elements)

        if date == self.selectedDate():
            # selected date is yellow, unless it is also today; then a lighter blue
            dotted_pen = QPen()
            highlight_color = QColor()
            highlight_color.setNamedColor("yellow")
            highlight_color.setAlpha(98)
            light_hightlight_color = QColor()
            light_hightlight_color.setNamedColor("white")
            light_hightlight_color.setAlpha(63)
            dotted_pen.setColor(Qt.black)
            dotted_pen.setStyle(Qt.DotLine)
            dotted_pen.setWidth(2)
            painter.setPen(dotted_pen)

            painter.drawRect(rect.adjusted(0, 0, 0, 0))
            painter.fillRect(rect.adjusted(0, 0, 0, 0), highlight_color)

            if date == date.currentDate():
                trans_color = QColor(0, 55, 255, 255)
                painter.setPen(trans_color)
                painter.setFont(QFont('Sarif', 12))
                painter.drawText(QRectF(rect.adjusted(5, 5, 0, 0)), Qt.TextSingleLine | Qt.AlignTop | Qt.AlignLeft,
                                 str(date.day()))
            else:
                painter.setPen(Qt.black)
                painter.setFont(QFont('Sarif', 10))
                painter.drawText(QRectF(rect.adjusted(5, 5, 0, 0)), Qt.TextSingleLine | Qt.AlignTop | Qt.AlignLeft,
                                 str(date.day()))

        elif date == date.currentDate():
            # current date to a blue color
            trans_color = QColor(0, 55, 255, 255)

            if self.monthShown() != date.month():
                gray_color = QColor()
                gray_color.setNamedColor("lightgray")
                painter.fillRect(rect.adjusted(0, 0, 0, 0), gray_color)

            painter.setPen(trans_color)
            painter.setFont(QFont('Sarif', 12))
            painter.drawText(QRectF(rect.adjusted(5, 5, 0, 0)), Qt.TextSingleLine | Qt.AlignTop | Qt.AlignLeft,
                             str(date.day()))

        elif self.monthShown() != date.month():
            # grey out cells that are not in current month
            gray_color = QColor()
            gray_color.setNamedColor("lightgray")
            painter.fillRect(rect.adjusted(0, 0, 0, 0), gray_color)

            painter.setPen(Qt.black)
            painter.setFont(QFont('Sarif', 10))
            painter.drawText(QRectF(rect.adjusted(5, 5, 0, 0)), Qt.TextSingleLine | Qt.AlignTop | Qt.AlignLeft,
                             str(date.day()))

        else:
            painter.setPen(Qt.black)
            painter.setFont(QFont('Sarif', 10))
            painter.drawText(QRectF(rect.adjusted(5, 5, 0, 0)), Qt.TextSingleLine | Qt.AlignTop | Qt.AlignLeft,
                             str(date.day()))

        painter.restore()

    def paintEventInDay(self, painter, _rect, events):
        # TODO: Continue writing the function that fits events into a calendar cell
        # For each dictionary in list, get color and icon
        # Create a painter with the color
        # Divide the cell up by number of events, up to a max of 4, with one spillover cell
        rect = _rect.adjusted(1, 1, 0, 0)

        rect_size = rect.size()
        rect_size.setHeight(rect_size.height()-1)
        rect_size.setWidth(rect_size.width())
        spillover_rect = QRectF(rect.topLeft(), QSizeF(rect_size.width()/5, rect_size.height()))

        spillover_top_right = spillover_rect.topRight()  # Starting point for event_space; event_space.topLeft()
        event_space_size = QSizeF(rect_size.width()*(4/5), rect_size.height())
        event_space = QRectF(spillover_top_right, event_space_size)
        event_space_x = event_space.left()
        event_space_y = event_space.top()

        for i, event in enumerate(events):
            if i < 4:
                event_color = event["color"]
                event_icon = event["icon"]

                event_rect_height = event_space.height()/4
                event_rect_width = event_space.width()
                event_space_top_left = QPoint(event_space_x, event_space_y + (i * event_rect_height))
                event_rect = QRectF(QPointF(event_space_top_left),
                                    QSize(event_rect_width, event_rect_height))
                painter.fillRect(event_rect, QColor(event_color))

                # Add Icon, Info
                # Divide event_rect into 3 parts, 1/3 will be for icon, 2/3 will be for info text
                pix_rect_top_left = event_rect.topLeft()
                pix_rect_bottom_right = QPointF((event_rect.left() + (event_rect.right() - event_rect.left()) / 7),
                                                event_rect.bottom())
                pix_rect = QRectF(pix_rect_top_left, pix_rect_bottom_right)
                # TODO: Add padding to left/right to make square; looks alright as it is...

                info_rect_top_left = QPointF(pix_rect.right() + 5, pix_rect.top())
                info_rect_bottom_right = event_rect.bottomRight()
                info_rect = QRectF(info_rect_top_left, info_rect_bottom_right)

                pix = QPixmap(event_icon)
                painter.drawPixmap(pix_rect, pix, pix.rect())

                # TODO: map foreign keys to int values
                driver = str(event["name"])
                county = str(event["county"])
                site = str(event["site"])
                info = driver + "|" + county

                painter.setPen(Qt.black)
                painter.setFont(QFont('Sarif', 10))
                painter.drawText(info_rect, Qt.TextSingleLine | Qt.AlignLeft | Qt.AlignVCenter, info)

            else:
                painter.setPen(Qt.black)
                painter.fillRect(spillover_rect, Qt.red)
                painter.setFont(QFont('Sarif', 18))
                painter.drawText(spillover_rect, Qt.TextSingleLine | Qt.AlignHCenter | Qt.AlignVCenter, "+")

    def repaint(self):
        self.date_list = self.dateQuery()
        super(QCustomCalendar, self).repaint()

    def dateQuery(self):
        # TODO: Change variables to hold entire record
        # dictionary = [{id, icon, color, vcc, county, site, name, delivery_date, vehicle}]
        i, icon, color, vcc, county, site, name, printer, quantity, delivery_date, vehicle, notes = range(12)
        query = QSqlQuery()
        query.exec_("SELECT * from Deliveries;")

        query_dict_list = []
        date_list = []

        while query.next():
            qdate_query = query.value(delivery_date)
            qdate = QDate.fromString(qdate_query, "M/d/yyyy")
            date_list.append(qdate)

            _id = query.value(i)
            _icon = query.value(icon)
            _color = query.value(color)
            _vcc = query.value(vcc)
            _county = query.value(county)
            _site = query.value(site)
            _name = query.value(name)
            _printer = query.value(printer)
            _quantity = query.value(quantity)
            _delivery_date = query.value(delivery_date)
            _vehicle = query.value(vehicle)
            _notes = query.value(notes)

            fkey_name = QSqlQuery()
            fkey_name.exec_(f"SELECT name FROM Aes_Employees WHERE id = {_name}")
            fkey_county = QSqlQuery()
            fkey_county.exec_(f"SELECT county FROM Counties WHERE id = {_county}")
            fkey_site = QSqlQuery()
            fkey_site.exec_(f"SELECT site FROM Sites WHERE id = {_site}")

            # change foreign keys to table values
            f_name = None
            f_county = None
            if fkey_name.first():
                f_name = fkey_name.value(0)
            if fkey_county.first():
                f_county = fkey_county.value(0)

            query_dict = {"id": _id,
                          "icon": _icon,
                          "color": _color,
                          "vcc": _vcc,
                          "county": f_county,
                          "site": _site,
                          "name": f_name,
                          "printer": _printer,
                          "quantity": _quantity,
                          "delivery_date": _delivery_date,
                          "vehicle": _vehicle,
                          "notes": _notes}

            query_dict_list.append(query_dict)

        sorted_list = self.sortAndGroupEvents(query_dict_list)
        return sorted_list
        # return date_list

    def sortAndGroupEvents(self, dict_list):
        date = "delivery_date"
        set_dates = set(map(lambda x: x[date], dict_list))
        sorted_list = [[j for j in dict_list if j[date] == i] for i in set_dates]

        return sorted_list


class QCustomDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super(QCustomDateEdit, self).__init__(parent)
        edit = self.lineEdit()
        edit.setReadOnly(True)
        edit.selectionChanged.connect(lambda edit=edit: edit.end(False))

    def stepBy(self, steps):
        self.setDateTime(self.dateTime().addDays(steps))


class DateEditForDelegate(QDateEdit):
    def __init__(self, parent=None):
        super(DateEditForDelegate, self).__init__(parent)

    def stepBy(self, steps):
        self.setDateTime(self.dateTime().addDays(steps))


class QCustomTableView(QTableView):
    # Reimplimented QTableView with a "delete" and "backspace" signal emission; also emits signal when editor closes
    keyPressed = Signal(int)
    editorClosed = Signal()
    commit_data = Signal()

    def __init__(self, parent=None):
        super(QCustomTableView, self).__init__(parent)
        self.horizontalHeader().setStretchLastSection(True)

    def keyPressEvent(self, event):
        super(QCustomTableView, self).keyPressEvent(event)
        if type(event) == QKeyEvent:
            if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
                self.keyPressed.emit(event.key())

    def commitData(self, editor):
        super(QCustomTableView, self).commitData(editor)
        self.commit_data.emit()


class TableEditDelegates(QSqlRelationalDelegate):
    # Keeps relational combo boxes while implementing new QDateEdit, QColoDialog, and QSpinBox editors for their
    # respective columns
    def __init__(self, parent=None):
        super(TableEditDelegates, self).__init__(parent)
        self.color = None
        self.icon = None

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        if index.column() == 1:  # Icon - Icon Dialog
            self.icon = VehicleIconDialog().getIcon()
            return QLineEdit(parent)
        if index.column() == 2:  # Color - Color Dialog
            self.color = QColorDialog().getColor()
            return QLineEdit(parent)
        if index.column() == 4:  # County - Disable editing and color red if selected
            non_edit_line = QLineEdit(parent)
            non_edit_line.setEnabled(False)
            non_edit_line.setStyleSheet("background: red;")
            return non_edit_line
        if index.column() == 5:  # Site
            site_filter = QComboBox(parent)
            site_filter.setCurrentIndex(site_filter.currentIndex())
            return site_filter
        if index.column() == 8:  # Quantity
            return QSpinBox(parent)
        if index.column() == 9:  # DateEdit
            return DateEditForDelegate(parent)
        return super(TableEditDelegates, self).createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        if isinstance(editor, QDateEdit):
            value = index.model().itemData(index)[0]
            date = QDate.fromString(value, "M/d/yyyy")
            editor.setDate(date)
        elif index.column() == 1:
            if self.icon:
                editor.setText(self.icon)
            else:
                value = index.model().itemData(index)[0]
                editor.setText(value)
        elif index.column() == 2:
            if self.color.isValid():
                editor.setText(f"{self.color.name()}")
        elif index.column() == 5:
            # Get County Name
            row = index.row()
            county_row = 4
            county = index.model().data(index.model().index(row, county_row), Qt.DisplayRole)

            # Make a query to select only sites in county
            site_model = QSqlQueryModel()
            site_model.setQuery(f"SELECT site FROM Sites WHERE county = '{county}'")
            editor.setModel(site_model)
        elif index.column() == 8:
            value = index.model().itemData(index)[0]
            editor.setRange(0, 99)
            editor.setValue(value)
        else:
            super(TableEditDelegates, self).setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
        if isinstance(editor, QDateEdit):
            model_date = editor.date()
            date = model_date.toString("M/d/yyyy")
            model.setData(index, date)
        elif index.column() == 1:
            if self.icon:
                model.setData(index, self.icon)
            else:
                pass
        elif index.column() == 2:
            model_data = editor.text()
            model.setData(index, model_data)
        elif index.column() == 5:
            site_name = editor.currentText()
            site_id = QSqlQuery()
            site_id.exec_(f"SELECT id from Sites WHERE site = '{site_name}'")
            data = None
            if site_id.first():
                data = site_id.value(0)
            model.setData(index, data)
        else:
            super(TableEditDelegates, self).setModelData(editor, model, index)
