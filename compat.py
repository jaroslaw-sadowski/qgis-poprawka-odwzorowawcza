"""Small Qt5/Qt6 compatibility surface shared by QGIS-facing modules."""

from qgis.PyQt.QtCore import QMetaType, QVariant


def _resolve_field_types(qmeta_type: object, qvariant: object) -> tuple:
    """Resolve QgsField types for both the Qt5 and Qt6 API shapes."""

    try:
        field_types = qmeta_type.Type
    except AttributeError:
        return (
            qvariant.Bool,
            qvariant.Double,
            qvariant.Int,
            qvariant.String,
        )
    return (
        field_types.Bool,
        field_types.Double,
        field_types.Int,
        field_types.QString,
    )


(
    FIELD_TYPE_BOOL,
    FIELD_TYPE_DOUBLE,
    FIELD_TYPE_INT,
    FIELD_TYPE_STRING,
) = _resolve_field_types(QMetaType, QVariant)

__all__ = [
    "FIELD_TYPE_BOOL",
    "FIELD_TYPE_DOUBLE",
    "FIELD_TYPE_INT",
    "FIELD_TYPE_STRING",
]
