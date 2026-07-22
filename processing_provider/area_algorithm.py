"""Batch Processing algorithm for statutory cadastral area calculation."""

from typing import Dict, Iterable, Optional, Tuple

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QCoreApplication

if "." in __package__:
    from ..adapters import (
        GeometryInputError,
        GeometryRepairError,
        GeometryRepairReport,
        GeometryTransformError,
        RepairMethod,
        RepairMode,
        ZoneSelectionError,
        prepare_geometry,
        resolve_target_pl2000_crs,
    )
    from ..compat import (
        FIELD_TYPE_BOOL,
        FIELD_TYPE_DOUBLE,
        FIELD_TYPE_INT,
        FIELD_TYPE_STRING,
    )
    from ..core import AreaCalculationError, AreaCalculationResult, calculate_area
else:
    from adapters import (
        GeometryInputError,
        GeometryRepairError,
        GeometryRepairReport,
        GeometryTransformError,
        RepairMethod,
        RepairMode,
        ZoneSelectionError,
        prepare_geometry,
        resolve_target_pl2000_crs,
    )
    from compat import (
        FIELD_TYPE_BOOL,
        FIELD_TYPE_DOUBLE,
        FIELD_TYPE_INT,
        FIELD_TYPE_STRING,
    )
    from core import AreaCalculationError, AreaCalculationResult, calculate_area


class CalculateEgibAreaAlgorithm(QgsProcessingAlgorithm):
    """Calculate statutory areas and write a separate diagnostic layer."""

    INPUT = "INPUT"
    ZONE = "ZONE"
    REPAIR_MODE = "REPAIR_MODE"
    OUTPUT = "OUTPUT"

    ZONE_OPTIONS = (
        "Z CRS warstwy (tylko EPSG:2176–2179)",
        "Strefa 5 — EPSG:2176",
        "Strefa 6 — EPSG:2177",
        "Strefa 7 — EPSG:2178",
        "Strefa 8 — EPSG:2179",
    )
    ZONE_BY_INDEX = {1: 5, 2: 6, 3: 7, 4: 8}

    REPAIR_OPTIONS = (
        "STRICT — bez wyniku ustawowego po naprawie",
        "AUTO_REPAIR — oblicz po naprawie",
    )

    OUTPUT_FIELD_NAMES = (
        "egib_po_m2",
        "egib_corr_m2",
        "egib_area_m2",
        "egib_area_ha",
        "egib_zone",
        "egib_epsg",
        "egib_pgk_x",
        "egib_pgk_y",
        "egib_sigma",
        "egib_scale",
        "egib_status",
        "egib_valid_before",
        "egib_valid_after",
        "egib_repair_method",
        "egib_orig_parts",
        "egib_repaired_parts",
        "egib_orig_rings",
        "egib_repaired_rings",
        "egib_orig_vertices",
        "egib_repaired_vertices",
        "egib_orig_area_m2",
        "egib_repaired_area_m2",
        "egib_area_diff_m2",
        "egib_vertices_added",
        "egib_vertices_removed",
        "egib_warnings",
    )

    def name(self) -> str:
        return "calculate_egib_area"

    def displayName(self) -> str:
        return self.tr("Oblicz powierzchnię działek EGiB")

    def group(self) -> str:
        return self.tr("Powierzchnia działki EGiB")

    def groupId(self) -> str:
        return "egib_area"

    def shortHelpString(self) -> str:
        return self.tr(
            "Oblicza powierzchnię działek z poprawką odwzorowawczą. "
            "Warstwa wejściowa nie jest modyfikowana; wynik powstaje w nowej "
            "warstwie PL-2000 wraz z raportem walidacji i naprawy geometrii."
        )

    def createInstance(self) -> "CalculateEgibAreaAlgorithm":
        return CalculateEgibAreaAlgorithm()

    def initAlgorithm(self, config: Optional[dict] = None) -> None:
        del config
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr("Warstwa działek"),
                [Qgis.ProcessingSourceType.VectorPolygon],
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.ZONE,
                self.tr("Strefa PL-2000"),
                options=list(self.ZONE_OPTIONS),
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.REPAIR_MODE,
                self.tr("Tryb obsługi niepoprawnej geometrii"),
                options=list(self.REPAIR_OPTIONS),
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Wyniki z diagnostyką"),
                Qgis.ProcessingSourceType.VectorPolygon,
            )
        )

    def processAlgorithm(
        self,
        parameters: dict,
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> Dict[str, object]:
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(
                self.tr("Nie można odczytać warstwy wejściowej.")
            )

        source.setInvalidGeometryCheck(Qgis.InvalidGeometryCheck.NoCheck)
        selected_zone = self._selected_zone(parameters, context)
        repair_mode = self._repair_mode(parameters, context)

        try:
            target_selection = resolve_target_pl2000_crs(
                source.sourceCrs(),
                selected_zone=selected_zone,
            )
        except (AreaCalculationError, ZoneSelectionError) as error:
            raise QgsProcessingException(str(error)) from error

        output_fields = self._output_fields(source.fields())
        output_wkb_type = QgsWkbTypes.multiType(
            QgsWkbTypes.linearType(source.wkbType())
        )
        sink, destination_id = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            output_fields,
            output_wkb_type,
            target_selection.crs,
        )
        if sink is None:
            raise QgsProcessingException(
                self.tr("Nie można utworzyć warstwy wynikowej.")
            )

        feature_count = source.featureCount()
        for feature_index, source_feature in enumerate(source.getFeatures()):
            if feedback.isCanceled():
                break

            output_feature = self._process_feature(
                source_feature,
                output_fields,
                source.sourceCrs(),
                context,
                feedback,
                selected_zone=selected_zone,
                target_epsg=target_selection.epsg,
                target_zone=target_selection.zone,
                repair_mode=repair_mode,
            )
            if not sink.addFeature(output_feature, QgsFeatureSink.FastInsert):
                raise QgsProcessingException(
                    self.tr("Nie można zapisać obiektu w warstwie wynikowej.")
                )

            if feature_count > 0:
                feedback.setProgress((feature_index + 1) * 100.0 / feature_count)

        return {self.OUTPUT: destination_id}

    def _process_feature(
        self,
        source_feature: QgsFeature,
        output_fields: QgsFields,
        source_crs: QgsCoordinateReferenceSystem,
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
        *,
        selected_zone: Optional[int],
        target_epsg: int,
        target_zone: int,
        repair_mode: RepairMode,
    ) -> QgsFeature:
        values = self._empty_result_values()
        values["egib_epsg"] = target_epsg
        values["egib_zone"] = target_zone
        output_geometry = QgsGeometry()

        try:
            prepared = prepare_geometry(
                source_feature.geometry(),
                source_crs,
                context.transformContext(),
                selected_zone=selected_zone,
                repair_mode=repair_mode,
            )
            self._put_report(values, prepared.report)
            values["egib_zone"] = prepared.zone
            values["egib_epsg"] = prepared.target_epsg
            output_geometry = QgsGeometry(prepared.geometry_for_area)

            if prepared.statutory_result_allowed:
                calculation = calculate_area(
                    po_m2=prepared.geometry_for_area.area(),
                    boundary_points=prepared.original_boundary_points,
                    epsg=prepared.target_epsg,
                )
                self._put_calculation(values, calculation)
                values["egib_status"] = (
                    "repaired"
                    if prepared.report.repair_method is not RepairMethod.NONE
                    else "ok"
                )
                values["egib_warnings"] = self._joined_warnings(
                    prepared.report.warnings,
                    calculation.warnings,
                )
            else:
                values["egib_status"] = "strict_repair_required"

        except GeometryRepairError as error:
            self._put_report(values, error.report)
            values["egib_status"] = "repair_failed"
            values["egib_warnings"] = self._joined_warnings(
                error.report.warnings,
                (str(error),),
            )
            feedback.reportError(
                self.tr(f"Obiekt {source_feature.id()}: {error}"),
                fatalError=False,
            )
        except (
            AreaCalculationError,
            GeometryInputError,
            GeometryTransformError,
            ZoneSelectionError,
        ) as error:
            values["egib_status"] = "error"
            values["egib_warnings"] = str(error)
            feedback.reportError(
                self.tr(f"Obiekt {source_feature.id()}: {error}"),
                fatalError=False,
            )

        output_feature = QgsFeature(output_fields)
        output_feature.setAttributes(
            list(source_feature.attributes())
            + [values[field_name] for field_name in self.OUTPUT_FIELD_NAMES]
        )
        if not output_geometry.isNull():
            if not output_geometry.isMultipart():
                output_geometry.convertToMultiType()
            output_feature.setGeometry(output_geometry)
        return output_feature

    def _output_fields(self, source_fields: QgsFields) -> QgsFields:
        collisions = set(source_fields.names()) & set(self.OUTPUT_FIELD_NAMES)
        if collisions:
            names = ", ".join(sorted(collisions))
            raise QgsProcessingException(
                self.tr(f"Warstwa wejściowa zawiera zarezerwowane pola: {names}")
            )

        fields = QgsFields(source_fields)
        for field in self._diagnostic_fields():
            if not fields.append(field):
                raise QgsProcessingException(
                    self.tr(f"Nie można dodać pola wynikowego {field.name()}.")
                )
        return fields

    @classmethod
    def _diagnostic_fields(cls) -> Tuple[QgsField, ...]:
        def double_field(name: str, precision: int = 10) -> QgsField:
            return QgsField(name, FIELD_TYPE_DOUBLE, "", 24, precision)

        def integer_field(name: str) -> QgsField:
            return QgsField(name, FIELD_TYPE_INT)

        def boolean_field(name: str) -> QgsField:
            return QgsField(name, FIELD_TYPE_BOOL)

        def string_field(name: str, length: int) -> QgsField:
            return QgsField(name, FIELD_TYPE_STRING, "", length)

        return (
            double_field("egib_po_m2"),
            double_field("egib_corr_m2"),
            double_field("egib_area_m2"),
            double_field("egib_area_ha", 4),
            integer_field("egib_zone"),
            integer_field("egib_epsg"),
            double_field("egib_pgk_x", 3),
            double_field("egib_pgk_y", 3),
            double_field("egib_sigma", 8),
            double_field("egib_scale", 10),
            string_field("egib_status", 40),
            boolean_field("egib_valid_before"),
            boolean_field("egib_valid_after"),
            string_field("egib_repair_method", 20),
            integer_field("egib_orig_parts"),
            integer_field("egib_repaired_parts"),
            integer_field("egib_orig_rings"),
            integer_field("egib_repaired_rings"),
            integer_field("egib_orig_vertices"),
            integer_field("egib_repaired_vertices"),
            double_field("egib_orig_area_m2"),
            double_field("egib_repaired_area_m2"),
            double_field("egib_area_diff_m2"),
            integer_field("egib_vertices_added"),
            integer_field("egib_vertices_removed"),
            string_field("egib_warnings", 2000),
        )

    @classmethod
    def _empty_result_values(cls) -> Dict[str, object]:
        return {field_name: None for field_name in cls.OUTPUT_FIELD_NAMES}

    @staticmethod
    def _put_report(
        values: Dict[str, object],
        report: GeometryRepairReport,
    ) -> None:
        values.update(
            {
                "egib_valid_before": report.validity_before,
                "egib_valid_after": report.validity_after,
                "egib_repair_method": report.repair_method.value,
                "egib_orig_parts": report.original_part_count,
                "egib_repaired_parts": report.repaired_part_count,
                "egib_orig_rings": report.original_ring_count,
                "egib_repaired_rings": report.repaired_ring_count,
                "egib_orig_vertices": report.original_vertex_count,
                "egib_repaired_vertices": report.repaired_vertex_count,
                "egib_orig_area_m2": report.original_area_m2,
                "egib_repaired_area_m2": report.repaired_area_m2,
                "egib_area_diff_m2": report.area_difference_m2,
                "egib_vertices_added": report.vertices_added,
                "egib_vertices_removed": report.vertices_removed,
                "egib_warnings": CalculateEgibAreaAlgorithm._joined_warnings(
                    report.warnings
                ),
            }
        )

    @staticmethod
    def _put_calculation(
        values: Dict[str, object],
        calculation: AreaCalculationResult,
    ) -> None:
        values.update(
            {
                "egib_po_m2": calculation.po_m2,
                "egib_corr_m2": calculation.correction_m2,
                "egib_area_m2": calculation.legal_area_m2_raw,
                "egib_area_ha": float(calculation.legal_area_ha_rounded),
                "egib_zone": calculation.zone,
                "egib_epsg": calculation.epsg,
                "egib_pgk_x": calculation.pgk_x_northing,
                "egib_pgk_y": calculation.pgk_y_easting,
                "egib_sigma": calculation.sigma_cm_per_km,
                "egib_scale": calculation.scale_m,
            }
        )

    def _selected_zone(
        self,
        parameters: dict,
        context: QgsProcessingContext,
    ) -> Optional[int]:
        zone_index = self.parameterAsEnum(parameters, self.ZONE, context)
        if zone_index == 0:
            return None
        try:
            return self.ZONE_BY_INDEX[zone_index]
        except KeyError as error:
            raise QgsProcessingException(
                self.tr("Nieprawidłowy wybór strefy.")
            ) from error

    def _repair_mode(
        self,
        parameters: dict,
        context: QgsProcessingContext,
    ) -> RepairMode:
        mode_index = self.parameterAsEnum(parameters, self.REPAIR_MODE, context)
        if mode_index == 0:
            return RepairMode.STRICT
        if mode_index == 1:
            return RepairMode.AUTO_REPAIR
        raise QgsProcessingException(self.tr("Nieprawidłowy tryb naprawy geometrii."))

    @staticmethod
    def _joined_warnings(*warning_groups: Iterable[str]) -> str:
        return "; ".join(
            warning
            for warning_group in warning_groups
            for warning in warning_group
            if warning
        )

    @staticmethod
    def tr(message: str) -> str:
        return QCoreApplication.translate("CalculateEgibAreaAlgorithm", message)
