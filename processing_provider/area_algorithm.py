"""Batch Processing algorithm for statutory cadastral area calculation."""

from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsDataSourceUri,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsMapLayer,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeatureSourceDefinition,
    QgsProcessingFeedback,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingUtils,
    QgsProviderRegistry,
    QgsVectorFileWriter,
    QgsVectorLayer,
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
        measure_geodesic_area_m2,
        prepare_geometry,
        resolve_target_pl2000_crs,
    )
    from ..compat import (
        FIELD_TYPE_BOOL,
        FIELD_TYPE_DOUBLE,
        FIELD_TYPE_INT,
        FIELD_TYPE_STRING,
    )
    from ..core import (
        AreaCalculationError,
        AreaCalculationResult,
        calculate_area,
    )
    from ..user_messages import (
        COORDINATE_TRANSFORM_WARNING,
        GEODESIC_MEASUREMENT_WARNING,
        safe_calculation_error_message,
    )
else:
    from adapters import (
        GeometryInputError,
        GeometryRepairError,
        GeometryRepairReport,
        GeometryTransformError,
        RepairMethod,
        RepairMode,
        ZoneSelectionError,
        measure_geodesic_area_m2,
        prepare_geometry,
        resolve_target_pl2000_crs,
    )
    from compat import (
        FIELD_TYPE_BOOL,
        FIELD_TYPE_DOUBLE,
        FIELD_TYPE_INT,
        FIELD_TYPE_STRING,
    )
    from core import (
        AreaCalculationError,
        AreaCalculationResult,
        calculate_area,
    )
    from user_messages import (
        COORDINATE_TRANSFORM_WARNING,
        GEODESIC_MEASUREMENT_WARNING,
        safe_calculation_error_message,
    )


class CalculateEgibAreaAlgorithm(QgsProcessingAlgorithm):
    """Calculate statutory areas and write a separate diagnostic layer."""

    INPUT = "INPUT"
    ZONE = "ZONE"
    REPAIR_MODE = "REPAIR_MODE"
    OUTPUT = "OUTPUT"
    OVERWRITE_ERROR = (
        "Wynik nie może nadpisać pliku źródłowego ani istniejącej tabeli "
        "w tym pliku lub bazie. Wybierz nowy plik lub nową nazwę warstwy."
    )

    ZONE_OPTIONS = (
        "Z CRS warstwy (tylko EPSG:2176–2179)",
        "Strefa 5 — EPSG:2176",
        "Strefa 6 — EPSG:2177",
        "Strefa 7 — EPSG:2178",
        "Strefa 8 — EPSG:2179",
    )
    ZONE_BY_INDEX = {1: 5, 2: 6, 3: 7, 4: 8}

    REPAIR_OPTIONS = (
        "Sprawdź geometrię; licz bez naprawy",
        "Wykryj błędy i spróbuj naprawić geometrię "
        "(uwaga: geometria wyniku może się zmienić)",
    )

    OUTPUT_FIELD_NAMES = (
        "PO_P0_m2",
        "PO_QGIS_m2",
        "PO_dP_m2",
        "PO_P_m2",
        "PO_P_ha",
        "PO_strefa",
        "PO_EPSG",
        "PO_PGK_X",
        "PO_PGK_Y",
        "PO_sigma",
        "PO_skala",
        "PO_status",
        "PO_poprawna_przed",
        "PO_poprawna_po",
        "PO_naprawa",
        "PO_czesci_przed",
        "PO_czesci_po",
        "PO_piersc_przed",
        "PO_piersc_po",
        "PO_wierz_przed",
        "PO_wierz_po",
        "PO_pole_przed_m2",
        "PO_pole_po_m2",
        "PO_zmiana_m2",
        "PO_pkt_dodane",
        "PO_pkt_usuniete",
        "PO_uwagi",
    )

    OUTPUT_FIELD_ALIASES = {
        "PO_P0_m2": "Powierzchnia przed poprawką P₀ [m²]",
        "PO_QGIS_m2": "Pomiar pomocniczy QGIS [m²]",
        "PO_dP_m2": "Poprawka odwzorowawcza ΔP₀ [m²]",
        "PO_P_m2": "Powierzchnia po poprawce P [m²]",
        "PO_P_ha": "Powierzchnia po poprawce P [ha]",
        "PO_strefa": "Strefa PL-2000",
        "PO_EPSG": "Kod EPSG wyniku",
        "PO_PGK_X": "P_GK: X — północ [m]",
        "PO_PGK_Y": "P_GK: Y — wschód [m]",
        "PO_sigma": "Zniekształcenie liniowe σ [cm/km]",
        "PO_skala": "Skala liniowa m",
        "PO_status": "Status obliczenia",
        "PO_poprawna_przed": "Poprawność geometrii przed naprawą",
        "PO_poprawna_po": "Poprawność geometrii po naprawie",
        "PO_naprawa": "Metoda naprawy",
        "PO_czesci_przed": "Liczba części przed naprawą",
        "PO_czesci_po": "Liczba części po naprawie",
        "PO_piersc_przed": "Liczba pierścieni przed naprawą",
        "PO_piersc_po": "Liczba pierścieni po naprawie",
        "PO_wierz_przed": "Liczba wierzchołków przed naprawą",
        "PO_wierz_po": "Liczba wierzchołków po naprawie",
        "PO_pole_przed_m2": "Powierzchnia przed naprawą [m²]",
        "PO_pole_po_m2": "Powierzchnia po naprawie [m²]",
        "PO_zmiana_m2": "Zmiana powierzchni wskutek naprawy [m²]",
        "PO_pkt_dodane": "Unikalne punkty dodane przez naprawę",
        "PO_pkt_usuniete": "Unikalne punkty usunięte przez naprawę",
        "PO_uwagi": "Uwagi i ostrzeżenia",
    }

    def name(self) -> str:
        return "calculate_egib_area"

    def displayName(self) -> str:
        return self.tr("Poprawka odwzorowawcza PL-2000")

    def group(self) -> str:
        return ""

    def groupId(self) -> str:
        return ""

    def shortHelpString(self) -> str:
        return self.tr(
            "Oblicza powierzchnię działek z poprawką odwzorowawczą. "
            "Oprócz głównego wyniku P zapisuje kartezjańskie P₀ oraz "
            "niezależny pomiar geodezyjny QGIS na elipsoidzie GRS 80. "
            "Warstwa wejściowa nie jest modyfikowana; wynik powstaje w nowej "
            "warstwie PL-2000. Oba tryby sprawdzają poprawność GEOS. "
            "Tryb bez naprawy liczy z niezmienionej kopii po transformacji; "
            "wynik dla błędnej geometrii jest tylko diagnostyczny. "
            "Tryb naprawy może zmienić kopię w warstwie wynikowej. "
            "P₀ i P_GK zawsze pochodzą z tej samej geometrii: "
            "bez naprawy — źródłowej, po naprawie — poprawionej. "
            "Wynik ma rzeczywiste pola z prefiksem PO_, m.in. PO_P0_m2, "
            "PO_dP_m2, PO_P_m2 i PO_P_ha. Starsze modele i wyrażenia "
            "odwołujące się do egib_* wymagają aktualizacji nazw. "
            "Zalecany format wyniku to GeoPackage. Shapefile skraca nazwy "
            "pól do 10 znaków i uwagi do 254 znaków. "
            "Wynik nie może nadpisać pliku źródłowego ani istniejącej "
            "tabeli w tym pliku; można dodać nową tabelę GeoPackage."
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
                self.tr("Poprawka odwzorowawcza PL-2000"),
                Qgis.ProcessingSourceType.VectorPolygon,
            )
        )

    def processAlgorithm(
        self,
        parameters: dict,
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> Dict[str, object]:
        output_driver = self._check_output_destination(parameters, context)
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
            raise QgsProcessingException(
                self.tr(safe_calculation_error_message(error))
            ) from error

        output_fields = self._output_fields(source.fields())
        if output_driver == "GPKG":
            # The GeoPackage primary key must be unique and numeric. Keep
            # source attributes intact under a separate ordinary field name.
            used_names = {name.casefold() for name in output_fields.names()}
            for field_index, field in enumerate(source.fields()):
                if field.name().casefold() != "fid":
                    continue
                new_name = "fid_zrodlowy"
                suffix = 2
                while new_name.casefold() in used_names:
                    new_name = f"fid_zrodlowy_{suffix}"
                    suffix += 1
                output_fields.rename(field_index, new_name)
                used_names.add(new_name.casefold())
                feedback.pushInfo(
                    self.tr(
                        f"Źródłowe pole {field.name()} zachowano jako "
                        f"{new_name}; GeoPackage utworzy własny klucz fid."
                    )
                )
        elif output_driver == "ESRI Shapefile":
            feedback.pushWarning(
                self.tr(
                    "Shapefile skróci nazwy pól do 10 znaków oraz uwagi "
                    "do 254 znaków. Aby zachować pełne nazwy i diagnostykę, "
                    "zapisz wynik w GeoPackage."
                )
            )
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
        status_counts = Counter()
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
            if not sink.addFeature(
                output_feature,
                QgsFeatureSink.Flag.FastInsert,
            ):
                raise QgsProcessingException(
                    self.tr("Nie można zapisać obiektu w warstwie wynikowej.")
                )

            status_counts[output_feature["PO_status"]] += 1

            if feature_count > 0:
                feedback.setProgress(
                    (feature_index + 1) * 100.0 / feature_count
                )

        if not sink.flushBuffer():
            raise QgsProcessingException(
                self.tr("Nie można zakończyć zapisu warstwy wynikowej.")
            )
        error_count = (
            status_counts["error"]
            + status_counts["repair_failed"]
            + status_counts["calculation_not_allowed"]
        )
        feedback.pushInfo(
            self.tr(
                f"Przetworzono: {sum(status_counts.values())}; "
                "poprawne bez naprawy: "
                f"{status_counts['ok'] + status_counts['source_geometry']}; "
                f"po naprawie: {status_counts['repaired']}; "
                "diagnostyczne: "
                f"{status_counts['invalid_source_geometry']}; "
                f"błędy: {error_count}."
            )
        )
        if feedback.isCanceled():
            feedback.pushWarning(
                self.tr("Anulowano przetwarzanie. Wynik jest niepełny.")
            )
        self._destination_id = destination_id
        self._output_driver = output_driver
        return {self.OUTPUT: destination_id}

    def postProcessAlgorithm(
        self,
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> Dict[str, object]:
        """Set result headings after processing, keeping raw field names."""

        layer = QgsProcessingUtils.mapLayerFromString(
            self._destination_id, context
        )
        if not isinstance(layer, QgsVectorLayer):
            return {}
        for index, field in enumerate(layer.fields()):
            alias = self.OUTPUT_FIELD_ALIASES.get(field.name())
            if alias:
                layer.setFieldAlias(
                    index, f"{field.name()} — {self.tr(alias)}"
                )

        visible_results = {
            "PO_P0_m2",
            "PO_QGIS_m2",
            "PO_dP_m2",
            "PO_P_m2",
            "PO_P_ha",
            "PO_status",
            "PO_uwagi",
        }
        table = layer.attributeTableConfig()
        columns = table.columns()
        for column in columns:
            if column.name in self.OUTPUT_FIELD_ALIASES:
                column.hidden = column.name not in visible_results
        table.setColumns(columns)
        layer.setAttributeTableConfig(table)

        if self._output_driver == "GPKG":
            categories = (
                QgsMapLayer.StyleCategory.Fields
                | QgsMapLayer.StyleCategory.AttributeTable
            )
            if hasattr(layer, "saveStyleToDatabaseV2"):
                _results, error = layer.saveStyleToDatabaseV2(
                    "pl2000", "Polskie nagłówki wyników", True, "", categories
                )
            else:
                error = layer.saveStyleToDatabase(
                    "pl2000", "Polskie nagłówki wyników", True, "", categories
                )
            if error:
                feedback.pushWarning(
                    self.tr(
                        "Nie zapisano nagłówków i układu tabeli w GeoPackage. "
                        "Wyniki obliczeń zostały zapisane."
                    )
                )
        return {}

    def _check_output_destination(
        self,
        parameters: dict,
        context: QgsProcessingContext,
    ) -> str:
        """Check file destinations before a sink can overwrite source data."""

        destination = self.parameterAsOutputLayer(
            parameters, self.OUTPUT, context
        )
        encoded, provider, uri = QgsProcessingUtils.decodeProviderKeyAndUri(
            destination
        )
        if not encoded:
            for prefix in ("ogr", "spatialite", "postgres", "postgis"):
                if destination.startswith(prefix + ":"):
                    encoded, provider, uri = (
                        True,
                        prefix,
                        destination.removeprefix(prefix + ":"),
                    )
                    break
        if destination.startswith("memory:"):
            return ""

        registry = QgsProviderRegistry.instance()
        source_value = parameters.get(self.INPUT)
        if isinstance(source_value, QgsProcessingFeatureSourceDefinition):
            source_value = source_value.source
        source_layer = self.parameterAsVectorLayer(
            {self.INPUT: source_value}, self.INPUT, context
        )
        if encoded and provider in ("postgres", "postgis"):
            if source_layer and source_layer.providerType() == "postgres":
                source_uri = QgsDataSourceUri(source_layer.source())
                output_uri = QgsDataSourceUri(uri)
                same_connection = (
                    source_uri.host().casefold()
                    == output_uri.host().casefold()
                    and (source_uri.port() or "5432")
                    == (output_uri.port() or "5432")
                    and source_uri.service() == output_uri.service()
                    and source_uri.database() == output_uri.database()
                )
                same_schema = (
                    not source_uri.schema()
                    or not output_uri.schema()
                    or source_uri.schema() == output_uri.schema()
                )
                if (
                    same_connection
                    and same_schema
                    and source_uri.table() == output_uri.table()
                ):
                    raise QgsProcessingException(self.tr(self.OVERWRITE_ERROR))
            return ""

        output_table = ""
        if encoded:
            datasource = QgsDataSourceUri(uri)
            output_path = datasource.database()
            output_table = datasource.table()
            if not output_path:
                parts = registry.decodeUri(provider, uri)
                output_path = parts.get("path") or ""
                output_table = parts.get("layerName") or ""
        else:
            output_path = destination

        if not output_path:
            return ""
        driver = QgsVectorFileWriter.driverForExtension(
            Path(output_path).suffix.lstrip(".")
        )
        if not driver and not encoded:
            # Processing appends .gpkg when the extension is unrecognized.
            output_path += ".gpkg"
            driver = "GPKG"
        if not encoded:
            metadata = QgsVectorFileWriter.MetaData()
            if QgsVectorFileWriter.driverMetadata(driver, metadata):
                extensions = metadata.ext.split()
                if extensions and Path(output_path).suffix[1:].lower() not in (
                    extensions
                ):
                    output_path += "." + extensions[0]
        if source_layer is None:
            return driver
        source_parts = registry.decodeUri(
            source_layer.providerType(), source_layer.source()
        )
        source_path = source_parts.get("path")
        if not source_path or not Path(source_path).exists():
            return driver

        source_path = Path(source_path).resolve()
        output_path = Path(output_path).resolve()
        same_file = source_path == output_path or (
            output_path.exists() and source_path.samefile(output_path)
        )
        if same_file:
            # An OGR table destination updates the database instead of
            # replacing the entire file. Only a new table is safe here.
            tables = registry.providerMetadata("ogr").querySublayers(
                str(source_path)
            )
            if (
                not encoded
                or provider != "ogr"
                or driver != "GPKG"
                or source_path != output_path
                or not output_table
                or not tables
                or output_table.casefold()
                in {table.name().casefold() for table in tables}
            ):
                raise QgsProcessingException(self.tr(self.OVERWRITE_ERROR))
        return driver

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
        values["PO_EPSG"] = target_epsg
        values["PO_strefa"] = target_zone
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
            if "coordinate_transform_fallback" in prepared.report.warnings:
                feedback.pushWarning(
                    self.tr(
                        f"Obiekt {source_feature.id()}: "
                        f"{COORDINATE_TRANSFORM_WARNING}"
                    )
                )
            values["PO_strefa"] = prepared.zone
            values["PO_EPSG"] = prepared.target_epsg
            output_geometry = QgsGeometry(prepared.geometry_for_area)

            if prepared.calculation_allowed:
                calculation = calculate_area(
                    po_m2=prepared.geometry_for_area.area(),
                    boundary_points=prepared.boundary_points_for_calculation,
                    epsg=prepared.target_epsg,
                )
                self._put_calculation(values, calculation)
                measurement_warnings = ()
                try:
                    values["PO_QGIS_m2"] = _round_m2(
                        measure_geodesic_area_m2(
                            prepared.geometry_for_area,
                            prepared.target_crs,
                            context.transformContext(),
                        )
                    )
                except (GeometryInputError, GeometryTransformError):
                    measurement_warnings = ("geodesic_measurement_failed",)
                    feedback.pushWarning(
                        self.tr(
                            f"Obiekt {source_feature.id()}: "
                            f"{GEODESIC_MEASUREMENT_WARNING}"
                        )
                    )
                if repair_mode is RepairMode.SOURCE_GEOMETRY:
                    values["PO_status"] = (
                        "source_geometry"
                        if prepared.report.validity_after
                        else "invalid_source_geometry"
                    )
                elif prepared.report.repair_method is not RepairMethod.NONE:
                    values["PO_status"] = "repaired"
                else:
                    values["PO_status"] = "ok"
                values["PO_uwagi"] = self._joined_warnings(
                    prepared.report.warnings,
                    calculation.warnings,
                    measurement_warnings,
                )
            else:
                values["PO_status"] = "calculation_not_allowed"

        except GeometryRepairError as error:
            safe_message = safe_calculation_error_message(error)
            self._put_report(values, error.report)
            values["PO_status"] = "repair_failed"
            values["PO_uwagi"] = self._joined_warnings(
                error.report.warnings,
                (safe_message,),
            )
            feedback.reportError(
                self.tr(f"Obiekt {source_feature.id()}: {safe_message}"),
                fatalError=False,
            )
        except (
            AreaCalculationError,
            GeometryInputError,
            GeometryTransformError,
            ZoneSelectionError,
        ) as error:
            safe_message = safe_calculation_error_message(error)
            values["PO_status"] = "error"
            values["PO_uwagi"] = safe_message
            feedback.reportError(
                self.tr(f"Obiekt {source_feature.id()}: {safe_message}"),
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
        reserved = {name.casefold() for name in self.OUTPUT_FIELD_NAMES}
        collisions = {
            name
            for name in source_fields.names()
            if name.casefold() in reserved
        }
        if collisions:
            names = ", ".join(sorted(collisions))
            raise QgsProcessingException(
                self.tr(
                    f"Warstwa wejściowa zawiera zarezerwowane pola: {names}"
                )
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
            double_field("PO_P0_m2", 2),
            double_field("PO_QGIS_m2", 2),
            double_field("PO_dP_m2", 2),
            double_field("PO_P_m2", 2),
            double_field("PO_P_ha", 4),
            integer_field("PO_strefa"),
            integer_field("PO_EPSG"),
            # Preserve raw parameters when a sink respects field precision.
            # Display rounding belongs to the GUI, not these audit fields.
            QgsField("PO_PGK_X", FIELD_TYPE_DOUBLE),
            QgsField("PO_PGK_Y", FIELD_TYPE_DOUBLE),
            QgsField("PO_sigma", FIELD_TYPE_DOUBLE),
            QgsField("PO_skala", FIELD_TYPE_DOUBLE),
            string_field("PO_status", 40),
            boolean_field("PO_poprawna_przed"),
            boolean_field("PO_poprawna_po"),
            string_field("PO_naprawa", 20),
            integer_field("PO_czesci_przed"),
            integer_field("PO_czesci_po"),
            integer_field("PO_piersc_przed"),
            integer_field("PO_piersc_po"),
            integer_field("PO_wierz_przed"),
            integer_field("PO_wierz_po"),
            double_field("PO_pole_przed_m2", 2),
            double_field("PO_pole_po_m2", 2),
            double_field("PO_zmiana_m2", 2),
            integer_field("PO_pkt_dodane"),
            integer_field("PO_pkt_usuniete"),
            string_field("PO_uwagi", 2000),
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
                "PO_poprawna_przed": report.validity_before,
                "PO_poprawna_po": report.validity_after,
                "PO_naprawa": report.repair_method.value,
                "PO_czesci_przed": report.original_part_count,
                "PO_czesci_po": report.repaired_part_count,
                "PO_piersc_przed": report.original_ring_count,
                "PO_piersc_po": report.repaired_ring_count,
                "PO_wierz_przed": report.original_vertex_count,
                "PO_wierz_po": report.repaired_vertex_count,
                "PO_pole_przed_m2": _round_m2(report.original_area_m2),
                "PO_pole_po_m2": _round_m2(report.repaired_area_m2),
                "PO_zmiana_m2": _round_m2(report.area_difference_m2),
                "PO_pkt_dodane": report.vertices_added,
                "PO_pkt_usuniete": report.vertices_removed,
                "PO_uwagi": CalculateEgibAreaAlgorithm._joined_warnings(
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
                "PO_P0_m2": _round_m2(calculation.po_m2),
                "PO_dP_m2": _round_m2(calculation.correction_m2),
                "PO_P_m2": _round_m2(calculation.legal_area_m2_raw),
                "PO_P_ha": float(calculation.legal_area_ha_rounded),
                "PO_strefa": calculation.zone,
                "PO_EPSG": calculation.epsg,
                "PO_PGK_X": calculation.pgk_x_northing,
                "PO_PGK_Y": calculation.pgk_y_easting,
                "PO_sigma": calculation.sigma_cm_per_km,
                "PO_skala": calculation.scale_m,
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
        mode_index = self.parameterAsEnum(
            parameters, self.REPAIR_MODE, context
        )
        if mode_index == 0:
            return RepairMode.SOURCE_GEOMETRY
        if mode_index == 1:
            return RepairMode.AUTO_REPAIR
        raise QgsProcessingException(
            self.tr("Nieprawidłowy tryb naprawy geometrii.")
        )

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
        return QCoreApplication.translate(
            "CalculateEgibAreaAlgorithm", message
        )


def _round_m2(value: float) -> float:
    """Round a square-metre output field to its declared precision."""

    return round(value, 2)
