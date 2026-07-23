"""Polish dialog for calculating one selected parcel."""

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Optional, Tuple

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext,
    QgsFeature,
    QgsVectorLayer,
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

if "." in __package__:
    from ..adapters import (
        GeometryInputError,
        GeometryPreparationResult,
        GeometryRepairError,
        GeometryTransformError,
        RepairMethod,
        RepairMode,
        ZoneSelectionError,
        prepare_geometry,
    )
    from ..core import (
        AreaCalculationError,
        AreaCalculationResult,
        calculate_area,
    )
else:
    from adapters import (
        GeometryInputError,
        GeometryPreparationResult,
        GeometryRepairError,
        GeometryTransformError,
        RepairMethod,
        RepairMode,
        ZoneSelectionError,
        prepare_geometry,
    )
    from core import (
        AreaCalculationError,
        AreaCalculationResult,
        calculate_area,
    )


_PL2000_ZONE_BY_EPSG = {2176: 5, 2177: 6, 2178: 7, 2179: 8}

_WARNING_LABELS = {
    "duplicate_boundary_points_removed": (
        "Usunięto powtarzające się współrzędne punktów przy "
        "wyznaczaniu P_GK."
    ),
    "geometry_invalid_before_repair": (
        "Geometria była niepoprawna według GEOS."
    ),
    "multipart_geometry": "Geometria zawiera więcej niż jedną część.",
    "interior_rings_included": (
        "Pierścienie wewnętrzne uwzględniono jako granice przy wyznaczaniu "
        "P_GK."
    ),
    "geometry_repaired": (
        "Obliczenia wykorzystują naprawioną kopię geometrii."
    ),
    "repair_changed_boundary_vertices": (
        "Naprawa zmieniła zbiór wierzchołków granicy."
    ),
    "repair_changed_part_count": (
        "Naprawa zmieniła liczbę części geometrii."
    ),
    "repair_changed_ring_count": "Naprawa zmieniła liczbę pierścieni.",
    "repair_changed_area": "Naprawa zmieniła pole powierzchni geometrii.",
    "structure_not_supported": "Metoda Structure nie jest obsługiwana.",
    "structure_failed": "Metoda Structure nie naprawiła geometrii.",
    "linework_not_supported": "Metoda Linework nie jest obsługiwana.",
    "linework_failed": "Metoda Linework nie naprawiła geometrii.",
    "strict_mode_blocks_statutory_result": (
        "Zgodnie z wybraną opcją nie wyznaczono wyniku po naprawie "
        "geometrii."
    ),
}

_REPAIR_METHOD_LABELS = {
    RepairMethod.NONE: "nie była potrzebna",
    RepairMethod.STRUCTURE: "Structure",
    RepairMethod.LINEWORK: "Linework",
    RepairMethod.FAILED: "nieudana",
}

_REPAIR_OPTION_NO_RESULT = "Wykryj błędy, ale nie licz po naprawie geometrii"
_REPAIR_OPTION_AUTO = "Wykryj błędy i spróbuj naprawić geometrię"
_REPAIR_HINT_NO_RESULT = (
    "Jeżeli geometria będzie wymagała naprawy, wynik powierzchni nie "
    "zostanie wyznaczony."
)
_REPAIR_HINT_AUTO = (
    "Uwaga: naprawa może zmienić geometrię poligonu używaną do "
    "obliczenia. Warstwa źródłowa pozostanie bez zmian."
)


@dataclass(frozen=True)
class SelectedParcelResult:
    """Calculation and geometry diagnostics presented by the dialog."""

    preparation: GeometryPreparationResult
    calculation: Optional[AreaCalculationResult]

    @property
    def warnings(self) -> Tuple[str, ...]:
        calculation_warnings = (
            self.calculation.warnings if self.calculation is not None else ()
        )
        return self.preparation.report.warnings + calculation_warnings


def calculate_selected_parcel(
    feature: QgsFeature,
    source_crs: QgsCoordinateReferenceSystem,
    transform_context: QgsCoordinateTransformContext,
    *,
    selected_zone: Optional[int],
    repair_mode: RepairMode,
) -> SelectedParcelResult:
    """Calculate one feature without mutating its source layer."""

    preparation = prepare_geometry(
        feature.geometry(),
        source_crs,
        transform_context,
        selected_zone=selected_zone,
        repair_mode=repair_mode,
    )
    calculation = None
    if preparation.statutory_result_allowed:
        calculation = calculate_area(
            po_m2=preparation.geometry_for_area.area(),
            boundary_points=preparation.original_boundary_points,
            epsg=preparation.target_epsg,
        )
    return SelectedParcelResult(
        preparation=preparation,
        calculation=calculation,
    )


class SelectedParcelDialog(QDialog):
    """Dialog showing a statutory calculation for one selected polygon."""

    def __init__(
        self,
        layer: QgsVectorLayer,
        feature: QgsFeature,
        transform_context: QgsCoordinateTransformContext,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._layer = layer
        self._feature = QgsFeature(feature)
        self._transform_context = transform_context
        self.last_result: Optional[SelectedParcelResult] = None

        self.setObjectName("selectedParcelDialog")
        self.setWindowTitle("Poprawka odwzorowawcza — zaznaczona działka")
        icon_path = (
            Path(__file__).resolve().parents[1] / "resources" / "icon.svg"
        )
        self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(720, 620)
        self.resize(820, 720)
        self._colors = _theme_colors(self)
        self._build_ui()
        self.setStyleSheet(_dialog_stylesheet(self._colors))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        icon_label = QLabel()
        icon_label.setObjectName("dialogIcon")
        icon_label.setPixmap(self.windowIcon().pixmap(42, 42))
        icon_label.setFixedSize(46, 46)
        header_layout.addWidget(icon_label)

        heading_layout = QVBoxLayout()
        heading_layout.setSpacing(1)
        title_label = QLabel("Korekta pola powierzchni działki")
        title_label.setObjectName("dialogTitle")
        subtitle_label = QLabel(
            "Obliczenie według wzorów dla układu współrzędnych PL-2000"
        )
        subtitle_label.setObjectName("dialogSubtitle")
        subtitle_label.setWordWrap(True)
        heading_layout.addWidget(title_label)
        heading_layout.addWidget(subtitle_label)
        header_layout.addLayout(heading_layout, 1)
        layout.addLayout(header_layout)

        selection_card = QFrame()
        selection_card.setObjectName("selectionCard")
        selection_layout = QHBoxLayout(selection_card)
        selection_layout.setContentsMargins(14, 10, 14, 10)
        selection_layout.setSpacing(12)

        layer_layout = QVBoxLayout()
        layer_layout.setSpacing(1)
        layer_caption = QLabel("WYBRANY OBIEKT")
        layer_caption.setObjectName("eyebrowLabel")
        layer_name = QLabel(self._layer.name())
        layer_name.setObjectName("selectionPrimary")
        layer_name.setWordWrap(True)
        layer_layout.addWidget(layer_caption)
        layer_layout.addWidget(layer_name)
        selection_layout.addLayout(layer_layout, 1)

        selection_meta = QLabel(
            f"ID: {self._feature.id()}\n"
            f"CRS: {self._layer.crs().authid() or 'brak identyfikatora'}"
        )
        selection_meta.setObjectName("selectionMeta")
        selection_meta.setWordWrap(True)
        selection_layout.addWidget(selection_meta)
        layout.addWidget(selection_card)

        settings_group = QGroupBox("Ustawienia obliczenia")
        settings_group.setObjectName("settingsGroup")
        settings_layout = QFormLayout(settings_group)
        settings_layout.setContentsMargins(16, 20, 16, 14)
        settings_layout.setHorizontalSpacing(18)
        settings_layout.setVerticalSpacing(10)

        self.zone_combo = QComboBox()
        self.zone_combo.setObjectName("zoneCombo")
        self._populate_zone_combo()
        settings_layout.addRow("Strefa układu PL-2000", self.zone_combo)

        self.repair_mode_combo = QComboBox()
        self.repair_mode_combo.setObjectName("repairModeCombo")
        self.repair_mode_combo.addItem(
            _REPAIR_OPTION_NO_RESULT,
            RepairMode.STRICT.value,
        )
        self.repair_mode_combo.addItem(
            _REPAIR_OPTION_AUTO,
            RepairMode.AUTO_REPAIR.value,
        )
        self.repair_mode_combo.setToolTip(
            f"{_REPAIR_OPTION_NO_RESULT}. {_REPAIR_HINT_NO_RESULT}\n\n"
            f"{_REPAIR_OPTION_AUTO}. {_REPAIR_HINT_AUTO}"
        )
        settings_layout.addRow("Obsługa geometrii", self.repair_mode_combo)

        self.repair_hint = QLabel()
        self.repair_hint.setObjectName("repairHint")
        self.repair_hint.setWordWrap(True)
        settings_layout.addRow("", self.repair_hint)
        layout.addWidget(settings_group)

        status_card = QFrame()
        status_card.setObjectName("statusCard")
        status_card.setProperty("state", "ready")
        status_layout = QHBoxLayout(status_card)
        status_layout.setContentsMargins(14, 9, 14, 9)
        status_layout.setSpacing(10)
        self.status_indicator = QLabel("●")
        self.status_indicator.setObjectName("statusIndicator")
        status_layout.addWidget(self.status_indicator)
        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label, 1)
        layout.addWidget(status_card)
        self.status_card = status_card

        self.result_text = QTextBrowser()
        self.result_text.setObjectName("resultText")
        self.result_text.setReadOnly(True)
        self.result_text.setOpenExternalLinks(False)
        self.result_text.setHtml(_empty_result_html(self._colors))
        layout.addWidget(self.result_text, 1)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch(1)
        self.close_button = QPushButton("Zamknij")
        self.close_button.setObjectName("closeButton")
        self.close_button.setProperty("role", "secondary")
        self.calculate_button = QPushButton("Oblicz powierzchnię")
        self.calculate_button.setObjectName("calculateButton")
        self.calculate_button.setProperty("role", "primary")
        self.calculate_button.setDefault(True)
        button_layout.addWidget(self.close_button)
        button_layout.addWidget(self.calculate_button)
        layout.addLayout(button_layout)

        self.repair_mode_combo.currentIndexChanged.connect(
            self._update_repair_hint
        )
        self.calculate_button.clicked.connect(self.calculate)
        self.close_button.clicked.connect(self.reject)
        self._update_repair_hint()
        self._set_status("Gotowy do obliczenia.", "ready")

    def _update_repair_hint(self) -> None:
        repair_mode = RepairMode(self.repair_mode_combo.currentData())
        hint = (
            _REPAIR_HINT_AUTO
            if repair_mode is RepairMode.AUTO_REPAIR
            else _REPAIR_HINT_NO_RESULT
        )
        self.repair_hint.setText(hint)

    def _set_status(self, message: str, state: str) -> None:
        self.status_label.setText(message)
        self.status_card.setProperty("state", state)
        self.status_card.style().unpolish(self.status_card)
        self.status_card.style().polish(self.status_card)
        self.status_card.update()

    def _populate_zone_combo(self) -> None:
        source_zone = _zone_from_crs(self._layer.crs())
        if source_zone is not None:
            source_epsg = 2171 + source_zone
            self.zone_combo.addItem(
                f"Z CRS warstwy — strefa {source_zone} (EPSG:{source_epsg})",
                None,
            )
            self.zone_combo.setEnabled(False)
            return

        self.zone_combo.addItem("Wybierz i potwierdź strefę…", None)
        for zone in (5, 6, 7, 8):
            self.zone_combo.addItem(
                f"Strefa {zone} — EPSG:{2171 + zone}",
                zone,
            )

    def calculate(self) -> None:
        """Calculate and render the feature without editing its layer."""

        selected_zone = self.zone_combo.currentData()
        if self.zone_combo.isEnabled() and selected_zone is None:
            self._show_error(
                "Wybierz strefę PL-2000 i potwierdź ją przed obliczeniem."
            )
            return

        repair_mode = RepairMode(self.repair_mode_combo.currentData())
        try:
            result = calculate_selected_parcel(
                self._feature,
                self._layer.crs(),
                self._transform_context,
                selected_zone=selected_zone,
                repair_mode=repair_mode,
            )
        except (
            AreaCalculationError,
            GeometryInputError,
            GeometryRepairError,
            GeometryTransformError,
            ZoneSelectionError,
        ) as error:
            self._show_error(
                f"Nie można obliczyć powierzchni.\n\nSzczegóły: {error}"
            )
            return

        self.last_result = result
        self.result_text.setHtml(_format_result_html(result, self._colors))
        if result.calculation is None:
            self._set_status(
                "Wykryto błędy geometrii. Zgodnie z wybraną opcją nie "
                "wyznaczono wyniku po naprawie.",
                "warning",
            )
        elif result.preparation.report.repair_method is RepairMethod.NONE:
            self._set_status("Obliczenie zakończone poprawnie.", "success")
        else:
            self._set_status(
                "Obliczenie zakończone na naprawionej kopii geometrii.",
                "warning",
            )

    def _show_error(self, message: str) -> None:
        self.last_result = None
        self._set_status("Obliczenie nie zostało wykonane.", "error")
        QMessageBox.warning(self, "Poprawka odwzorowawcza", message)


def _zone_from_crs(crs: QgsCoordinateReferenceSystem) -> Optional[int]:
    authid = crs.authid().upper()
    if not authid.startswith("EPSG:"):
        return None
    try:
        epsg = int(authid.removeprefix("EPSG:"))
    except ValueError:
        return None
    return _PL2000_ZONE_BY_EPSG.get(epsg)


def _format_result_html(
    result: SelectedParcelResult,
    colors: dict,
) -> str:
    preparation = result.preparation
    report = preparation.report
    calculation = result.calculation

    if calculation is None:
        result_content = (
            '<div class="empty-state">'
            '<div class="empty-title">Nie wyznaczono wyniku</div>'
            "<div>Geometria wymagała naprawy, a wybrana opcja nie "
            "dopuszcza obliczenia na naprawionej kopii.</div>"
            "</div>"
        )
    else:
        result_rows = (
            _result_row(
                "P₀",
                "Pole powierzchni działki obliczone na podstawie "
                "współrzędnych prostokątnych płaskich w układzie "
                "PL-2000",
                f"{_format_number(calculation.po_m2, 2)} m²",
            ),
            _result_row(
                "ΔP₀",
                "Powierzchniowa poprawka odwzorowawcza",
                f"{_format_number(calculation.correction_m2, 2)} m²",
            ),
            _result_row(
                "P = P₀ − ΔP₀",
                "Pole powierzchni obiektu ewidencyjnego, jako fragmentu "
                "powierzchni elipsoidy GRS 80",
                f"{_format_number(calculation.legal_area_m2_raw, 2)} m²",
                prominent=True,
            ),
            _result_row(
                "P",
                "Pole powierzchni obiektu ewidencyjnego w hektarach",
                f"{_format_decimal(calculation.legal_area_ha_rounded)} ha",
                prominent=True,
            ),
        )
        result_content = (
            '<table class="result-table" cellspacing="0" cellpadding="0">'
            f"{''.join(result_rows)}"
            "</table>"
        )

    parameter_content = ""
    if calculation is not None:
        parameter_rows = (
            _parameter_row(
                "P<sub>GK</sub> — X₂₀₀₀",
                _format_number(calculation.pgk_x_northing, 3),
                "m",
            ),
            _parameter_row(
                "P<sub>GK</sub> — Y₂₀₀₀",
                _format_number(calculation.pgk_y_easting, 3),
                "m",
            ),
            _parameter_row(
                "X<sub>GK</sub>",
                _format_number(calculation.x_gk_northing, 3),
                "m",
            ),
            _parameter_row(
                "Y<sub>GK</sub>",
                _format_number(calculation.y_gk_easting, 3),
                "m",
            ),
            _parameter_row("u", _format_number(calculation.u, 8)),
            _parameter_row("v", _format_number(calculation.v, 8)),
            _parameter_row(
                "σ",
                _format_number(calculation.sigma_cm_per_km, 8),
                "cm/km",
            ),
            _parameter_row(
                "m",
                _format_number(calculation.scale_m, 10),
            ),
            _parameter_row(
                "m²",
                _format_number(calculation.scale_m**2, 10),
            ),
        )
        parameter_content = (
            '<div class="section-title">PARAMETRY WZORU</div>'
            '<div class="formula">'
            "ΔP₀ = P₀ · (m² − 1)"
            '<span class="formula-separator"> • </span>'
            "m = σ · 10⁻⁵ + 1"
            "<br>"
            "σ = σ₀ + m₀ · v² · "
            "(q₁ + q₂ · u + q₃ · u² + q₄ · v²)"
            "</div>"
            '<div class="parameter-intro">'
            "P<sub>GK</sub> — punkt określający przybliżony środek "
            "ciężkości działki ewidencyjnej, obliczony jako średnia "
            "arytmetyczna współrzędnych punktów granicznych działki "
            "ewidencyjnej."
            "</div>"
            '<table class="parameter-table" cellspacing="0" cellpadding="0">'
            f"{''.join(parameter_rows)}"
            "</table>"
        )

    geometry_rows = (
        _diagnostic_row(
            "Strefa układu PL-2000",
            f"{preparation.zone} (EPSG:{preparation.target_epsg})",
        ),
        _diagnostic_row(
            "Poprawność GEOS przed naprawą",
            _yes_no(report.validity_before),
        ),
        _diagnostic_row(
            "Poprawność GEOS po naprawie",
            _yes_no(report.validity_after),
        ),
        _diagnostic_row(
            "Metoda naprawy",
            _REPAIR_METHOD_LABELS[report.repair_method],
        ),
        _diagnostic_row(
            "Części geometrii",
            f"{report.original_part_count} → {report.repaired_part_count}",
        ),
        _diagnostic_row(
            "Pierścienie",
            f"{report.original_ring_count} → {report.repaired_ring_count}",
        ),
        _diagnostic_row(
            "Wierzchołki",
            f"{report.original_vertex_count} → "
            f"{report.repaired_vertex_count}",
        ),
        _diagnostic_row(
            "Wierzchołki dodane / usunięte",
            f"{report.vertices_added} / {report.vertices_removed}",
        ),
        _diagnostic_row(
            "Pole geometrii przed / po",
            f"{_format_number(report.original_area_m2, 2)} / "
            f"{_format_number(report.repaired_area_m2, 2)} m²",
        ),
        _diagnostic_row(
            "Różnica pola po naprawie",
            f"{_format_number(report.area_difference_m2, 2)} m²",
        ),
    )
    geometry_content = (
        '<div class="section-title">STREFA I GEOMETRIA</div>'
        '<table class="diagnostic-table" cellspacing="0" cellpadding="0">'
        f"{''.join(geometry_rows)}"
        "</table>"
    )

    warnings = tuple(_warning_label(warning) for warning in result.warnings)
    if warnings:
        warning_items = "".join(
            f"<li>{escape(warning)}</li>" for warning in warnings
        )
        warning_content = (
            '<div class="section-title warning-heading">UWAGI</div>'
            f'<ul class="warnings">{warning_items}</ul>'
        )
    else:
        warning_content = (
            '<div class="section-title">UWAGI</div>'
            '<div class="no-warnings">Brak uwag do obliczenia.</div>'
        )

    body = (
        '<div class="section-title first">WYNIK OBLICZENIA</div>'
        f"{result_content}"
        f"{parameter_content}"
        f"{geometry_content}"
        f"{warning_content}"
    )
    return _html_document(body, colors)


def _result_row(
    symbol: str,
    description: str,
    value: str,
    *,
    prominent: bool = False,
) -> str:
    row_class = " prominent" if prominent else ""
    return (
        f'<tr class="result-row{row_class}">'
        f'<td class="result-symbol">{symbol}</td>'
        f'<td class="result-description">{escape(description)}</td>'
        f'<td class="result-value">{value}</td>'
        "</tr>"
    )


def _parameter_row(symbol: str, value: str, unit: str = "") -> str:
    formatted_unit = f" {escape(unit)}" if unit else ""
    return (
        "<tr>"
        f'<td class="parameter-symbol">{symbol}</td>'
        f'<td class="parameter-value">{value}{formatted_unit}</td>'
        "</tr>"
    )


def _diagnostic_row(label: str, value: str) -> str:
    return (
        "<tr>"
        f'<td class="diagnostic-label">{escape(label)}</td>'
        f'<td class="diagnostic-value">{escape(value)}</td>'
        "</tr>"
    )


def _empty_result_html(colors: dict) -> str:
    body = (
        '<div class="welcome">'
        '<div class="welcome-mark">P = P₀ − ΔP₀</div>'
        '<div class="welcome-title">Raport obliczenia pojawi się tutaj</div>'
        "<div>Sprawdź ustawienia i wybierz „Oblicz powierzchnię”.</div>"
        "</div>"
    )
    return _html_document(body, colors)


def _html_document(body: str, colors: dict) -> str:
    return f"""
    <html>
      <head>
        <style>
          body {{
            color: {colors["text"]};
            background-color: {colors["surface"]};
            font-family: "Segoe UI", "Noto Sans", "DejaVu Sans",
              "Helvetica Neue", Arial, sans-serif;
            font-size: 10pt;
            margin: 14px;
          }}
          .section-title {{
            color: {colors["muted"]};
            font-size: 8.5pt;
            font-weight: 700;
            margin-top: 22px;
            margin-bottom: 8px;
          }}
          .section-title.first {{
            margin-top: 0;
          }}
          table {{
            width: 100%;
            border-collapse: collapse;
          }}
          td {{
            border-bottom: 1px solid {colors["border"]};
            padding: 8px 7px;
            vertical-align: middle;
          }}
          .result-symbol {{
            color: {colors["accent"]};
            font-family: "Cambria Math", "STIX Two Math",
              "DejaVu Serif", serif;
            font-size: 12pt;
            font-weight: 700;
            white-space: nowrap;
            width: 25%;
          }}
          .result-description {{
            color: {colors["muted"]};
            font-size: 8.7pt;
            width: 48%;
          }}
          .result-value {{
            font-family: "Cascadia Mono", "SFMono-Regular",
              "DejaVu Sans Mono", "Liberation Mono", Consolas, monospace;
            font-size: 10.5pt;
            font-weight: 700;
            text-align: right;
            white-space: nowrap;
            width: 27%;
          }}
          .prominent td {{
            background-color: {colors["accent_soft"]};
          }}
          .formula {{
            color: {colors["accent"]};
            background-color: {colors["accent_soft"]};
            font-family: "Cambria Math", "STIX Two Math",
              "DejaVu Serif", serif;
            font-size: 10.5pt;
            padding: 10px 12px;
          }}
          .formula-separator {{
            color: {colors["muted"]};
            padding-left: 12px;
            padding-right: 12px;
          }}
          .parameter-intro {{
            color: {colors["muted"]};
            font-size: 8.7pt;
            margin-top: 8px;
            margin-bottom: 4px;
          }}
          .parameter-table, .diagnostic-table {{
            margin-top: 5px;
          }}
          .parameter-symbol, .diagnostic-label {{
            color: {colors["muted"]};
            width: 62%;
          }}
          .parameter-symbol {{
            font-family: "Cambria Math", "STIX Two Math",
              "DejaVu Serif", serif;
            font-size: 10.5pt;
          }}
          .parameter-value, .diagnostic-value {{
            font-family: "Cascadia Mono", "SFMono-Regular",
              "DejaVu Sans Mono", "Liberation Mono", Consolas, monospace;
            text-align: right;
            white-space: nowrap;
          }}
          .warnings {{
            color: {colors["warning"]};
            margin-top: 4px;
            margin-bottom: 8px;
          }}
          .warning-heading {{
            color: {colors["warning"]};
          }}
          .no-warnings {{
            color: {colors["success"]};
            padding: 3px 0 8px 0;
          }}
          .empty-state {{
            color: {colors["warning"]};
            background-color: {colors["warning_soft"]};
            padding: 14px;
          }}
          .empty-title, .welcome-title {{
            color: {colors["text"]};
            font-size: 12pt;
            font-weight: 700;
            margin-bottom: 5px;
          }}
          .welcome {{
            color: {colors["muted"]};
            text-align: center;
            margin-top: 55px;
          }}
          .welcome-mark {{
            color: {colors["accent"]};
            font-family: "Cambria Math", "STIX Two Math",
              "DejaVu Serif", serif;
            font-size: 19pt;
            font-weight: 700;
            margin-bottom: 12px;
          }}
        </style>
      </head>
      <body>{body}</body>
    </html>
    """


def _warning_label(warning: str) -> str:
    warning_code, separator, details = warning.partition(": ")
    label = _WARNING_LABELS.get(warning_code, warning_code)
    if separator:
        return f"{label} Szczegóły: {details}"
    return label


def _format_number(value: float, decimal_places: int) -> str:
    return f"{value:.{decimal_places}f}".replace(".", ",")


def _format_decimal(value: object) -> str:
    return str(value).replace(".", ",")


def _yes_no(value: bool) -> str:
    return "tak" if value else "nie"


def _theme_colors(dialog: QDialog) -> dict:
    is_dark = dialog.palette().window().color().lightness() < 128
    if is_dark:
        return {
            "window": "#1d252c",
            "surface": "#252f38",
            "surface_alt": "#2d3943",
            "text": "#edf3f7",
            "muted": "#adbac5",
            "border": "#44515d",
            "accent": "#63b3d4",
            "accent_hover": "#7bc1de",
            "accent_soft": "#243f4c",
            "success": "#65c59b",
            "success_soft": "#243e35",
            "warning": "#efbd68",
            "warning_soft": "#453922",
            "error": "#ee817c",
            "error_soft": "#482d2e",
        }
    return {
        "window": "#f2f5f7",
        "surface": "#ffffff",
        "surface_alt": "#eaf0f3",
        "text": "#17242d",
        "muted": "#5e6d77",
        "border": "#d3dde3",
        "accent": "#176b8b",
        "accent_hover": "#0f5874",
        "accent_soft": "#e1f0f5",
        "success": "#247253",
        "success_soft": "#e1f1e9",
        "warning": "#946116",
        "warning_soft": "#fbefd8",
        "error": "#a43d3a",
        "error_soft": "#f8e5e4",
    }


def _dialog_stylesheet(colors: dict) -> str:
    return f"""
    QDialog#selectedParcelDialog {{
        background-color: {colors["window"]};
        color: {colors["text"]};
        font-family: "Segoe UI", "Noto Sans", "DejaVu Sans",
            "Helvetica Neue", Arial, sans-serif;
        font-size: 10pt;
    }}
    QLabel {{
        background: transparent;
        color: {colors["text"]};
    }}
    QLabel#dialogTitle {{
        font-size: 17pt;
        font-weight: 700;
    }}
    QLabel#dialogSubtitle, QLabel#selectionMeta, QLabel#repairHint {{
        color: {colors["muted"]};
    }}
    QLabel#dialogSubtitle {{
        font-size: 9.5pt;
    }}
    QLabel#eyebrowLabel {{
        color: {colors["accent"]};
        font-size: 8pt;
        font-weight: 700;
    }}
    QLabel#selectionPrimary {{
        font-size: 11pt;
        font-weight: 600;
    }}
    QLabel#selectionMeta {{
        font-family: "Cascadia Mono", "SFMono-Regular",
            "DejaVu Sans Mono", "Liberation Mono", Consolas, monospace;
        font-size: 8.5pt;
    }}
    QLabel#repairHint {{
        font-size: 8.5pt;
        padding-bottom: 2px;
    }}
    QFrame#selectionCard, QGroupBox#settingsGroup,
    QTextBrowser#resultText {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        border-radius: 9px;
    }}
    QGroupBox#settingsGroup {{
        color: {colors["text"]};
        font-weight: 600;
        margin-top: 10px;
        padding-top: 8px;
    }}
    QGroupBox#settingsGroup::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
    }}
    QComboBox {{
        color: {colors["text"]};
        background-color: {colors["surface_alt"]};
        border: 1px solid {colors["border"]};
        border-radius: 6px;
        min-height: 24px;
        padding: 6px 34px 6px 10px;
        selection-background-color: {colors["accent"]};
        selection-color: #ffffff;
    }}
    QComboBox:hover, QComboBox:focus {{
        border-color: {colors["accent"]};
    }}
    QComboBox:disabled {{
        color: {colors["muted"]};
        background-color: {colors["window"]};
    }}
    QComboBox::drop-down {{
        border: 0;
        width: 28px;
    }}
    QComboBox QAbstractItemView {{
        color: {colors["text"]};
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        selection-background-color: {colors["accent"]};
        selection-color: #ffffff;
        outline: 0;
        padding: 4px;
    }}
    QFrame#statusCard {{
        background-color: {colors["surface_alt"]};
        border: 1px solid {colors["border"]};
        border-radius: 7px;
    }}
    QFrame#statusCard[state="success"] {{
        background-color: {colors["success_soft"]};
        border-color: {colors["success"]};
    }}
    QFrame#statusCard[state="warning"] {{
        background-color: {colors["warning_soft"]};
        border-color: {colors["warning"]};
    }}
    QFrame#statusCard[state="error"] {{
        background-color: {colors["error_soft"]};
        border-color: {colors["error"]};
    }}
    QLabel#statusLabel {{
        font-weight: 600;
    }}
    QLabel#statusIndicator {{
        color: {colors["accent"]};
        font-size: 10pt;
    }}
    QFrame#statusCard[state="success"] QLabel#statusIndicator {{
        color: {colors["success"]};
    }}
    QFrame#statusCard[state="warning"] QLabel#statusIndicator {{
        color: {colors["warning"]};
    }}
    QFrame#statusCard[state="error"] QLabel#statusIndicator {{
        color: {colors["error"]};
    }}
    QTextBrowser#resultText {{
        padding: 3px;
        selection-background-color: {colors["accent"]};
        selection-color: #ffffff;
    }}
    QPushButton {{
        min-height: 24px;
        padding: 7px 18px;
        border-radius: 6px;
        font-weight: 600;
    }}
    QPushButton[role="primary"] {{
        color: #ffffff;
        background-color: {colors["accent"]};
        border: 1px solid {colors["accent"]};
    }}
    QPushButton[role="primary"]:hover {{
        background-color: {colors["accent_hover"]};
        border-color: {colors["accent_hover"]};
    }}
    QPushButton[role="primary"]:pressed {{
        background-color: {colors["accent_hover"]};
    }}
    QPushButton[role="secondary"] {{
        color: {colors["text"]};
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
    }}
    QPushButton[role="secondary"]:hover {{
        border-color: {colors["accent"]};
        color: {colors["accent"]};
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {colors["border"]};
        min-height: 30px;
        border-radius: 4px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    """
