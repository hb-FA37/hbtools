"""
Modification of a modification:
Original sources:
 https://groups.google.com/forum/#!topic/python_inside_maya/vO1pvA4YhF0
 http://pastebin.com/mZ04q16h
Modification of Blur's Accordion Widget to include a Maya style.  Also got rid of the need for a pixmap and used QPolygon instead.
"""

from Qt.QtCore import Qt, QRect, QMimeData, QEvent, QPoint, Signal, Property
from Qt.QtGui import QCursor, QColor, QPolygon, QBrush
from Qt.QtGui import QDrag, QPixmap, QPainter, QPalette, QPen
from Qt.QtWidgets import QWidget, QScrollArea, QGroupBox, QApplication, QVBoxLayout


class AccordionItem(QGroupBox):
    """
    Item to be added to an AccordionWidget, only used by the widget itself.
    """
    def __init__(self, accordion, title, widget):
        QGroupBox.__init__(self, accordion)

        # Create the layout
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(0)
        layout.addWidget(widget)

        self._accordianWidget = accordion
        self._rolloutStyle = 2
        self._dragDropMode = 0

        self.setAcceptDrops(True)
        self.setLayout(layout)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showMenu)

        # Create custom properties
        self._widget = widget
        self._collapsed = False
        self._collapsible = True
        self._clicked = False
        self._customData = {}

        # set common properties
        self.setTitle(title)

    def accordionWidget(self):
        """
        \remarks    grabs the parent item for the accordian widget
        \return     <blurdev.gui.widgets.accordianwidget.AccordianWidget>
        """
        return self._accordianWidget

    def customData(self, key, default=None):
        """
        \remarks    return a custom pointer to information stored with this item
        \param      key         <str>
        \param      default     <variant>       default value to return if the key was not found
        \return     <variant>   data
        """
        return self._customData.get(str(key), default)

    def dragEnterEvent(self, event):
        if not self._dragDropMode:
            return

        source = event.source()
        if source != self and source.parent() == self.parent() and isinstance(source, AccordionItem):
            event.acceptProposedAction()

    def dragDropRect(self):
        return QRect(25, 7, 10, 6)

    def dragDropMode(self):
        return self._dragDropMode

    def dragMoveEvent(self, event):
        if not self._dragDropMode:
            return

        source = event.source()
        if source != self and source.parent() == self.parent() and isinstance(source, AccordionItem):
            event.acceptProposedAction()

    def dropEvent(self, event):
        widget = event.source()
        layout = self.parent().layout()
        layout.insertWidget(layout.indexOf(self), widget)
        self._accordianWidget.emitItemsReordered()

    def expandCollapseRect(self):
        return QRect(0, 0, self.width(), 20)

    def enterEvent(self, event):
        self.accordionWidget().leaveEvent(event)
        event.accept()

    def leaveEvent(self, event):
        self.accordionWidget().enterEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        if self._clicked and self.expandCollapseRect().contains(event.pos()):
            self.toggleCollapsed()
            event.accept()
        else:
            event.ignore()

        self._clicked = False

    def mouseMoveEvent(self, event):
        event.ignore()

    def mousePressEvent(self, event):
        # handle an internal move
        # Start a drag event
        if event.button() == Qt.LeftButton and self.dragDropRect().contains(event.pos()):
            # Create the pixmap
            pixmap = QPixmap.grabWidget(self, self.rect())
            # Create the mimedata
            mimeData = QMimeData()
            mimeData.setText('ItemTitle::%s' % (self.title()))
            # Create the drag
            drag = QDrag(self)
            drag.setMimeData(mimeData)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())

            if not drag.exec_():
                self._accordianWidget.emitItemDragFailed(self)

            event.accept()

        # Determine if the expand/collapse should occur
        elif event.button() == Qt.LeftButton and self.expandCollapseRect().contains(event.pos()):
            self._clicked = True
            event.accept()
        else:
            event.ignore()

    def isCollapsed(self):
        return self._collapsed

    def isCollapsible(self):
        return self._collapsible

    def __drawTriangle(self, painter, x, y):
        brush = QBrush(QColor(255, 255, 255, 160), Qt.SolidPattern)
        if not self.isCollapsed():
            tl, tr, tp = QPoint(x + 9, y + 8), QPoint(x + 19, y + 8), QPoint(x + 14, y + 13.0)
            points = [tl, tr, tp]
            triangle = QPolygon(points)
        else:
            tl, tr, tp = QPoint(x + 11, y + 6), QPoint(x + 16, y + 11), QPoint(x + 11, y + 16.0)
            points = [tl, tr, tp]
            triangle = QPolygon(points)
        currentBrush = painter.brush()
        painter.setBrush(brush)
        painter.drawPolygon(triangle)
        painter.setBrush(currentBrush)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(painter.Antialiasing)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)

        x = self.rect().x()
        y = self.rect().y()
        w = self.rect().width() - 1
        h = self.rect().height() - 1
        r = 8

        # Draw a rounded style
        if self._rolloutStyle == 2:
            # Draw the text
            painter.drawText(x + 33, y + 3, w, 16, Qt.AlignLeft | Qt.AlignTop, self.title())
            # Draw the triangle
            self.__drawTriangle(painter, x, y)
            # Draw the borders
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.6)
            painter.setPen(pen)
            painter.drawRoundedRect(x + 1, y + 1, w - 1, h - 1, r, r)

            pen.setColor(self.palette().color(QPalette.Shadow))
            painter.setPen(pen)
            painter.drawRoundedRect(x, y, w - 1, h - 1, r, r)

        # Draw a square style
        if self._rolloutStyle == 3:
            # draw the text
            painter.drawText(x + 33, y + 3, w, 16, Qt.AlignLeft | Qt.AlignTop, self.title())
            self.__drawTriangle(painter, x, y)
            # draw the borders
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.6)
            painter.setPen(pen)
            painter.drawRect(x + 1, y + 1, w - 1, h - 1)

            pen.setColor(self.palette().color(QPalette.Shadow))
            painter.setPen(pen)
            painter.drawRect(x, y, w - 1, h - 1)

        # Draw a Maya style
        if self._rolloutStyle == 4:
            # Draw the text
            painter.drawText(x + 33, y + 3, w, 16, Qt.AlignLeft | Qt.AlignTop, self.title())
            painter.setRenderHint(QPainter.Antialiasing, False)
            self.__drawTriangle(painter, x, y)
            # Draw the borders - top
            headerHeight = 20
            headerRect = QRect(x + 1, y + 1, w - 1, headerHeight)
            headerRectShadow = QRect(x - 1, y - 1, w + 1, headerHeight + 2)
            # Highlight
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.4)
            painter.setPen(pen)
            painter.drawRect(headerRect)
            painter.fillRect(headerRect, QColor(255, 255, 255, 18))
            # Shadow
            pen.setColor(self.palette().color(QPalette.Dark))
            painter.setPen(pen)
            painter.drawRect(headerRectShadow)

            if not self.isCollapsed():
                # Draw the lover border
                pen = QPen(self.palette().color(QPalette.Dark))
                pen.setWidthF(0.8)
                painter.setPen(pen)
                offSet = headerHeight + 3
                bodyRect = QRect(x, y + offSet, w, h - offSet)
                bodyRectShadow = QRect(x + 1, y + offSet, w + 1, h - offSet + 1)
                painter.drawRect(bodyRect)

                pen.setColor(self.palette().color(QPalette.Light))
                pen.setWidthF(0.4)
                painter.setPen(pen)
                painter.drawRect(bodyRectShadow)

        # Draw a boxed style
        elif self._rolloutStyle == 1:
            if self.isCollapsed():
                arect = QRect(x + 1, y + 9, w - 1, 4)
                brect = QRect(x, y + 8, w - 1, 4)
                text = '+'
            else:
                arect = QRect(x + 1, y + 9, w - 1, h - 9)
                brect = QRect(x, y + 8, w - 1, h - 9)
                text = '-'

            # Draw the borders
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.6)
            painter.setPen(pen)
            painter.drawRect(arect)

            pen.setColor(self.palette().color(QPalette.Shadow))
            painter.setPen(pen)
            painter.drawRect(brect)
            painter.setRenderHint(painter.Antialiasing, False)
            painter.setBrush(self.palette().color(QPalette.Window).darker(120))
            painter.drawRect(x + 10, y + 1, w - 20, 16)
            painter.drawText(x + 16, y + 1, w - 32, 16, Qt.AlignLeft | Qt.AlignVCenter, text)
            painter.drawText(x + 10, y + 1, w - 20, 16, Qt.AlignCenter, self.title())

        if self.dragDropMode():
            rect = self.dragDropRect()
            # Draw the lines
            l = rect.left()
            r = rect.right()
            cy = rect.center().y()
            for y in (cy - 3, cy, cy + 3):
                painter.drawLine(l, y, r, y)

        painter.end()

    def setCollapsed(self, state=True):
        if self.isCollapsible():
            accord = self.accordionWidget()
            accord.setUpdatesEnabled(False)
            self._collapsed = state
            if state:
                self.setMinimumHeight(22)
                self.setMaximumHeight(22)
                self.widget().setVisible(False)
            else:
                self.setMinimumHeight(0)
                self.setMaximumHeight(1000000)
                self.widget().setVisible(True)

            self._accordianWidget.emitItemCollapsed(self)
            accord.setUpdatesEnabled(True)

    def setCollapsible(self, state=True):
        self._collapsible = state

    def setCustomData(self, key, value):
        """
        \remarks    set a custom pointer to information stored on this item
        \param              key             <str>
        \param              value   <variant>
        """
        self._customData[str(key)] = value

    def setDragDropMode(self, mode):
        self._dragDropMode = mode

    def setRolloutStyle(self, style):
        self._rolloutStyle = style

    def showMenu(self):
        if QRect(0, 0, self.width(), 20).contains(self.mapFromGlobal(QCursor.pos())):
            self._accordianWidget.emitItemMenuRequested(self)

    def rolloutStyle(self):
        return self._rolloutStyle

    def toggleCollapsed(self):
        self.setCollapsed(not self.isCollapsed())

    def widget(self):
        return self._widget


class AccordionWidget(QScrollArea):
    """
    \namespace      trax.gui.widgets.accordianwidget
    \remarks        A container widget for creating expandable and collapsible components
    \author         beta@blur.com
    \author         Blur Studio
    \date           04/29/10
    """
    itemCollapsed = Signal(AccordionItem)
    itemMenuRequested = Signal(AccordionItem)
    itemDragFailed = Signal(AccordionItem)
    itemsReordered = Signal()

    Boxed = 1
    Rounded = 2
    Square = 3
    Maya = 4

    NoDragDrop = 0
    InternalMove = 1

    def __init__(self, parent):
        QScrollArea.__init__(self, parent)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setAutoFillBackground(False)
        self.setWidgetResizable(True)
        self.setMouseTracking(True)
        # self.verticalScrollBar().setMaximumWidth(10)
        widget = QWidget(self)
        # Define custom properties
        self._rolloutStyle = AccordionWidget.Rounded
        self._dragDropMode = AccordionWidget.NoDragDrop
        self._scrolling = False
        self._scrollInitY = 0
        self._scrollInitVal = 0
        self._itemClass = AccordionItem
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        layout.addStretch(1)
        widget.setLayout(layout)
        self.setWidget(widget)

    def setSpacing(self, spaceInt):
        self.widget().layout().setSpacing(spaceInt)

    def addItem(self, title, widget, collapsed=False):
        self.setUpdatesEnabled(False)
        item = self._itemClass(self, title, widget)
        item.setRolloutStyle(self.rolloutStyle())
        item.setDragDropMode(self.dragDropMode())
        layout = self.widget().layout()
        layout.insertWidget(layout.count() - 1, item)
        layout.setStretchFactor(item, 0)

        if collapsed:
            item.setCollapsed(collapsed)

        self.setUpdatesEnabled(True)
        return item

    def clear(self):
        self.setUpdatesEnabled(False)
        layout = self.widget().layout()
        while layout.count() > 1:
            item = layout.itemAt(0)
            # Remove the item from the layout
            w = item.widget()
            layout.removeItem(item)
            # Close the widget and delete it
            w.close()
            w.deleteLater()

        self.setUpdatesEnabled(True)

    def eventFilter(self, object, event):
        if event.type() == QEvent.MouseButtonPress:
            self.mousePressEvent(event)
            return True
        elif event.type() == QEvent.MouseMove:
            self.mouseMoveEvent(event)
            return True
        elif event.type() == QEvent.MouseButtonRelease:
            self.mouseReleaseEvent(event)
            return True

        return False

    def canScroll(self):
        return self.verticalScrollBar().maximum() > 0

    def count(self):
        return self.widget().layout().count() - 1

    def dragDropMode(self):
        return self._dragDropMode

    def indexOf(self, widget):
        """
        \remarks    Searches for widget(not including child layouts).
                    Returns the index of widget, or -1 if widget is not found
        \return             <int>
        """
        layout = self.widget().layout()
        for index in range(layout.count()):
            if layout.itemAt(index).widget().widget() == widget:
                return index
        return -1

    def isBoxedMode(self):
        return self._rolloutStyle == AccordionWidget.Boxed

    def itemClass(self):
        return self._itemClass

    def itemAt(self, index):
        layout = self.widget().layout()
        if 0 <= index and index < layout.count() - 1:
            return layout.itemAt(index).widget()
        return None

    def emitItemCollapsed(self, item):
        if not self.signalsBlocked():
            self.itemCollapsed.emit(item)

    def emitItemDragFailed(self, item):
        if not self.signalsBlocked():
            self.itemDragFailed.emit(item)

    def emitItemMenuRequested(self, item):
        if not self.signalsBlocked():
            self.itemMenuRequested.emit(item)

    def emitItemsReordered(self):
        if not self.signalsBlocked():
            self.itemsReordered.emit()

    def enterEvent(self, event):
        if self.canScroll():
            QApplication.setOverrideCursor(Qt.OpenHandCursor)

    def leaveEvent(self, event):
        if self.canScroll():
            QApplication.restoreOverrideCursor()

    def mouseMoveEvent(self, event):
        if self._scrolling:
            sbar = self.verticalScrollBar()
            smax = sbar.maximum()
            # Calculate the distance moved for the moust point
            dy = event.globalY() - self._scrollInitY
            # Calculate the percentage that is of the scroll bar
            dval = smax * (dy / float(sbar.height()))
            # Calculate the new value
            sbar.setValue(self._scrollInitVal - dval)

        event.accept()

    def mousePressEvent(self, event):
        # handle a scroll event
        if event.button() == Qt.LeftButton and self.canScroll():
            self._scrolling = True
            self._scrollInitY = event.globalY()
            self._scrollInitVal = self.verticalScrollBar().value()
            QApplication.setOverrideCursor(Qt.ClosedHandCursor)

        event.accept()

    def mouseReleaseEvent(self, event):
        if self._scrolling:
            QApplication.restoreOverrideCursor()

        self._scrolling = False
        self._scrollInitY = 0
        self._scrollInitVal = 0
        event.accept()

    def moveItemDown(self, index):
        layout = self.widget().layout()
        if (layout.count() - 1) > (index + 1):
            widget = layout.takeAt(index).widget()
            layout.insertWidget(index + 1, widget)

    def moveItemUp(self, index):
        if index > 0:
            layout = self.widget().layout()
            widget = layout.takeAt(index).widget()
            layout.insertWidget(index - 1, widget)

    def setBoxedMode(self, state):
        if state:
            self._rolloutStyle = AccordionWidget.Boxed
        else:
            self._rolloutStyle = AccordionWidget.Rounded

    def setDragDropMode(self, dragDropMode):
        self._dragDropMode = dragDropMode

        for item in self.findChildren(AccordionItem):
            item.setDragDropMode(self._dragDropMode)

    def setItemClass(self, itemClass):
        self._itemClass = itemClass

    def setRolloutStyle(self, rolloutStyle):
        self._rolloutStyle = rolloutStyle

        for item in self.findChildren(AccordionItem):
            item.setRolloutStyle(self._rolloutStyle)

    def rolloutStyle(self):
        return self._rolloutStyle

    def takeAt(self, index):
        self.setUpdatesEnabled(False)
        layout = self.widget().layout()
        widget = None
        if 0 <= index and index < layout.count() - 1:
            item = layout.itemAt(index)
            widget = item.widget()

            layout.removeItem(item)
            widget.close()
        self.setUpdatesEnabled(True)
        return widget

    def widgetAt(self, index):
        item = self.itemAt(index)
        if item:
            return item.widget()
        return None

    pyBoxedMode = Property('bool', isBoxedMode, setBoxedMode)


# _gUI = None
# from Qt.QtWidgets import QDialog, QVBoxLayout, QFrame, QPushButton

# class Sample(QDialog):
#     def __init__(self, parent=None):
#         super(Sample, self).__init__(parent)
#         self.setLayout(QVBoxLayout())
#         self.accWidget = AccordionWidget(self)
#         self.accWidget.addItem("A", self.buildFrame())
#         self.accWidget.addItem("B", self.buildFrame())
#         self.accWidget.setRolloutStyle(self.accWidget.Maya)
#         self.accWidget.setSpacing(0)  # More like Maya but I like some padding.
#         self.layout().addWidget(self.accWidget)

#     def buildFrame(self):
#         someFrame = QFrame(self)
#         someFrame.setLayout(QVBoxLayout())
#         someFrame.layout().addWidget(QPushButton("Test"))
#         return someFrame

#     @classmethod
#     def display(cls):
#         """Demo Display method for Maya"""
#         global _gUI
#         _gUI = cls()
#         _gUI.show()

