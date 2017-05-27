from Qt import QtWidgets, QtGui, QtCore


class BaseSliderWidget(QtWidgets.QWidget):
    """ A custom slider that bidirectionally connects a text field and a slider. """
    DEFAULT_MIN_VALUE = -1
    DEFAULT_MAX_VALUE = -1
    signal_value_changed = QtCore.Signal()

    def __init__(self, title=None, min_value=None, max_value=None, start_value=None, is_horizontal=False,
                 spacing=4, margins=QtCore.QMargins(1, 1, 1, 1), parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self._slider = None
        self._text = None

        if min_value is None:
            self._min_value = self.DEFAULT_MIN_VALUE
        else:
            self._min_value = min_value

        if max_value is None:
            self._max_value = self.DEFAULT_MAX_VALUE
        else:
            self._max_value = max_value

        if is_horizontal:
            self.setLayout(QtWidgets.QHBoxLayout(self))
        else:
            self.setLayout(QtWidgets.QVBoxLayout(self))

        if title is not None:
            label = QtWidgets.QLabel(title)
            self.layout().addWidget(label)

        validator = self._get_validator()
        self._text = QtWidgets.QLineEdit()
        self._text.setValidator(validator)
        self.layout().addWidget(self._text)

        self._slider = QtWidgets.QSlider()
        self._slider.setOrientation(QtCore.Qt.Horizontal)
        self._setup_slider(self._slider)
        self.layout().addWidget(self._slider)

        self.layout().setContentsMargins(margins)
        self.layout().setSpacing(spacing)

        self._setup_values(start_value=start_value)

        self._text.textChanged.connect(self._on_text_changed)
        self._slider.valueChanged.connect(self._on_slider_changed)

    def set_value(self, value):
        self._text.setText(str(value))

    def get_value(self):
        raise NotImplementedError(
            "Implement the get_value method for the slider type.")

    def _get_validator(self):
        raise NotImplementedError(
            "Implement the _get_validator method for the slider type.")

    def _setup_slider(self, slider):
        raise NotImplementedError(
            "Implement the _setup_slider method for the slider type")

    def _setup_values(self, start_value=None):
        raise NotImplementedError(
            "Implement the _setup_values method for the slider type")

    def _on_text_changed(self):
        raise NotImplementedError(
            "Implement the _on_text_changed method for the slider type")

    def _on_slider_changed(self):
        raise NotImplementedError(
            "Implement the _on_slider_changed method for the slider type")


class FloatSliderWidget(BaseSliderWidget):
    """ Custom float slider widget. """

    DEFAULT_MIN_VALUE = 0.0
    DEFAULT_MAX_VALUE = 1.0
    SLIDER_TICKS = 5000  # Granularity.

    # Implemented #

    def get_value(self):
        return self._slider_value_to_text_value(self._float_sldr.value())

    def _get_validator(self):
        return QtGui.QDoubleValidator()

    def _setup_slider(self, slider):
        slider.setRange(0, self.SLIDER_TICKS)

    def _setup_values(self, start_value=None):
        if start_value is None:
            self._text.setText(str((self._min_value + self._max_value) / 2.0))
            self._slider.setValue(self.SLIDER_TICKS / 2.0)
        else:
            self._text.setText(str(start_value))
            slider_value = (start_value - self._min_value) * self.SLIDER_TICKS / (self._max_value - self._min_value)
            self._slider.setValue(slider_value)

    def _on_text_changed(self):
        value = float(self._text.text())
        self._slider.valueChanged.disconnect(self._on_slider_changed)

        if value > self._max_value:
            self._text.setText(str(self._max_value))
        if value < self._min_value:
            self._text.setText(str(self._min_value))

        slider_value = (value - self._min_value) * self.SLIDER_TICKS / (self._max_value - self._min_value)
        self._slider.setValue(slider_value)
        self._slider.valueChanged.connect(self._on_slider_changed)
        self.signal_value_changed.emit()

    def _on_slider_changed(self):
        value = float(self._slider.value())
        self._text.textChanged.disconnect(self._on_text_changed)
        text_value = self._slider_value_to_text_value(value)
        self._text.setText(str(text_value))
        self._text.textChanged.connect(self._on_text_changed)
        self.signal_value_changed.emit()

    # Other #

    def _slider_value_to_text_value(self, value):
        return self._min_value + value * (self._max_value - self._min_value) / self.SLIDER_TICKS


class IntegerSliderWidget(BaseSliderWidget):
    """ Custom integer slider widget. """

    DEFAULT_MIN_VALUE = 0
    DEFAULT_MAX_VALUE = 100

    # Implemented #

    def get_value(self):
        return self._sliders.value()

    def _get_validator(self):
        return QtGui.QIntValidator()

    def _setup_slider(self, slider):
        slider.setRange(self._min_value, self._max_value)

    def _setup_values(self, start_value=None):
        if start_value is None:
            self._text.setText(str((self._min_value + self._max_value) / 2))
            self._slider.setValue((self._max_value - self._min_value) / 2)
        else:
            self._text.setText(str(start_value))
            self._slider.setValue(start_value)

    def _on_text_changed(self):
        value = int(self._text.text())
        self._sliders.valueChanged.disconnect(self._on_slider_changed)

        if value > self._max_value:
            self._text.setText(str(self._max_value))
        if value < self._min_value:
            self._text.setText(str(self._min_value))

        self._sliders.setValue(value)
        self._sliders.valueChanged.connect(self._on_slider_changed)

    def _on_slider_changed(self):
        value = int(self._sliders.value())
        self._text.textChanged.disconnect(self._on_text_changed)
        self._text.setText(str(value))
        self._text.textChanged.connect(self._on_text_changed)
