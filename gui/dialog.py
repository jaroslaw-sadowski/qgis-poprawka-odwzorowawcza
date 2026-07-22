"""A small Polish dialog for calculating one selected parcel."""

from dataclasses import dataclass
from typing import Optional, Tuple

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext,
    QgsFeature,
    QgsVectorLayer,
)
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
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
        "Usunięto powtarzające się współrzędne punktów przy obliczaniu PGK."
    ),
    "geometry_invalid_before_repair": (
        "Geometria była niepoprawna według GEOS."
    ),
    "multipart_geometry": "Geometria zawiera więcej niż jedną część.",
    "interior_rings_included": (
        "Pierścienie wewnętrzne uwzględniono jako granice przy obliczaniu PGK."
    ),
    "geometry_repaired": "Obliczenia wykorzystują naprawioną kopię geometrii.",
    "repair_changed_boundary_vertices": (
        "Naprawa zmieniła zbiór wierzchołków granicy."
    ),
    "repair_changed_part_count": "Naprawa zmieniła liczbę części geometrii.",
    "repair_changed_ring_count": "Naprawa zmieniła liczbę pierścieni.",
    "repair_changed_area": "Naprawa zmieniła pole powierzchni geometrii.",
    "structure_not_supported": "Metoda Structure nie jest obsługiwana.",
    "structure_failed": "Metoda Structure nie naprawiła geometrii.",
    "linework_not_supported": "Metoda Linework nie jest obsługiwana.",
    "linework_failed": "Metoda Linework nie naprawiła geometrii.",
    "strict_mode_blocks_statutory_result": (
        "Tryb STRICT zablokował wynik ustawowy po naprawie."
    ),
}

_REPAIR_METHOD_LABELS = {
    RepairMethod.NONE: "nie była potrzebna",
    RepairMethod.STRUCTURE: "Structure",
    RepairMethod.LINEWORK: "Linework",
    RepairMethod.FAILED: "nieudana",
}


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

        self.setWindowTitle("Poprawka odwzorowawcza — zaznaczona działka")
        self.setMinimumSize(620, 520)
        self.resize(720, 580)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        selection_label = QLabel(
            f"Warstwa: {self._layer.name()}\n"
            f"Identyfikator obiektu: {self._feature.id()}"
        )
        selection_label.setWordWrap(True)
        layout.addWidget(selection_label)

        settings_group = QGroupBox("Ustawienia obliczenia")
        settings_layout = QFormLayout(settings_group)

        self.zone_combo = QComboBox()
        self.zone_combo.setObjectName("zoneCombo")
        self._populate_zone_combo()
        settings_layout.addRow("Strefa PL-2000:", self.zone_combo)

        self.repair_mode_combo = QComboBox()
        self.repair_mode_combo.setObjectName("repairModeCombo")
        self.repair_mode_combo.addItem(
            "STRICT — zatrzymaj wynik po istotnej naprawie",
            RepairMode.STRICT.value,
        )
        self.repair_mode_combo.addItem(
            "AUTO_REPAIR — oblicz po naprawie kopii",
            RepairMode.AUTO_REPAIR.value,
        )
        settings_layout.addRow("Tryb naprawy:", self.repair_mode_combo)
        layout.addWidget(settings_group)

        self.status_label = QLabel("Gotowy do obliczenia.")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(self.status_label)

        self.result_text = QPlainTextEdit()
        self.result_text.setObjectName("resultText")
        self.result_text.setReadOnly(True)
        self.result_text.setPlainText(
            "Wybierz ustawienia i kliknij „Oblicz powierzchnię”."
        )
        layout.addWidget(self.result_text, 1)

        button_layout = QHBoxLayout()
        self.calculate_button = QPushButton("Oblicz powierzchnię")
        self.calculate_button.setObjectName("calculateButton")
        self.close_button = QPushButton("Zamknij")
        self.close_button.setObjectName("closeButton")
        button_layout.addWidget(self.calculate_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.calculate_button.clicked.connect(self.calculate)
        self.close_button.clicked.connect(self.reject)

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
        self.result_text.setPlainText(_format_result(result))
        if result.calculation is None:
            self.status_label.setText(
                "Geometria wymagała naprawy. Tryb STRICT zablokował "
                "wynik ustawowy."
            )
        elif result.preparation.report.repair_method is RepairMethod.NONE:
            self.status_label.setText("Obliczenie zakończone poprawnie.")
        else:
            self.status_label.setText(
                "Obliczenie zakończone na naprawionej kopii geometrii."
            )

    def _show_error(self, message: str) -> None:
        self.last_result = None
        self.status_label.setText("Obliczenie nie zostało wykonane.")
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


def _format_result(result: SelectedParcelResult) -> str:
    preparation = result.preparation
    report = preparation.report
    calculation = result.calculation

    if calculation is None:
        legal_result_lines = (
            "WYNIK USTAWOWY",
            "Nie wyznaczono — geometria wymagała naprawy w trybie STRICT.",
        )
    else:
        legal_result_lines = (
            "WYNIK USTAWOWY",
            f"Pole z geometrii Po: {_format_number(calculation.po_m2, 4)} m²",
            "Poprawka odwzorowawcza: "
            f"{_format_number(calculation.correction_m2, 8)} m²",
            "Pole po korekcie: "
            f"{_format_number(calculation.legal_area_m2_raw, 8)} m²",
            "Pole ewidencyjne: "
            f"{str(calculation.legal_area_ha_rounded).replace('.', ',')} ha",
            "PGK — prawne X (północna): "
            f"{_format_number(calculation.pgk_x_northing, 3)} m",
            "PGK — prawne Y (wschodnia): "
            f"{_format_number(calculation.pgk_y_easting, 3)} m",
        )

    warnings = tuple(_warning_label(warning) for warning in result.warnings)
    warning_lines = warnings if warnings else ("Brak.",)

    lines = (
        legal_result_lines
        + (
            "",
            "STREFA I GEOMETRIA",
            f"Strefa PL-2000: {preparation.zone} "
            f"(EPSG:{preparation.target_epsg})",
            "Poprawna według GEOS przed naprawą: "
            f"{_yes_no(report.validity_before)}",
            "Poprawna według GEOS po naprawie: "
            f"{_yes_no(report.validity_after)}",
            f"Metoda naprawy: {_REPAIR_METHOD_LABELS[report.repair_method]}",
            f"Części: {report.original_part_count} → "
            f"{report.repaired_part_count}",
            f"Pierścienie: {report.original_ring_count} → "
            f"{report.repaired_ring_count}",
            f"Wierzchołki: {report.original_vertex_count} → "
            f"{report.repaired_vertex_count}",
            f"Wierzchołki dodane/usunięte: {report.vertices_added}/"
            f"{report.vertices_removed}",
            "Pole geometrii przed/po: "
            f"{_format_number(report.original_area_m2, 4)} / "
            f"{_format_number(report.repaired_area_m2, 4)} m²",
            "Różnica pola po naprawie: "
            f"{_format_number(report.area_difference_m2, 8)} m²",
            "",
            "OSTRZEŻENIA",
        )
        + warning_lines
    )
    return "\n".join(lines)


def _warning_label(warning: str) -> str:
    warning_code, separator, details = warning.partition(": ")
    label = _WARNING_LABELS.get(warning_code, warning_code)
    if separator:
        return f"{label} Szczegóły: {details}"
    return label


def _format_number(value: float, decimal_places: int) -> str:
    return f"{value:.{decimal_places}f}".replace(".", ",")


def _yes_no(value: bool) -> str:
    return "tak" if value else "nie"
