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
from qgis.PyQt.QtCore import QEvent
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
    QToolTip,
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
}

_REPAIR_METHOD_LABELS = {
    RepairMethod.NONE: "nie była potrzebna",
    RepairMethod.STRUCTURE: "Structure",
    RepairMethod.LINEWORK: "Linework",
    RepairMethod.FAILED: "nieudana",
}

_REPAIR_OPTION_SOURCE = (
    "Nie wykrywaj błędów geometrii; licz obiekt źródłowy"
)
_REPAIR_OPTION_AUTO = "Wykryj błędy i spróbuj naprawić geometrię"

_EVENT_TYPE_ENUM = getattr(QEvent, "Type", QEvent)
_TOOLTIP_EVENT_TYPE = getattr(_EVENT_TYPE_ENUM, "ToolTip")

_WARNING_DETAILS = {
    "duplicate_boundary_points_removed": (
        "Powtarzające się pary współrzędnych zostały usunięte przed "
        "obliczeniem średniej arytmetycznej. Każdy unikalny punkt graniczny "
        "wpływa więc na położenie P_GK tylko jeden raz."
    ),
    "geometry_invalid_before_repair": (
        "Kontrola GEOS wykryła błąd topologiczny, na przykład "
        "samoprzecięcie albo nieprawidłowe ułożenie pierścieni. Dalszy wynik "
        "zależy od wybranej metody obsługi geometrii."
    ),
    "multipart_geometry": (
        "Obiekt składa się z kilku części poligonowych. Pole obejmuje "
        "wszystkie części, a P_GK jest wyznaczany z punktów granicznych "
        "każdej z nich."
    ),
    "interior_rings_included": (
        "Obiekt zawiera otwory. Punkty ich pierścieni są punktami granicy "
        "poligonu i zostały uwzględnione przy wyznaczaniu P_GK. Może to "
        "wpłynąć na położenie przybliżonego środka ciężkości."
    ),
    "geometry_repaired": (
        "Do obliczenia użyto kopii geometrii naprawionej przez QGIS/GEOS. "
        "Geometria na warstwie źródłowej nie została zmieniona."
    ),
    "repair_changed_boundary_vertices": (
        "Naprawa dodała lub usunęła współrzędne na granicy poligonu. Pole "
        "P₀ obliczono z naprawionej kopii, natomiast P_GK nadal pochodzi z "
        "punktów geometrii sprzed naprawy."
    ),
    "repair_changed_part_count": (
        "Po naprawie poligon ma inną liczbę części. Zmiana dotyczy wyłącznie "
        "kopii używanej do obliczenia i warstwy wynikowej."
    ),
    "repair_changed_ring_count": (
        "Po naprawie zmieniła się liczba pierścieni zewnętrznych lub "
        "wewnętrznych. Może to oznaczać zmianę topologii poligonu."
    ),
    "repair_changed_area": (
        "Pole naprawionej kopii różni się od pola geometrii wejściowej. "
        "Dokładną różnicę pokazano w sekcji diagnostycznej."
    ),
    "structure_not_supported": (
        "Bieżąca wersja QGIS/GEOS nie obsługuje metody Structure. Wtyczka "
        "przechodzi do próby metodą Linework."
    ),
    "structure_failed": (
        "Metoda Structure nie utworzyła poprawnej geometrii poligonowej. "
        "Wtyczka przechodzi do próby metodą Linework."
    ),
    "linework_not_supported": (
        "Bieżąca wersja QGIS/GEOS nie obsługuje metody Linework."
    ),
    "linework_failed": (
        "Metoda Linework nie utworzyła poprawnej geometrii poligonowej."
    ),
}

_PARAMETER_DETAILS = {
    "param:pgk-x": (
        "P_GK — X₂₀₀₀",
        "Współrzędna X w układzie PL-2000 punktu określającego przybliżony "
        "środek ciężkości działki. P_GK jest średnią arytmetyczną "
        "współrzędnych unikalnych punktów granicznych.",
    ),
    "param:pgk-y": (
        "P_GK — Y₂₀₀₀",
        "Współrzędna Y w układzie PL-2000 punktu określającego przybliżony "
        "środek ciężkości działki. Zawiera prefiks pasa odwzorowawczego.",
    ),
    "param:x-gk": (
        "X_GK",
        "Niemodyfikowana współrzędna X punktu P_GK w odwzorowaniu "
        "Gaussa–Krügera, obliczona jako X₂₀₀₀ / m₀.",
    ),
    "param:y-gk": (
        "Y_GK",
        "Niemodyfikowana współrzędna Y punktu P_GK w odwzorowaniu "
        "Gaussa–Krügera, po odjęciu prefiksu pasa i przesunięcia 500 000 m.",
    ),
    "param:u": (
        "u",
        "Argument wielomianu: u = (X_GK − 5 800 000,0) · 2,0 · 10⁻⁶.",
    ),
    "param:v": (
        "v",
        "Argument wielomianu: v = Y_GK · 2,0 · 10⁻⁶.",
    ),
    "param:sigma": (
        "σ",
        "Elementarne zniekształcenie liniowe w punkcie P_GK, wyrażone "
        "w centymetrach na kilometr.",
    ),
    "param:m": (
        "m",
        "Skala zniekształcenia liniowego w punkcie P_GK: "
        "m = σ · 10⁻⁵ + 1.",
    ),
    "param:m2": (
        "m²",
        "Skala zniekształcenia powierzchniowego, równa kwadratowi skali "
        "zniekształcenia liniowego m.",
    ),
    "param:n": (
        "N",
        "Numer pasa odwzorowawczego układu PL-2000, wynikający z wybranej "
        "strefy i prefiksu współrzędnej Y₂₀₀₀.",
    ),
}

_RESULT_DETAILS = {
    "result:p0": (
        "P₀ — pole w układzie PL-2000",
        "Pole powierzchni działki obliczone z płaskich współrzędnych "
        "prostokątnych w docelowej strefie PL-2000, przed zastosowaniem "
        "powierzchniowej poprawki odwzorowawczej.",
    ),
    "result:correction": (
        "ΔP₀ — poprawka odwzorowawcza",
        "Powierzchniowa poprawka odwzorowawcza obliczona ze skali m² "
        "w punkcie P_GK. Wartość może być dodatnia albo ujemna.",
    ),
    "result:p-m2": (
        "P = P₀ − ΔP₀",
        "Pole powierzchni obiektu ewidencyjnego po uwzględnieniu poprawki "
        "odwzorowawczej. Wartość w metrach kwadratowych jest prezentowana "
        "z dokładnością do dwóch miejsc po przecinku.",
    ),
    "result:p-ha": (
        "P w hektarach",
        "Pole ewidencyjne przeliczone na hektary i zaokrąglone do 0,0001 ha "
        "zgodnie z przyjętą polityką zaokrąglania ROUND_HALF_UP.",
    ),
}

_DIAGNOSTIC_DETAILS = {
    "diagnostic:zone": (
        "Docelowa strefa PL-2000",
        "Strefa i kod EPSG, w których wykonano obliczenie. Dla warstwy "
        "spoza PL-2000 geometria została wcześniej przetransformowana "
        "w locie do tej strefy.",
    ),
    "diagnostic:valid-before": (
        "Kontrola GEOS przed naprawą",
        "Wynik testu poprawności topologicznej geometrii przed ewentualnym "
        "makeValid(). Wartość „nie sprawdzano” oznacza świadomie wybraną "
        "opcję obliczenia bez wykrywania błędów.",
    ),
    "diagnostic:valid-after": (
        "Kontrola GEOS po naprawie",
        "Wynik testu poprawności naprawionej kopii. „Nie sprawdzano” oznacza, "
        "że kontrola i naprawa geometrii były wyłączone.",
    ),
    "diagnostic:repair-method": (
        "Metoda naprawy",
        "Metoda QGIS/GEOS użyta do utworzenia poprawnej kopii poligonu. "
        "Structure zachowuje strukturę pierścieni, a Linework odbudowuje "
        "poligony z linii granicznych.",
    ),
    "diagnostic:parts": (
        "Części geometrii",
        "Liczba części poligonu przed i po naprawie. Strzałka pokazuje "
        "zmianę w kopii wykorzystywanej do obliczenia.",
    ),
    "diagnostic:rings": (
        "Pierścienie",
        "Łączna liczba pierścieni zewnętrznych i wewnętrznych przed oraz "
        "po naprawie geometrii.",
    ),
    "diagnostic:vertices": (
        "Wierzchołki",
        "Liczba unikalnych wierzchołków granicy przed i po naprawie. "
        "Techniczne punkty domykające pierścienie nie są liczone podwójnie.",
    ),
    "diagnostic:vertex-change": (
        "Wierzchołki dodane i usunięte",
        "Porównanie zbiorów współrzędnych granicy przed i po makeValid(). "
        "Zmiana może świadczyć o przebudowie kształtu poligonu.",
    ),
    "diagnostic:areas": (
        "Pole geometrii przed i po",
        "Porównanie planarnego pola kopii wejściowej i kopii po naprawie, "
        "jeszcze przed zastosowaniem poprawki odwzorowawczej.",
    ),
    "diagnostic:area-difference": (
        "Różnica pola po naprawie",
        "Pole naprawionej kopii minus pole geometrii przed naprawą. Zero "
        "oznacza brak zmiany pola z dokładnością prezentacji.",
    ),
}


class TechnicalReportBrowser(QTextBrowser):
    """Read-only report with contextual help for symbols and warnings."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._hover_help = {}

    def set_hover_help(self, hover_help: dict) -> None:
        self._hover_help = dict(hover_help)

    def viewportEvent(self, event: object) -> bool:
        if event.type() == _TOOLTIP_EVENT_TYPE:
            help_key = self.anchorAt(event.pos())
            help_text = self._hover_help.get(help_key)
            if help_text:
                QToolTip.showText(event.globalPos(), help_text, self)
                return True
            QToolTip.hideText()
        return super().viewportEvent(event)


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
        self.setMinimumSize(680, 480)
        self.resize(840, 600)
        self._colors = _theme_colors(self)
        self._build_ui()
        self.setStyleSheet(_dialog_stylesheet(self._colors))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 11, 14, 11)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        icon_label = QLabel()
        icon_label.setObjectName("dialogIcon")
        icon_label.setPixmap(self.windowIcon().pixmap(28, 28))
        icon_label.setFixedSize(30, 30)
        header_layout.addWidget(icon_label)

        heading_layout = QVBoxLayout()
        heading_layout.setSpacing(0)
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
        selection_layout.setContentsMargins(10, 6, 10, 6)
        selection_layout.setSpacing(8)

        layer_caption = QLabel("WYBRANY OBIEKT")
        layer_caption.setObjectName("eyebrowLabel")
        selection_layout.addWidget(layer_caption)

        layer_name = QLabel(
            f"<b>Warstwa:</b> {escape(self._layer.name())}"
        )
        layer_name.setObjectName("selectionField")
        layer_name.setToolTip(
            _tooltip_html(
                "Warstwa źródłowa",
                "Nazwa aktywnej warstwy, z której pochodzi wybrany obiekt: "
                f"{self._layer.name()}. Wtyczka pracuje na kopii geometrii "
                "i nie modyfikuje tej warstwy.",
            )
        )
        selection_layout.addWidget(layer_name, 1)

        authid = self._layer.crs().authid()
        epsg = (
            authid.partition(":")[2]
            if authid.upper().startswith("EPSG:")
            else "brak"
        )
        epsg_label = QLabel(
            f"<b>Wykryty EPSG:</b> {escape(epsg or 'brak')}"
        )
        epsg_label.setObjectName("selectionField")
        epsg_label.setToolTip(_source_crs_tooltip(self._layer.crs()))
        selection_layout.addWidget(epsg_label)

        object_label = QLabel(f"<b>Obiekt:</b> {self._feature.id()}")
        object_label.setObjectName("selectionField")
        object_label.setToolTip(
            _tooltip_html(
                "Identyfikator obiektu",
                "Wewnętrzny identyfikator wybranego obiektu w warstwie: "
                f"{self._feature.id()}. Obliczenie dotyczy wyłącznie tego "
                "jednego poligonu.",
            )
        )
        selection_layout.addWidget(object_label)
        layout.addWidget(selection_card)

        settings_group = QGroupBox("Ustawienia obliczenia")
        settings_group.setObjectName("settingsGroup")
        settings_layout = QFormLayout(settings_group)
        settings_layout.setContentsMargins(11, 14, 11, 8)
        settings_layout.setHorizontalSpacing(12)
        settings_layout.setVerticalSpacing(5)

        self.zone_combo = QComboBox()
        self.zone_combo.setObjectName("zoneCombo")
        self._populate_zone_combo()
        settings_layout.addRow("Docelowy układ PL-2000", self.zone_combo)

        self.repair_mode_combo = QComboBox()
        self.repair_mode_combo.setObjectName("repairModeCombo")
        self.repair_mode_combo.addItem(
            _REPAIR_OPTION_SOURCE,
            RepairMode.SOURCE_GEOMETRY.value,
        )
        self.repair_mode_combo.addItem(
            _REPAIR_OPTION_AUTO,
            RepairMode.AUTO_REPAIR.value,
        )
        self.repair_mode_combo.setToolTip(_repair_options_tooltip())
        settings_layout.addRow("Obsługa geometrii", self.repair_mode_combo)
        layout.addWidget(settings_group)

        status_card = QFrame()
        status_card.setObjectName("statusCard")
        status_card.setProperty("state", "ready")
        status_layout = QHBoxLayout(status_card)
        status_layout.setContentsMargins(10, 5, 10, 5)
        status_layout.setSpacing(7)
        self.status_indicator = QLabel("●")
        self.status_indicator.setObjectName("statusIndicator")
        status_layout.addWidget(self.status_indicator)
        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label, 1)
        layout.addWidget(status_card)
        self.status_card = status_card

        self.result_text = TechnicalReportBrowser()
        self.result_text.setObjectName("resultText")
        self.result_text.setReadOnly(True)
        self.result_text.setOpenLinks(False)
        self.result_text.setOpenExternalLinks(False)
        self.result_text.setHtml(_empty_result_html(self._colors))
        layout.addWidget(self.result_text, 1)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(7)
        button_layout.addStretch(1)
        self.close_button = QPushButton("Zamknij")
        self.close_button.setObjectName("closeButton")
        self.close_button.setProperty("role", "secondary")
        self.calculate_button = QPushButton("Oblicz powierzchnię")
        self.calculate_button.setObjectName("calculateButton")
        self.calculate_button.setProperty("role", "primary")
        self.calculate_button.setDefault(True)
        self.calculate_button.setToolTip(
            _tooltip_html(
                "Oblicz powierzchnię",
                "Tworzy roboczą kopię geometrii, w razie potrzeby "
                "transformuje ją w locie do wybranej strefy PL-2000, "
                "stosuje wybraną obsługę geometrii i wyświetla raport. "
                "Warstwa źródłowa pozostaje bez zmian.",
            )
        )
        button_layout.addWidget(self.close_button)
        button_layout.addWidget(self.calculate_button)
        layout.addLayout(button_layout)

        self.calculate_button.clicked.connect(self.calculate)
        self.zone_combo.currentIndexChanged.connect(
            self._update_zone_tooltip
        )
        self.close_button.clicked.connect(self.reject)
        self._set_status("Gotowy do obliczenia.", "ready")

    def _set_status(self, message: str, state: str) -> None:
        self.status_label.setText(message)
        self.status_card.setToolTip(_status_tooltip(message, state))
        self.status_card.setProperty("state", state)
        self.status_card.style().unpolish(self.status_card)
        self.status_card.style().polish(self.status_card)
        self.status_card.update()

    def _populate_zone_combo(self) -> None:
        source_zone = _zone_from_crs(self._layer.crs())
        if source_zone is not None:
            source_epsg = 2171 + source_zone
            self.zone_combo.addItem(
                "Wykryto PL-2000 — "
                f"strefa {source_zone} (EPSG:{source_epsg})",
                None,
            )
            self.zone_combo.setEnabled(False)
            self.zone_combo.setToolTip(
                _zone_selection_tooltip(
                    self._layer.crs(),
                    selected_zone=source_zone,
                    detected_pl2000=True,
                )
            )
            return

        self.zone_combo.addItem(
            "Wskaż strefę PL-2000, w której leży obiekt…",
            None,
        )
        for zone in (5, 6, 7, 8):
            self.zone_combo.addItem(
                f"PL-2000 — strefa {zone} (EPSG:{2171 + zone})",
                zone,
            )
        self._update_zone_tooltip()

    def _update_zone_tooltip(self) -> None:
        if not self.zone_combo.isEnabled():
            return
        self.zone_combo.setToolTip(
            _zone_selection_tooltip(
                self._layer.crs(),
                selected_zone=self.zone_combo.currentData(),
                detected_pl2000=False,
            )
        )

    def calculate(self) -> None:
        """Calculate and render the feature without editing its layer."""

        selected_zone = self.zone_combo.currentData()
        if self.zone_combo.isEnabled() and selected_zone is None:
            self._show_error(
                "Wskaż strefę PL-2000, w której leży obiekt, i potwierdź "
                "wybór przed obliczeniem."
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
        self.result_text.set_hover_help(_report_hover_help(result))
        self.result_text.setHtml(_format_result_html(result, self._colors))
        if result.calculation is None:
            self._set_status(
                "Nie wyznaczono wyniku powierzchni.",
                "warning",
            )
        elif repair_mode is RepairMode.SOURCE_GEOMETRY:
            self._set_status(
                "Obliczenie wykonano bez kontroli poprawności geometrii.",
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
                "result:p0",
                "P₀",
                "Pole powierzchni działki obliczone na podstawie "
                "współrzędnych prostokątnych płaskich w układzie "
                "PL-2000",
                f"{_format_number(calculation.po_m2, 2)} m²",
            ),
            _result_row(
                "result:correction",
                "ΔP₀",
                "Powierzchniowa poprawka odwzorowawcza",
                f"{_format_number(calculation.correction_m2, 2)} m²",
            ),
            _result_row(
                "result:p-m2",
                "P = P₀ − ΔP₀",
                "Pole powierzchni obiektu ewidencyjnego, jako fragmentu "
                "powierzchni elipsoidy GRS 80",
                f"{_format_number(calculation.legal_area_m2_raw, 2)} m²",
                prominent=True,
            ),
            _result_row(
                "result:p-ha",
                "P",
                "Pole powierzchni obiektu ewidencyjnego w hektarach",
                f"{_format_decimal(calculation.legal_area_ha_rounded)} ha",
                prominent=True,
            ),
        )
        result_content = (
            '<table class="result-table" width="100%" '
            'cellspacing="0" cellpadding="0">'
            f"{''.join(result_rows)}"
            "</table>"
        )

    parameter_content = ""
    if calculation is not None:
        parameter_items = (
            _parameter_cells(
                "param:pgk-x",
                "P<sub>GK</sub> — X₂₀₀₀",
                _format_number(calculation.pgk_x_northing, 3),
                "m",
            ),
            _parameter_cells(
                "param:pgk-y",
                "P<sub>GK</sub> — Y₂₀₀₀",
                _format_number(calculation.pgk_y_easting, 3),
                "m",
            ),
            _parameter_cells(
                "param:x-gk",
                "X<sub>GK</sub>",
                _format_number(calculation.x_gk_northing, 3),
                "m",
            ),
            _parameter_cells(
                "param:y-gk",
                "Y<sub>GK</sub>",
                _format_number(calculation.y_gk_easting, 3),
                "m",
            ),
            _parameter_cells(
                "param:u",
                "u",
                _format_number(calculation.u, 8),
            ),
            _parameter_cells(
                "param:v",
                "v",
                _format_number(calculation.v, 8),
            ),
            _parameter_cells(
                "param:sigma",
                "σ",
                _format_number(calculation.sigma_cm_per_km, 8),
                "cm/km",
            ),
            _parameter_cells(
                "param:m",
                "m",
                _format_number(calculation.scale_m, 10),
            ),
            _parameter_cells(
                "param:m2",
                "m²",
                _format_number(calculation.scale_m**2, 10),
            ),
            _parameter_cells(
                "param:n",
                "N",
                str(calculation.zone),
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
            "Najedź na symbol parametru, aby zobaczyć jego pełną definicję."
            "</div>"
            '<table class="parameter-table" width="100%" '
            'cellspacing="0" cellpadding="0">'
            f"{_wide_grid_rows(parameter_items)}"
            "</table>"
        )

    repair_method_label = _REPAIR_METHOD_LABELS[report.repair_method]
    if report.validity_before is None:
        repair_method_label = "nie wykonywano"

    geometry_items = (
        _diagnostic_cells(
            "diagnostic:zone",
            "Strefa układu PL-2000",
            f"{preparation.zone} (EPSG:{preparation.target_epsg})",
        ),
        _diagnostic_cells(
            "diagnostic:valid-before",
            "Kontrola GEOS przed naprawą",
            _yes_no(report.validity_before),
        ),
        _diagnostic_cells(
            "diagnostic:valid-after",
            "Kontrola GEOS po naprawie",
            _yes_no(report.validity_after),
        ),
        _diagnostic_cells(
            "diagnostic:repair-method",
            "Metoda naprawy",
            repair_method_label,
        ),
        _diagnostic_cells(
            "diagnostic:parts",
            "Części geometrii",
            f"{report.original_part_count} → {report.repaired_part_count}",
        ),
        _diagnostic_cells(
            "diagnostic:rings",
            "Pierścienie",
            f"{report.original_ring_count} → {report.repaired_ring_count}",
        ),
        _diagnostic_cells(
            "diagnostic:vertices",
            "Wierzchołki",
            f"{report.original_vertex_count} → "
            f"{report.repaired_vertex_count}",
        ),
        _diagnostic_cells(
            "diagnostic:vertex-change",
            "Wierzchołki dodane / usunięte",
            f"{report.vertices_added} / {report.vertices_removed}",
        ),
        _diagnostic_cells(
            "diagnostic:areas",
            "Pole geometrii przed / po",
            f"{_format_number(report.original_area_m2, 2)} / "
            f"{_format_number(report.repaired_area_m2, 2)} m²",
        ),
        _diagnostic_cells(
            "diagnostic:area-difference",
            "Różnica pola po naprawie",
            f"{_format_number(report.area_difference_m2, 2)} m²",
        ),
    )
    geometry_content = (
        '<div class="section-title">STREFA I GEOMETRIA</div>'
        '<table class="diagnostic-table single" width="100%" '
        'cellspacing="0" cellpadding="0">'
        f"{_single_grid_rows(geometry_items)}"
        "</table>"
    )

    if result.warnings:
        warning_items = "".join(
            '<li><a class="help-link" '
            f'href="warning:{warning_index}">'
            f"{escape(_warning_label(warning))}</a></li>"
            for warning_index, warning in enumerate(result.warnings)
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

    if parameter_content:
        details_content = (
            '<table class="details-layout" width="100%" '
            'cellspacing="0" cellpadding="0"><tr>'
            f'<td class="details-column left">{parameter_content}</td>'
            f'<td class="details-column">{geometry_content}</td>'
            "</tr></table>"
        )
    else:
        details_content = geometry_content

    body = (
        '<div class="section-title first">WYNIK OBLICZENIA</div>'
        f"{result_content}"
        f"{details_content}"
        f"{warning_content}"
    )
    return _html_document(body, colors)


def _result_row(
    help_key: str,
    symbol: str,
    description: str,
    value: str,
    *,
    prominent: bool = False,
) -> str:
    row_class = " prominent" if prominent else ""
    return (
        f'<tr class="result-row{row_class}">'
        '<td class="result-symbol">'
        f'<a class="help-link" href="{help_key}">{symbol}</a></td>'
        f'<td class="result-description">{escape(description)}</td>'
        f'<td class="result-value">{value}</td>'
        "</tr>"
    )


def _parameter_cells(
    help_key: str,
    symbol: str,
    value: str,
    unit: str = "",
) -> str:
    formatted_unit = f" {escape(unit)}" if unit else ""
    return (
        '<td class="parameter-symbol">'
        f'<a class="help-link" href="{help_key}">{symbol}</a></td>'
        f'<td class="parameter-value">{value}{formatted_unit}</td>'
    )


def _diagnostic_cells(help_key: str, label: str, value: str) -> str:
    return (
        '<td class="diagnostic-label">'
        f'<a class="help-link" href="{help_key}">'
        f"{escape(label)}</a></td>"
        f'<td class="diagnostic-value">{escape(value)}</td>'
    )


def _wide_grid_rows(items: Tuple[str, ...]) -> str:
    rows = []
    for index in range(0, len(items), 2):
        left = items[index]
        right = (
            items[index + 1]
            if index + 1 < len(items)
            else '<td colspan="2"></td>'
        )
        rows.append(f"<tr>{left}{right}</tr>")
    return "".join(rows)


def _single_grid_rows(items: Tuple[str, ...]) -> str:
    return "".join(f"<tr>{item}</tr>" for item in items)


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
            font-family: "DejaVu Sans Mono", Consolas, Menlo,
              "Liberation Mono", monospace;
            font-size: 8.5pt;
            margin: 8px;
          }}
          .section-title {{
            color: {colors["muted"]};
            font-size: 7.5pt;
            font-weight: 700;
            margin-top: 12px;
            margin-bottom: 5px;
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
            padding: 4px 5px;
            vertical-align: middle;
          }}
          .details-column {{
            border-bottom: 0;
            padding: 0 0 0 8px;
            vertical-align: top;
            width: 50%;
          }}
          .details-column.left {{
            border-right: 1px solid {colors["border"]};
            padding-left: 0;
            padding-right: 8px;
          }}
          .result-symbol {{
            color: {colors["accent"]};
            font-family: "DejaVu Sans Mono", Consolas, Menlo,
              "Liberation Mono", monospace;
            font-size: 9.5pt;
            font-weight: 700;
            white-space: nowrap;
            width: 24%;
          }}
          .result-description {{
            color: {colors["muted"]};
            font-size: 7.5pt;
            width: 49%;
          }}
          .result-value {{
            font-family: "DejaVu Sans Mono", Consolas, Menlo,
              "Liberation Mono", monospace;
            font-size: 9pt;
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
            font-family: "DejaVu Sans Mono", Consolas, Menlo,
              "Liberation Mono", monospace;
            font-size: 8.5pt;
            padding: 6px 8px;
          }}
          .formula-separator {{
            color: {colors["muted"]};
            padding-left: 12px;
            padding-right: 12px;
          }}
          .parameter-intro {{
            color: {colors["muted"]};
            font-size: 7.5pt;
            margin-top: 5px;
            margin-bottom: 2px;
          }}
          .parameter-table, .diagnostic-table {{
            margin-top: 5px;
          }}
          .parameter-symbol, .diagnostic-label {{
            color: {colors["muted"]};
            width: 18%;
          }}
          .parameter-symbol {{
            font-family: "DejaVu Sans Mono", Consolas, Menlo,
              "Liberation Mono", monospace;
            font-size: 8.5pt;
          }}
          .parameter-value, .diagnostic-value {{
            font-family: "DejaVu Sans Mono", Consolas, Menlo,
              "Liberation Mono", monospace;
            text-align: right;
            white-space: nowrap;
            width: 32%;
          }}
          .diagnostic-table.single .diagnostic-label {{
            width: 64%;
          }}
          .diagnostic-table.single .diagnostic-value {{
            width: 36%;
          }}
          a.help-link {{
            color: {colors["accent"]};
            text-decoration: none;
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
            margin-top: 30px;
          }}
          .welcome-mark {{
            color: {colors["accent"]};
            font-family: "DejaVu Sans Mono", Consolas, Menlo,
              "Liberation Mono", monospace;
            font-size: 14pt;
            font-weight: 700;
            margin-bottom: 7px;
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


def _report_hover_help(result: SelectedParcelResult) -> dict:
    hover_help = {
        help_key: _tooltip_html(title, description)
        for details in (
            _RESULT_DETAILS,
            _PARAMETER_DETAILS,
            _DIAGNOSTIC_DETAILS,
        )
        for help_key, (title, description) in details.items()
    }
    for warning_index, warning in enumerate(result.warnings):
        warning_code, separator, details = warning.partition(": ")
        description = _WARNING_DETAILS.get(
            warning_code,
            "Wtyczka zgłosiła dodatkową informację diagnostyczną dla "
            "tego obliczenia.",
        )
        if separator:
            description = f"{description} Szczegóły techniczne: {details}"
        hover_help[f"warning:{warning_index}"] = _tooltip_html(
            "Wyjaśnienie uwagi",
            description,
        )
    return hover_help


def _repair_options_tooltip() -> str:
    source_description = (
        "Wtyczka pomija kontrolę GEOS i nie uruchamia makeValid(). "
        "P₀ jest obliczane z kopii geometrii obiektu źródłowego po "
        "transformacji do PL-2000. Błędy topologiczne mogą więc wpłynąć "
        "na wiarygodność pola. Nadal sprawdzane są podstawowe warunki "
        "techniczne: obecność poligonu, strefa PL-2000 oraz skończoność "
        "i dodatniość wyniku. "
        "Warstwa źródłowa nie jest modyfikowana."
    )
    repair_description = (
        "Wtyczka sprawdza geometrię za pomocą GEOS. Jeżeli wykryje błąd, "
        "próbuje naprawić kopię metodą Structure, a następnie Linework. "
        "Naprawa może zmienić pole, granicę, liczbę części lub pierścieni. "
        "P_GK nadal pochodzi z punktów sprzed naprawy, a warstwa źródłowa "
        "pozostaje bez zmian."
    )
    return (
        '<html><div style="width:430px">'
        f"<b>{escape(_REPAIR_OPTION_SOURCE)}</b><br>"
        f"{escape(source_description)}"
        '<br><br><span style="color:#176b8b">'
        f"<b>{escape(_REPAIR_OPTION_AUTO)}</b></span><br>"
        f"{escape(repair_description)}"
        "</div></html>"
    )


def _status_tooltip(message: str, state: str) -> str:
    if state == "ready":
        details = (
            "Wtyczka czeka na uruchomienie obliczenia. Sprawdź docelową "
            "strefę PL-2000 i sposób obsługi geometrii."
        )
    elif "bez kontroli" in message:
        details = (
            "Wynik obliczono z kopii geometrii źródłowej bez testu GEOS "
            "i bez makeValid(). Błędy topologiczne mogły wpłynąć na pole."
        )
    elif "naprawionej kopii" in message:
        details = (
            "GEOS wykrył problem, a wynik obliczono z naprawionej kopii. "
            "Sprawdź uwagi oraz porównanie geometrii przed i po naprawie."
        )
    elif state == "success":
        details = (
            "Obliczenie zakończyło się bez błędów i bez potrzeby naprawy "
            "geometrii."
        )
    elif state == "error":
        details = (
            "Nie utworzono wyniku. Szczegóły przyczyny pokazuje komunikat "
            "ostrzegawczy QGIS."
        )
    else:
        details = (
            "Obliczenie wymaga uwagi użytkownika. Sprawdź treść raportu "
            "i wyjaśnienia poszczególnych ostrzeżeń."
        )
    return _tooltip_html("Status obliczenia", details)


def _source_crs_tooltip(crs: QgsCoordinateReferenceSystem) -> str:
    authid = crs.authid() or "brak identyfikatora"
    description = crs.description() or "brak nazwy układu"
    if authid.upper().startswith("EPSG:"):
        details = (
            f"Warstwa ma przypisany układ {authid} — {description}. "
            "Jest to źródłowy układ współrzędnych używany do odczytania "
            "geometrii. Jeżeli nie jest to PL-2000, robocza kopia obiektu "
            "zostanie podczas obliczenia przetransformowana w locie do "
            "wybranej strefy PL-2000."
        )
    else:
        details = (
            f"Warstwa ma przypisany układ „{description}” ({authid}), ale "
            "nie udało się odczytać identyfikatora EPSG. Przed obliczeniem "
            "sprawdź definicję CRS warstwy i wskaż właściwą strefę PL-2000."
        )
    return _tooltip_html("Wykryty układ warstwy", details)


def _zone_selection_tooltip(
    source_crs: QgsCoordinateReferenceSystem,
    *,
    selected_zone: Optional[int],
    detected_pl2000: bool,
) -> str:
    source_authid = source_crs.authid() or "CRS bez identyfikatora"
    if detected_pl2000:
        target_epsg = 2171 + int(selected_zone)
        details = (
            f"Wykryty CRS warstwy to {source_authid}, czyli układ PL-2000 "
            f"w strefie {selected_zone}. Wybór jest zablokowany, ponieważ "
            f"strefa wynika bezpośrednio z EPSG:{target_epsg}. Obliczenia "
            "są wykonywane na kopii obiektu; warstwa źródłowa pozostaje "
            "bez zmian."
        )
        return _tooltip_html("Automatycznie wykryto PL-2000", details)

    transform_details = (
        f"Wykryty układ źródłowy to {source_authid}, a nie jedna z czterech "
        "stref PL-2000. Wtyczka nie zgaduje strefy na podstawie centroidu. "
        "Wskaż strefę 5, 6, 7 albo 8 zgodną z rzeczywistym położeniem "
        "obiektu. Podczas obliczenia robocza kopia geometrii zostanie "
        "przeliczona w locie do wskazanego układu PL-2000. Warstwa "
        "źródłowa i jej CRS nie zostaną zmienione."
    )
    if selected_zone is None:
        return _tooltip_html(
            "Wymagany wybór strefy PL-2000",
            transform_details,
        )

    target_epsg = 2171 + int(selected_zone)
    return _tooltip_html(
        f"Wybrano strefę {selected_zone} — EPSG:{target_epsg}",
        transform_details
        + f" Aktualnie wskazano strefę {selected_zone} "
        f"(EPSG:{target_epsg}).",
    )


def _tooltip_html(title: str, description: str) -> str:
    return (
        '<html><div style="width:380px">'
        f"<b>{escape(title)}</b><br>{escape(description)}"
        "</div></html>"
    )


def _format_number(value: float, decimal_places: int) -> str:
    return f"{value:.{decimal_places}f}".replace(".", ",")


def _format_decimal(value: object) -> str:
    return str(value).replace(".", ",")


def _yes_no(value: Optional[bool]) -> str:
    if value is None:
        return "nie sprawdzano"
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
        font-family: "DejaVu Sans Mono", Consolas, Menlo,
            "Liberation Mono", monospace;
        font-size: 8.5pt;
    }}
    QLabel {{
        background: transparent;
        color: {colors["text"]};
    }}
    QLabel#dialogTitle {{
        font-size: 12pt;
        font-weight: 600;
    }}
    QLabel#dialogSubtitle {{
        color: {colors["muted"]};
        font-size: 7.5pt;
    }}
    QLabel#eyebrowLabel {{
        color: {colors["accent"]};
        font-size: 7pt;
        font-weight: 700;
    }}
    QLabel#selectionField {{
        color: {colors["text"]};
        font-size: 8pt;
    }}
    QFrame#selectionCard, QGroupBox#settingsGroup,
    QTextBrowser#resultText {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        border-radius: 6px;
    }}
    QGroupBox#settingsGroup {{
        color: {colors["text"]};
        font-weight: 600;
        margin-top: 7px;
        padding-top: 4px;
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
        border-radius: 4px;
        min-height: 20px;
        padding: 3px 30px 3px 7px;
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
        border-radius: 5px;
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
        font-size: 8pt;
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
        padding: 2px;
        selection-background-color: {colors["accent"]};
        selection-color: #ffffff;
    }}
    QPushButton {{
        min-height: 20px;
        padding: 4px 12px;
        border-radius: 4px;
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
    QToolTip {{
        color: {colors["text"]};
        background-color: {colors["surface"]};
        border: 1px solid {colors["accent"]};
        padding: 7px;
        font-family: "DejaVu Sans Mono", Consolas, Menlo,
            "Liberation Mono", monospace;
        font-size: 8pt;
    }}
    """
