import ast
import math
import operator
import random
import re
import sys

from PyQt5.QtCore import QSignalBlocker, QTimer, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class SequenceGraph(QWidget):
    def __init__(self):
        super().__init__()
        self.values = []
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_values(self, values):
        self.values = values[:]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(9, 13, 21, 190))

        margin = 28
        graph_width = max(self.width() - margin * 2, 1)
        graph_height = max(self.height() - margin * 2, 1)
        left = margin
        bottom = self.height() - margin

        painter.setPen(QPen(QColor(92, 132, 184, 95), 1))
        painter.drawLine(left, margin, left, bottom)
        painter.drawLine(left, bottom, self.width() - margin, bottom)

        for i in range(1, 4):
            y = margin + int(graph_height * i / 4)
            painter.setPen(QPen(QColor(92, 132, 184, 38), 1))
            painter.drawLine(left, y, self.width() - margin, y)

        if not self.values:
            painter.setPen(QColor(174, 192, 216, 180))
            painter.drawText(self.rect(), Qt.AlignCenter, "Graph will appear here")
            return

        max_value = max(self.values)
        min_value = min(self.values)
        value_range = max(max_value - min_value, 1)
        step = graph_width / max(len(self.values) - 1, 1)

        points = []
        for index, value in enumerate(self.values):
            x = left + index * step
            y = bottom - ((value - min_value) / value_range) * graph_height
            points.append((int(x), int(y)))

        painter.setPen(QPen(QColor(88, 150, 214, 225), 2))
        for start, end in zip(points, points[1:]):
            painter.drawLine(start[0], start[1], end[0], end[1])

        painter.setBrush(QColor(205, 224, 245, 230))
        painter.setPen(Qt.NoPen)
        point_stride = max(len(points) // 80, 1)
        for point in points[::point_stride]:
            painter.drawEllipse(point[0] - 2, point[1] - 2, 4, 4)

        painter.setPen(QColor(180, 205, 235, 180))
        painter.drawText(left, 18, f"max {max_value}")
        painter.drawText(self.width() - 120, bottom + 20, f"{len(self.values)} steps")


class MathHub(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Your Handy Calculator Hub")
        self.setWindowIcon(QIcon("Graph.ico"))
        self.resize(940, 640)
        self.setMinimumSize(620, 460)
        self.setMouseTracking(True)
        self.loading_step = 0
        self.layers = [
            {"speed": 0.2, "size": 2, "count": 55, "alpha": 55, "z": 0.35},
            {"speed": 0.45, "size": 3, "count": 35, "alpha": 95, "z": 0.65},
            {"speed": 0.75, "size": 4, "count": 18, "alpha": 135, "z": 1.0},
        ]
        self.particles = []
        self.last_particle_width = self.width()
        self.last_particle_height = self.height()
        self.init_particles()
        self.current_engine_key = "math"
        self.engines = [
            {
                "key": "math",
                "name": "Math Engine",
                "covers": "Algebra, graphs, calculus, matrices",
                "keywords": "math algebra graph calculus matrices equations functions numbers",
                "tools": [
                    ("Basic Calculator", self.show_basic, "arithmetic everyday simple"),
                    ("Scientific Calculator", self.show_scientific, "trig roots logs powers"),
                    ("Quadratic Solver", self.show_quadratic, "equation roots polynomial algebra"),
                    ("Collatz Sequence", self.show_collatz, "sequence graph pattern"),
                    ("Prime Checker", self.show_prime, "prime divisibility factors"),
                    ("Factorial", self.show_factorial, "factorial permutations counting"),
                    ("Function Grapher", self.show_function_grapher, "function graph plot y x"),
                    ("2x2 Matrix Solver", self.show_matrix_solver, "matrix determinant inverse"),
                    ("Derivative Finder", self.show_derivative_finder, "derivative slope calculus"),
                    ("Integral Helper", self.show_integral_helper, "integral area calculus"),
                ],
                "planned": [],
            },
            {
                "key": "finance",
                "name": "Finance Engine",
                "covers": "Money, loans, investing, tax",
                "keywords": "finance money loan mortgage investing interest tax budget",
                "tools": [
                    ("Tip Calculator", self.show_tip_calculator, "tip restaurant bill split"),
                    ("Loan Payment", self.show_loan_payment, "loan payment apr interest"),
                    ("Mortgage Estimate", self.show_mortgage_estimate, "mortgage house payment loan"),
                    ("Compound Interest", self.show_compound_interest, "investing compound interest savings"),
                    ("Tax Helper", self.show_tax_helper, "tax percent income sales"),
                ],
                "planned": [],
            },
            {
                "key": "conversion",
                "name": "Conversion Engine",
                "covers": "Units, measurements, everyday conversions",
                "keywords": "conversion units measurements length weight temperature cooking currency",
                "tools": [
                    ("Unit Converter", self.show_unit_converter, "length weight distance units"),
                    ("Temperature Converter", self.show_temperature_converter, "celsius fahrenheit kelvin"),
                    ("Cooking Measurements", self.show_cooking_converter, "cups tablespoons teaspoons cooking"),
                    ("Currency Helper", self.show_currency_helper, "currency exchange money"),
                ],
                "planned": [],
            },
            {
                "key": "science",
                "name": "Science Engine",
                "covers": "Physics, chemistry, engineering",
                "keywords": "science physics chemistry engineering formulas motion energy molar",
                "tools": [
                    ("Physics Formula Solver", self.show_physics_solver, "physics force velocity energy"),
                    ("Molar Mass", self.show_molar_mass, "chemistry molar mass molecules"),
                    ("Ohm's Law", self.show_ohms_law, "voltage current resistance"),
                    ("Density Calculator", self.show_density_calculator, "density mass volume"),
                ],
                "planned": [],
            },
            {
                "key": "data",
                "name": "Data Engine",
                "covers": "Stats, health, time, analysis",
                "keywords": "data stats statistics health time analysis average median bmi date",
                "tools": [
                    ("Mean Median Mode", self.show_mean_median_mode, "stats average median mode"),
                    ("Standard Deviation", self.show_standard_deviation, "statistics deviation variance"),
                    ("BMI Calculator", self.show_bmi_calculator, "health bmi weight height"),
                    ("Time Difference", self.show_time_difference, "time hours minutes difference"),
                ],
                "planned": [],
            },
        ]

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(28, 24, 28, 24)
        self.main_layout.setSpacing(16)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(20)

        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.advance_loading)

        self.setStyleSheet(APP_STYLE)
        self.show_loading()

    def init_particles(self):
        self.particles.clear()
        width = max(self.width(), 1)
        height = max(self.height(), 1)
        for layer_index, layer in enumerate(self.layers):
            for _ in range(layer["count"]):
                self.particles.append(
                    {
                        "x": random.uniform(0, width),
                        "y": random.uniform(0, height),
                        "vx": random.uniform(-0.14, 0.14),
                        "vy": random.uniform(-0.14, 0.14),
                        "layer": layer_index,
                    }
                )

    def resizeEvent(self, event):
        old_width = max(self.last_particle_width, 1)
        old_height = max(self.last_particle_height, 1)
        new_width = max(self.width(), 1)
        new_height = max(self.height(), 1)

        width_ratio = new_width / old_width
        height_ratio = new_height / old_height
        for particle in self.particles:
            particle["x"] *= width_ratio
            particle["y"] *= height_ratio

        self.last_particle_width = new_width
        self.last_particle_height = new_height
        super().resizeEvent(event)

    def update_scene(self):
        width = max(self.width(), 1)
        height = max(self.height(), 1)

        for particle in self.particles:
            layer = self.layers[particle["layer"]]
            particle["x"] += particle["vx"] * layer["speed"] * 45
            particle["y"] += particle["vy"] * layer["speed"] * 45

            if particle["x"] < -5:
                particle["x"] = width + 5
            elif particle["x"] > width + 5:
                particle["x"] = -5
            if particle["y"] < -5:
                particle["y"] = height + 5
            elif particle["y"] > height + 5:
                particle["y"] = -5

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#090b10"))

        painter.setPen(QPen(QColor(65, 115, 185, 45), 1))
        width = self.width()
        height = self.height()
        for offset in range(-120, height + 120, 80):
            points = []
            for x in range(0, width + 20, 20):
                y = offset + math.sin((x + self.loading_step * 4) / 70) * 18
                points.append((x, int(y)))
            for start, end in zip(points, points[1:]):
                painter.drawLine(start[0], start[1], end[0], end[1])

        for particle in self.particles:
            layer = self.layers[particle["layer"]]
            painter.setBrush(QColor(130, 190, 255, layer["alpha"]))
            painter.drawEllipse(
                int(particle["x"]),
                int(particle["y"]),
                layer["size"],
                layer["size"],
            )

    def advance_loading(self):
        self.loading_step += 1
        symbols = ["+", "-", "x", "/", "pi", "sqrt", "=", "sum"]
        if hasattr(self, "loading_symbol"):
            self.loading_symbol.setText(symbols[self.loading_step % len(symbols)])
        if self.loading_step >= 18:
            self.loading_timer.stop()
            self.show_home()

    def clear_content(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            self.delete_layout_item(item)

    def delete_layout_item(self, item):
        widget = item.widget()
        if widget:
            widget.deleteLater()
            return

        layout = item.layout()
        if layout:
            while layout.count():
                self.delete_layout_item(layout.takeAt(0))
            layout.deleteLater()

    def make_title(self, text, subtitle=None):
        wrap = QWidget()
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        heading = QLabel(text)
        heading.setObjectName("title")
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("subtitle")
            sub.setAlignment(Qt.AlignCenter)
            sub.setWordWrap(True)
            layout.addWidget(sub)

        return wrap

    def make_button(self, text, callback, accent=False):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(44)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if accent:
            button.setObjectName("accentButton")
        button.clicked.connect(callback)
        return button

    def make_label(self, text, object_name="subtitle", align=Qt.AlignLeft):
        label = QLabel(text)
        label.setObjectName(object_name)
        label.setAlignment(align)
        label.setWordWrap(True)
        return label

    def make_input(self, placeholder):
        entry = QLineEdit()
        entry.setPlaceholderText(placeholder)
        entry.setMinimumHeight(42)
        return entry

    def make_expression_input(self, placeholder):
        entry = self.make_input(placeholder)
        entry.textChanged.connect(lambda _text: self.normalize_expression_input(entry))
        return entry

    def normalize_expression_input(self, entry):
        original = entry.text()
        normalized = normalize_display_expression(original)
        if original == normalized:
            return

        cursor = entry.cursorPosition()
        blocker = QSignalBlocker(entry)
        entry.setText(normalized)
        entry.setCursorPosition(min(cursor, len(normalized)))
        del blocker

    def insert_expression_text(self, entry, text, cursor_shift=0):
        cursor = entry.cursorPosition()
        current = entry.text()
        entry.setText(current[:cursor] + text + current[cursor:])
        entry.setCursorPosition(cursor + len(text) + cursor_shift)
        entry.setFocus()

    def make_symbol_pad(self, entry, symbols):
        pad = QFrame()
        pad.setObjectName("symbolPad")
        layout = QVBoxLayout(pad)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        for row_symbols in symbols:
            row = QHBoxLayout()
            row.setSpacing(8)
            for label, insert_text, cursor_shift in row_symbols:
                symbol_button = self.make_button(label, lambda checked=False, text=insert_text, shift=cursor_shift: self.insert_expression_text(entry, text, shift))
                symbol_button.setObjectName("symbolButton")
                symbol_button.setMinimumWidth(48)
                row.addWidget(symbol_button)
            layout.addLayout(row)

        return pad

    def add_button_rows(self, layout, items, per_row=3):
        for start in range(0, len(items), per_row):
            row = QHBoxLayout()
            row.setSpacing(12)
            for label, callback in items[start:start + per_row]:
                row.addWidget(self.make_button(label, callback, accent=True))
            layout.addLayout(row)

    def make_result(self):
        result = QLabel("")
        result.setObjectName("result")
        result.setWordWrap(True)
        result.setTextInteractionFlags(Qt.TextSelectableByMouse)
        result.setMinimumHeight(44)
        return result

    def make_panel(self):
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)
        return panel, layout

    def add_back_button(self):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        back = self.make_button("Back", lambda: self.show_engine(self.current_engine_key))
        back.setObjectName("secondaryButton")
        back.setFixedWidth(110)
        row.addWidget(back)
        row.addStretch()
        self.main_layout.addLayout(row)

    def add_system_back_button(self):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        back = self.make_button("Systems", self.show_engine_menu)
        back.setObjectName("secondaryButton")
        back.setFixedWidth(110)
        row.addWidget(back)
        row.addStretch()
        self.main_layout.addLayout(row)

    def show_loading(self):
        self.clear_content()
        self.loading_step = 0
        self.main_layout.addStretch()

        self.loading_symbol = QLabel("pi")
        self.loading_symbol.setObjectName("loadingSymbol")
        self.loading_symbol.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.loading_symbol)

        loading_text = QLabel("Getting the numbers ready")
        loading_text.setObjectName("subtitle")
        loading_text.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(loading_text)

        self.main_layout.addStretch()
        self.loading_timer.start(90)

    def show_home(self):
        self.clear_content()
        self.main_layout.addStretch()
        self.main_layout.addWidget(
            self.make_title("Your Handy Calculator", "Quick math tools in one clean place.")
        )

        start = self.make_button("Start", self.show_engine_menu, accent=True)
        start.setObjectName("startButton")
        start.setFixedWidth(220)
        start_row = QHBoxLayout()
        start_row.addStretch()
        start_row.addWidget(start)
        start_row.addStretch()
        self.main_layout.addLayout(start_row)
        self.main_layout.addStretch()

    def get_engine(self, engine_key):
        for engine in self.engines:
            if engine["key"] == engine_key:
                return engine
        return self.engines[0]

    def show_engine_menu(self):
        self.clear_content()
        self.main_layout.addWidget(
            self.make_title("Your Handy Calculator", "Everything is organized into five calculator systems.")
        )

        self.search_box = self.make_input("Search systems or calculators")
        self.search_box.textChanged.connect(lambda _text: self.populate_engine_menu())
        self.main_layout.addWidget(self.search_box)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("menuScroll")

        self.menu_container = QWidget()
        self.menu_results_layout = QVBoxLayout(self.menu_container)
        self.menu_results_layout.setContentsMargins(2, 2, 2, 2)
        self.menu_results_layout.setSpacing(14)
        scroll.setWidget(self.menu_container)
        self.main_layout.addWidget(scroll, 1)
        self.populate_engine_menu()

    def populate_engine_menu(self):
        while self.menu_results_layout.count():
            self.delete_layout_item(self.menu_results_layout.takeAt(0))

        query = self.search_box.text().strip().lower()
        matches_found = False

        for engine in self.engines:
            tool_matches = [
                label
                for label, _callback, keywords in engine["tools"]
                if query and (query in label.lower() or query in keywords)
            ]
            engine_matches = not query or query in engine["name"].lower() or query in engine["covers"].lower() or query in engine["keywords"]
            planned_matches = [
                item for item in engine["planned"] if query and query in item.lower()
            ]

            if not engine_matches and not tool_matches and not planned_matches:
                continue

            matches_found = True
            section = QLabel(engine["name"])
            section.setObjectName("sectionTitle")
            self.menu_results_layout.addWidget(section)
            self.menu_results_layout.addWidget(self.make_label(engine["covers"]))

            row = QHBoxLayout()
            row.setSpacing(12)
            row.addWidget(self.make_button("Open Engine", lambda checked=False, key=engine["key"]: self.show_engine(key), accent=True))
            if tool_matches:
                row.addWidget(self.make_label("Matches: " + ", ".join(tool_matches), "hintLabel"))
            elif planned_matches:
                row.addWidget(self.make_label("Planned: " + ", ".join(planned_matches), "hintLabel"))
            else:
                row.addWidget(self.make_label(f"{len(engine['tools'])} available now", "hintLabel"))
            self.menu_results_layout.addLayout(row)

        if not matches_found:
            empty = QLabel("No systems or calculators found")
            empty.setObjectName("subtitle")
            empty.setAlignment(Qt.AlignCenter)
            self.menu_results_layout.addWidget(empty)

        self.menu_results_layout.addStretch()

    def show_engine(self, engine_key):
        engine = self.get_engine(engine_key)
        self.current_engine_key = engine["key"]
        self.clear_content()
        self.add_system_back_button()
        self.main_layout.addWidget(self.make_title(engine["name"], engine["covers"]))

        self.engine_search_box = self.make_input("Search inside this engine")
        self.engine_search_box.textChanged.connect(lambda _text: self.populate_engine_tools(engine))
        self.main_layout.addWidget(self.engine_search_box)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("menuScroll")

        self.engine_container = QWidget()
        self.engine_results_layout = QVBoxLayout(self.engine_container)
        self.engine_results_layout.setContentsMargins(2, 2, 2, 2)
        self.engine_results_layout.setSpacing(14)
        scroll.setWidget(self.engine_container)
        self.main_layout.addWidget(scroll, 1)
        self.populate_engine_tools(engine)

    def populate_engine_tools(self, engine):
        while self.engine_results_layout.count():
            self.delete_layout_item(self.engine_results_layout.takeAt(0))

        query = self.engine_search_box.text().strip().lower()
        visible_tools = [
            (label, callback)
            for label, callback, keywords in engine["tools"]
            if not query or query in label.lower() or query in keywords
        ]
        visible_planned = [
            item for item in engine["planned"] if not query or query in item.lower()
        ]

        if visible_tools:
            available = QLabel("Available now")
            available.setObjectName("sectionTitle")
            self.engine_results_layout.addWidget(available)
            self.add_button_rows(self.engine_results_layout, visible_tools)

        if visible_planned:
            planned = QLabel("Planned tools")
            planned.setObjectName("sectionTitle")
            self.engine_results_layout.addWidget(planned)
            for item in visible_planned:
                self.engine_results_layout.addWidget(self.make_label(item, "plannedItem"))

        if not visible_tools and not visible_planned:
            empty = QLabel("No matches inside this engine")
            empty.setObjectName("subtitle")
            empty.setAlignment(Qt.AlignCenter)
            self.engine_results_layout.addWidget(empty)

        self.engine_results_layout.addStretch()

    def show_tool(self, heading, builder):
        self.clear_content()
        self.add_back_button()
        self.main_layout.addWidget(self.make_title(heading))
        panel, layout = self.make_panel()
        builder(layout)
        self.main_layout.addWidget(panel)
        self.main_layout.addStretch()

    def show_form_tool(self, heading, fields, calculate):
        def build(layout):
            inputs = {}
            for key, placeholder in fields:
                entry = self.make_input(placeholder)
                inputs[key] = entry
                layout.addWidget(entry)

            result = self.make_result()

            def run():
                try:
                    result.setText(calculate({key: field.text() for key, field in inputs.items()}))
                except Exception:
                    result.setText("Enter valid numbers and try again.")

            for entry in inputs.values():
                entry.returnPressed.connect(run)
            layout.addWidget(self.make_button("Calculate", run, accent=True))
            layout.addWidget(result)

        self.show_tool(heading, build)

    def show_basic(self):
        def build(layout):
            expression = self.make_expression_input("Example: (8 + 4) ÷ 3")
            result = self.make_result()

            def calculate():
                result.setText(safe_calculate(expression.text()))

            expression.returnPressed.connect(calculate)
            layout.addWidget(expression)
            layout.addWidget(
                self.make_symbol_pad(
                    expression,
                    [
                        [("7", "7", 0), ("8", "8", 0), ("9", "9", 0), ("÷", " ÷ ", 0)],
                        [("4", "4", 0), ("5", "5", 0), ("6", "6", 0), ("×", " × ", 0)],
                        [("1", "1", 0), ("2", "2", 0), ("3", "3", 0), ("-", " - ", 0)],
                        [("0", "0", 0), (".", ".", 0), ("(", "(", 0), (")", ")", 0), ("+", " + ", 0)],
                    ],
                )
            )
            layout.addWidget(self.make_button("Calculate", calculate, accent=True))
            layout.addWidget(result)

        self.show_tool("Basic Calculator", build)

    def show_scientific(self):
        def build(layout):
            expression = self.make_expression_input("Example: sin(π ÷ 2) + √(16)")
            result = self.make_result()

            def calculate():
                result.setText(safe_calculate(expression.text(), scientific=True))

            expression.returnPressed.connect(calculate)
            layout.addWidget(expression)
            layout.addWidget(
                self.make_symbol_pad(
                    expression,
                    [
                        [("π", "π", 0), ("e", "e", 0), ("τ", "τ", 0), ("^", "^", 0), ("√", "√()", -1)],
                        [("sin", "sin()", -1), ("cos", "cos()", -1), ("tan", "tan()", -1)],
                        [("log", "log10()", -1), ("ln", "ln()", -1), ("(", "(", 0), (")", ")", 0)],
                        [("+", " + ", 0), ("-", " - ", 0), ("×", " × ", 0), ("÷", " ÷ ", 0)],
                    ],
                )
            )
            layout.addWidget(self.make_button("Calculate", calculate, accent=True))
            layout.addWidget(result)

        self.show_tool("Scientific Calculator", build)

    def show_collatz(self):
        def build(layout):
            number = self.make_input("Enter a positive whole number")
            graph = SequenceGraph()
            result = self.make_result()

            def run():
                try:
                    value = int(number.text())
                    if value < 1:
                        raise ValueError
                    sequence = []
                    while value != 1 and len(sequence) < 2000:
                        sequence.append(value)
                        value = value // 2 if value % 2 == 0 else 3 * value + 1
                    sequence.append(1)
                    graph.set_values(sequence)
                    result.setText(" -> ".join(map(str, sequence)))
                except ValueError:
                    graph.set_values([])
                    result.setText("Enter a positive whole number.")

            number.returnPressed.connect(run)
            layout.addWidget(number)
            layout.addWidget(self.make_button("Run", run, accent=True))
            layout.addWidget(graph)
            layout.addWidget(result)

        self.show_tool("Collatz Sequence", build)

    def show_prime(self):
        def build(layout):
            number = self.make_input("Enter a whole number")
            result = self.make_result()

            def check():
                try:
                    value = int(number.text())
                    result.setText("Prime" if is_prime(value) else "Not prime")
                except ValueError:
                    result.setText("Enter a whole number.")

            number.returnPressed.connect(check)
            layout.addWidget(number)
            layout.addWidget(self.make_button("Check", check, accent=True))
            layout.addWidget(result)

        self.show_tool("Prime Checker", build)

    def show_factorial(self):
        def build(layout):
            number = self.make_input("Enter a whole number from 0 to 500")
            result = self.make_result()

            def calculate():
                try:
                    value = int(number.text())
                    if value < 0 or value > 500:
                        raise ValueError
                    result.setText(str(math.factorial(value)))
                except ValueError:
                    result.setText("Enter a whole number from 0 to 500.")

            number.returnPressed.connect(calculate)
            layout.addWidget(number)
            layout.addWidget(self.make_button("Calculate", calculate, accent=True))
            layout.addWidget(result)

        self.show_tool("Factorial", build)

    def show_quadratic(self):
        def build(layout):
            a = self.make_input("a")
            b = self.make_input("b")
            c = self.make_input("c")
            result = self.make_result()

            def solve():
                try:
                    value_a = float(a.text())
                    value_b = float(b.text())
                    value_c = float(c.text())
                    if value_a == 0:
                        result.setText("a cannot be 0 for a quadratic equation.")
                        return
                    discriminant = value_b * value_b - 4 * value_a * value_c
                    if discriminant < 0:
                        real = -value_b / (2 * value_a)
                        imaginary = math.sqrt(abs(discriminant)) / (2 * value_a)
                        result.setText(f"{real:.6g} + {imaginary:.6g}i, {real:.6g} - {imaginary:.6g}i")
                    else:
                        root = math.sqrt(discriminant)
                        x1 = (-value_b + root) / (2 * value_a)
                        x2 = (-value_b - root) / (2 * value_a)
                        result.setText(f"{x1:.6g}, {x2:.6g}")
                except ValueError:
                    result.setText("Enter numeric values for a, b, and c.")

            for entry in (a, b, c):
                entry.returnPressed.connect(solve)
                layout.addWidget(entry)
            layout.addWidget(self.make_button("Solve", solve, accent=True))
            layout.addWidget(result)

        self.show_tool("Quadratic Solver", build)

    def show_function_grapher(self):
        def build(layout):
            expression = self.make_expression_input("Function of x, example: x^2 - 4x + 3")
            start = self.make_input("Start x, example: -10")
            end = self.make_input("End x, example: 10")
            graph = SequenceGraph()
            result = self.make_result()

            def run():
                try:
                    x1 = float(start.text() or "-10")
                    x2 = float(end.text() or "10")
                    values = []
                    samples = 120
                    for index in range(samples):
                        x = x1 + (x2 - x1) * index / (samples - 1)
                        values.append(calculate_value(expression.text(), scientific=True, variables={"x": x}))
                    graph.set_values(values)
                    result.setText(f"Plotted y = {expression.text()} from x = {x1:g} to x = {x2:g}.")
                except Exception:
                    graph.set_values([])
                    result.setText("Enter a valid function and range.")

            for entry in (expression, start, end):
                entry.returnPressed.connect(run)
                layout.addWidget(entry)
            layout.addWidget(self.make_symbol_pad(expression, [[("x", "x", 0), ("^", "^", 0), ("√", "√()", -1), ("π", "π", 0)], [("+", " + ", 0), ("-", " - ", 0), ("×", " × ", 0), ("÷", " ÷ ", 0)]]))
            layout.addWidget(self.make_button("Graph", run, accent=True))
            layout.addWidget(graph)
            layout.addWidget(result)

        self.show_tool("Function Grapher", build)

    def show_matrix_solver(self):
        def calculate(values):
            a = float(values["a"])
            b = float(values["b"])
            c = float(values["c"])
            d = float(values["d"])
            det = a * d - b * c
            if det == 0:
                return f"Determinant: 0\nNo inverse exists."
            return (
                f"Determinant: {det:.6g}\n"
                f"Inverse:\n[{d / det:.6g}, {-b / det:.6g}]\n"
                f"[{-c / det:.6g}, {a / det:.6g}]"
            )

        self.show_form_tool("2x2 Matrix Solver", [("a", "Top left"), ("b", "Top right"), ("c", "Bottom left"), ("d", "Bottom right")], calculate)

    def show_derivative_finder(self):
        def calculate(values):
            expression = values["f"]
            x = float(values["x"] or "0")
            h = 0.00001
            y1 = calculate_value(expression, scientific=True, variables={"x": x + h})
            y0 = calculate_value(expression, scientific=True, variables={"x": x - h})
            return f"Approximate derivative at x = {x:g}: {(y1 - y0) / (2 * h):.8g}"

        self.show_form_tool("Derivative Finder", [("f", "Function of x, example: x^2 + 3x"), ("x", "x value")], calculate)

    def show_integral_helper(self):
        def calculate(values):
            expression = values["f"]
            a = float(values["a"])
            b = float(values["b"])
            steps = 800
            width = (b - a) / steps
            total = 0
            for index in range(steps):
                x = a + (index + 0.5) * width
                total += calculate_value(expression, scientific=True, variables={"x": x})
            return f"Approximate integral from {a:g} to {b:g}: {total * width:.8g}"

        self.show_form_tool("Integral Helper", [("f", "Function of x, example: x^2"), ("a", "Lower bound"), ("b", "Upper bound")], calculate)

    def show_tip_calculator(self):
        def calculate(values):
            bill = float(values["bill"])
            tip = float(values["tip"]) / 100
            people = max(int(float(values["people"] or "1")), 1)
            total = bill * (1 + tip)
            return f"Tip: ${bill * tip:.2f}\nTotal: ${total:.2f}\nEach person: ${total / people:.2f}"

        self.show_form_tool("Tip Calculator", [("bill", "Bill amount"), ("tip", "Tip percent"), ("people", "Number of people")], calculate)

    def show_loan_payment(self):
        def calculate(values):
            principal = float(values["principal"])
            annual_rate = float(values["rate"]) / 100
            months = int(float(values["months"]))
            monthly_rate = annual_rate / 12
            payment = principal / months if monthly_rate == 0 else principal * monthly_rate / (1 - (1 + monthly_rate) ** -months)
            return f"Monthly payment: ${payment:.2f}\nTotal paid: ${payment * months:.2f}\nInterest: ${payment * months - principal:.2f}"

        self.show_form_tool("Loan Payment", [("principal", "Loan amount"), ("rate", "Annual interest percent"), ("months", "Months")], calculate)

    def show_mortgage_estimate(self):
        def calculate(values):
            price = float(values["price"])
            down = float(values["down"])
            rate = float(values["rate"]) / 100 / 12
            months = int(float(values["years"])) * 12
            tax = float(values["tax"] or "0") / 12
            principal = price - down
            payment = principal / months if rate == 0 else principal * rate / (1 - (1 + rate) ** -months)
            return f"Estimated monthly: ${payment + tax:.2f}\nPrincipal and interest: ${payment:.2f}\nLoan amount: ${principal:.2f}"

        self.show_form_tool("Mortgage Estimate", [("price", "Home price"), ("down", "Down payment"), ("rate", "Annual interest percent"), ("years", "Years"), ("tax", "Monthly tax/insurance, optional")], calculate)

    def show_compound_interest(self):
        def calculate(values):
            principal = float(values["principal"])
            rate = float(values["rate"]) / 100
            years = float(values["years"])
            compounds = int(float(values["compounds"] or "12"))
            amount = principal * (1 + rate / compounds) ** (compounds * years)
            return f"Final balance: ${amount:.2f}\nGrowth: ${amount - principal:.2f}"

        self.show_form_tool("Compound Interest", [("principal", "Starting amount"), ("rate", "Annual return percent"), ("years", "Years"), ("compounds", "Compounds per year")], calculate)

    def show_tax_helper(self):
        def calculate(values):
            amount = float(values["amount"])
            rate = float(values["rate"]) / 100
            return f"Tax: ${amount * rate:.2f}\nTotal with tax: ${amount * (1 + rate):.2f}\nAfter removing tax: ${amount / (1 + rate):.2f}"

        self.show_form_tool("Tax Helper", [("amount", "Amount"), ("rate", "Tax percent")], calculate)

    def show_unit_converter(self):
        def calculate(values):
            value = float(values["value"])
            unit_from = values["from"].strip().lower()
            unit_to = values["to"].strip().lower()
            factors = {"m": 1, "meter": 1, "km": 1000, "cm": 0.01, "mm": 0.001, "mi": 1609.344, "mile": 1609.344, "ft": 0.3048, "in": 0.0254, "kg": 1, "g": 0.001, "lb": 0.45359237, "oz": 0.0283495}
            if unit_from not in factors or unit_to not in factors:
                return "Supported: m, km, cm, mm, mi, ft, in, kg, g, lb, oz."
            return f"{value:g} {unit_from} = {value * factors[unit_from] / factors[unit_to]:.8g} {unit_to}"

        self.show_form_tool("Unit Converter", [("value", "Value"), ("from", "From unit"), ("to", "To unit")], calculate)

    def show_temperature_converter(self):
        def calculate(values):
            value = float(values["value"])
            unit = values["unit"].strip().lower()
            if unit in ("c", "celsius"):
                c = value
            elif unit in ("f", "fahrenheit"):
                c = (value - 32) * 5 / 9
            elif unit in ("k", "kelvin"):
                c = value - 273.15
            else:
                return "Use C, F, or K."
            return f"{c:.4g} C\n{c * 9 / 5 + 32:.4g} F\n{c + 273.15:.4g} K"

        self.show_form_tool("Temperature Converter", [("value", "Temperature"), ("unit", "Unit: C, F, or K")], calculate)

    def show_cooking_converter(self):
        def calculate(values):
            value = float(values["value"])
            unit_from = values["from"].strip().lower()
            unit_to = values["to"].strip().lower()
            cups = {"cup": 1, "cups": 1, "tbsp": 1 / 16, "tablespoon": 1 / 16, "tsp": 1 / 48, "teaspoon": 1 / 48, "ml": 1 / 236.588, "l": 1000 / 236.588}
            if unit_from not in cups or unit_to not in cups:
                return "Supported: cup, tbsp, tsp, ml, l."
            return f"{value:g} {unit_from} = {value * cups[unit_from] / cups[unit_to]:.8g} {unit_to}"

        self.show_form_tool("Cooking Measurements", [("value", "Value"), ("from", "From: cup, tbsp, tsp, ml, l"), ("to", "To unit")], calculate)

    def show_currency_helper(self):
        def calculate(values):
            amount = float(values["amount"])
            rate = float(values["rate"])
            return f"Converted amount: {amount * rate:.2f}\nReverse rate result: {amount / rate:.2f}"

        self.show_form_tool("Currency Helper", [("amount", "Amount"), ("rate", "Exchange rate")], calculate)

    def show_physics_solver(self):
        def calculate(values):
            mass = float(values["mass"] or "0")
            acceleration = float(values["acceleration"] or "0")
            velocity = float(values["velocity"] or "0")
            return f"Force: {mass * acceleration:.6g} N\nKinetic energy: {0.5 * mass * velocity * velocity:.6g} J"

        self.show_form_tool("Physics Formula Solver", [("mass", "Mass in kg"), ("acceleration", "Acceleration in m/s^2"), ("velocity", "Velocity in m/s")], calculate)

    def show_molar_mass(self):
        def calculate(values):
            return f"Molar mass: {molar_mass(values['formula']):.6g} g/mol"

        self.show_form_tool("Molar Mass", [("formula", "Chemical formula, example: H2O or CO2")], calculate)

    def show_ohms_law(self):
        def calculate(values):
            voltage = optional_float(values["voltage"])
            current = optional_float(values["current"])
            resistance = optional_float(values["resistance"])
            if voltage is None and current is not None and resistance is not None:
                return f"Voltage: {current * resistance:.6g} V"
            if current is None and voltage is not None and resistance is not None:
                return f"Current: {voltage / resistance:.6g} A"
            if resistance is None and voltage is not None and current is not None:
                return f"Resistance: {voltage / current:.6g} ohms"
            return "Fill any two values and leave the third blank."

        self.show_form_tool("Ohm's Law", [("voltage", "Voltage V"), ("current", "Current A"), ("resistance", "Resistance ohms")], calculate)

    def show_density_calculator(self):
        def calculate(values):
            mass = float(values["mass"])
            volume = float(values["volume"])
            return f"Density: {mass / volume:.6g}"

        self.show_form_tool("Density Calculator", [("mass", "Mass"), ("volume", "Volume")], calculate)

    def show_mean_median_mode(self):
        def calculate(values):
            nums = parse_number_list(values["numbers"])
            counts = {number: nums.count(number) for number in nums}
            modes = [number for number, count in counts.items() if count == max(counts.values())]
            nums_sorted = sorted(nums)
            mid = len(nums_sorted) // 2
            median = nums_sorted[mid] if len(nums_sorted) % 2 else (nums_sorted[mid - 1] + nums_sorted[mid]) / 2
            return f"Mean: {sum(nums) / len(nums):.6g}\nMedian: {median:.6g}\nMode: {', '.join(f'{m:g}' for m in modes)}"

        self.show_form_tool("Mean Median Mode", [("numbers", "Numbers separated by commas")], calculate)

    def show_standard_deviation(self):
        def calculate(values):
            nums = parse_number_list(values["numbers"])
            mean = sum(nums) / len(nums)
            variance = sum((number - mean) ** 2 for number in nums) / len(nums)
            return f"Mean: {mean:.6g}\nVariance: {variance:.6g}\nStandard deviation: {math.sqrt(variance):.6g}"

        self.show_form_tool("Standard Deviation", [("numbers", "Numbers separated by commas")], calculate)

    def show_bmi_calculator(self):
        def calculate(values):
            weight = float(values["weight"])
            height = float(values["height"])
            bmi = 703 * weight / (height * height)
            return f"BMI: {bmi:.1f}"

        self.show_form_tool("BMI Calculator", [("weight", "Weight in pounds"), ("height", "Height in inches")], calculate)

    def show_time_difference(self):
        def calculate(values):
            start = time_to_minutes(values["start"])
            end = time_to_minutes(values["end"])
            if end < start:
                end += 24 * 60
            diff = end - start
            return f"Difference: {diff // 60} hours {diff % 60} minutes"

        self.show_form_tool("Time Difference", [("start", "Start time, example: 9:30"), ("end", "End time, example: 17:45")], calculate)


APP_STYLE = """
QWidget#content {
    background: transparent;
}
QLabel#title {
    color: #f8fbff;
    font: 700 28px "Segoe UI";
}
QLabel#subtitle {
    color: #aebbd0;
    font: 14px "Segoe UI";
}
QLabel#loadingSymbol {
    color: #e8f1fb;
    font: 700 58px "Segoe UI";
    padding: 10px;
}
QLabel#sectionTitle {
    color: #d9e8f8;
    font: 700 15px "Segoe UI";
    padding: 8px 2px 0 2px;
}
QLabel#hintLabel {
    color: #91a6bd;
    font: 13px "Segoe UI";
    padding: 8px 2px;
}
QLabel#plannedItem {
    color: #b9cce0;
    background-color: rgba(8, 12, 20, 115);
    border: 1px solid rgba(84, 124, 180, 48);
    border-radius: 6px;
    padding: 10px 12px;
    font: 14px "Segoe UI";
}
QFrame#panel {
    background-color: rgba(15, 20, 32, 224);
    border: 1px solid rgba(86, 126, 185, 90);
    border-radius: 8px;
}
QFrame#symbolPad {
    background-color: rgba(8, 12, 20, 120);
    border: 1px solid rgba(84, 124, 180, 58);
    border-radius: 8px;
}
QLineEdit {
    color: #f8fbff;
    background-color: rgba(8, 12, 20, 230);
    border: 1px solid rgba(84, 124, 180, 105);
    border-radius: 6px;
    padding: 8px 10px;
    font: 15px "Segoe UI";
}
QLineEdit:focus {
    border: 1px solid rgba(93, 157, 225, 185);
}
QPushButton {
    color: #eef6ff;
    background-color: rgba(25, 34, 50, 230);
    border: 1px solid rgba(82, 117, 168, 92);
    border-radius: 6px;
    padding: 9px 12px;
    font: 600 14px "Segoe UI";
}
QPushButton:hover {
    background-color: rgba(37, 57, 84, 238);
    border: 1px solid rgba(105, 151, 213, 135);
}
QPushButton:pressed {
    background-color: rgba(18, 45, 74, 245);
}
QPushButton#accentButton {
    background-color: rgba(35, 96, 165, 235);
    border: 1px solid rgba(100, 157, 222, 130);
}
QPushButton#accentButton:hover {
    background-color: rgba(45, 112, 190, 242);
}
QPushButton#symbolButton {
    background-color: rgba(20, 31, 48, 225);
    border: 1px solid rgba(88, 128, 184, 85);
    padding: 7px 8px;
    font: 600 15px "Segoe UI";
}
QPushButton#symbolButton:hover {
    background-color: rgba(32, 52, 78, 238);
}
QPushButton#startButton {
    min-height: 52px;
    font: 700 16px "Segoe UI";
}
QPushButton#secondaryButton {
    background-color: rgba(18, 24, 36, 225);
}
QLabel#result {
    color: #f4f8ff;
    background-color: rgba(8, 12, 20, 185);
    border: 1px solid rgba(84, 124, 180, 72);
    border-radius: 6px;
    padding: 10px;
    font: 14px "Consolas";
}
QScrollArea#menuScroll {
    border: none;
    background: transparent;
}
QScrollArea#menuScroll > QWidget > QWidget {
    background: transparent;
}
QScrollBar:vertical {
    background: rgba(255, 255, 255, 18);
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(85, 132, 190, 135);
    border-radius: 5px;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}
"""


ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

ALLOWED_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "log": math.log,
    "log10": math.log10,
    "ln": math.log,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
}

ALLOWED_NAMES = {"pi": math.pi, "e": math.e, "tau": math.tau}


def normalize_display_expression(text):
    replacements = [
        (r"\bsqrt\b", "√"),
        (r"\bpi\b", "π"),
        (r"\btau\b", "τ"),
    ]
    normalized = text.replace("*", "×").replace("/", "÷")
    for pattern, replacement in replacements:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    return normalized


def display_to_python_expression(text):
    expression = normalize_display_expression(text)
    expression = expression.replace("×", "*")
    expression = expression.replace("÷", "/")
    expression = expression.replace("π", "pi")
    expression = expression.replace("τ", "tau")
    expression = expression.replace("√", "sqrt")
    expression = expression.replace("^", "**")
    expression = add_implicit_multiplication(expression)
    return expression


def add_implicit_multiplication(expression):
    functions = "log10|sqrt|asin|acos|atan|sin|cos|tan|log|ln|exp"
    names = "pi|tau|e|x"
    expression = re.sub(rf"((?<![A-Za-z])\d|\)|{names})\s*(\()", r"\1*\2", expression)
    expression = re.sub(rf"(\))\s*(\d|{names}|{functions})", r"\1*\2", expression)
    expression = re.sub(rf"(\d|\)|{names})\s*({functions})", r"\1*\2", expression)
    expression = re.sub(rf"(\d|\))\s*({names})", r"\1*\2", expression)
    return expression


def safe_calculate(text, scientific=False):
    try:
        value = calculate_value(text, scientific=scientific)
        return f"{value:.12g}" if isinstance(value, float) else str(value)
    except Exception:
        return "Could not calculate that expression."


def calculate_value(text, scientific=False, variables=None):
    expression = display_to_python_expression(text.strip())
    if not expression:
        raise ValueError("Empty expression")
    tree = ast.parse(expression, mode="eval")
    allowed_functions = ALLOWED_FUNCTIONS if scientific else {}
    return evaluate_node(tree.body, allowed_functions, variables or {})


def evaluate_node(node, allowed_functions, variables=None):
    variables = variables or {}
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](
            evaluate_node(node.left, allowed_functions, variables),
            evaluate_node(node.right, allowed_functions, variables),
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](evaluate_node(node.operand, allowed_functions, variables))
    if isinstance(node, ast.Name) and node.id in variables:
        return variables[node.id]
    if isinstance(node, ast.Name) and node.id in ALLOWED_NAMES and allowed_functions:
        return ALLOWED_NAMES[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in allowed_functions:
        args = [evaluate_node(arg, allowed_functions, variables) for arg in node.args]
        return allowed_functions[node.func.id](*args)
    raise ValueError("Unsupported expression")


def is_prime(value):
    if value < 2:
        return False
    if value == 2:
        return True
    if value % 2 == 0:
        return False
    for divisor in range(3, int(math.sqrt(value)) + 1, 2):
        if value % divisor == 0:
            return False
    return True


def optional_float(text):
    text = text.strip()
    return None if not text else float(text)


def parse_number_list(text):
    numbers = [float(part.strip()) for part in re.split(r"[,\s]+", text) if part.strip()]
    if not numbers:
        raise ValueError("No numbers")
    return numbers


def time_to_minutes(text):
    parts = text.strip().split(":")
    if len(parts) != 2:
        raise ValueError("Use HH:MM")
    return int(parts[0]) * 60 + int(parts[1])


ATOMIC_MASSES = {
    "H": 1.008,
    "He": 4.0026,
    "C": 12.011,
    "N": 14.007,
    "O": 15.999,
    "Na": 22.99,
    "Mg": 24.305,
    "Al": 26.982,
    "Si": 28.085,
    "P": 30.974,
    "S": 32.06,
    "Cl": 35.45,
    "K": 39.098,
    "Ca": 40.078,
    "Fe": 55.845,
    "Cu": 63.546,
    "Zn": 65.38,
    "Ag": 107.8682,
    "I": 126.904,
    "Au": 196.9666,
    "Pb": 207.2,
}


def molar_mass(formula):
    total = 0
    tokens = re.findall(r"([A-Z][a-z]?)(\d*)", formula.strip())
    if not tokens:
        raise ValueError("Bad formula")
    for element, count_text in tokens:
        if element not in ATOMIC_MASSES:
            raise ValueError("Unknown element")
        total += ATOMIC_MASSES[element] * int(count_text or "1")
    return total


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MathHub()
    window.show()
    sys.exit(app.exec_())
