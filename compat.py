"""Small Qt5/Qt6 compatibility surface shared by QGIS-facing modules."""

from qgis.PyQt import QtGui, QtWidgets
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


def _resolve_qaction(qt_gui: object, qt_widgets: object) -> object:
    """Return QAction from its Qt6 or Qt5 module location."""

    action_class = getattr(qt_gui, "QAction", None)
    if action_class is not None:
        return action_class
    return qt_widgets.QAction


def execute_dialog(dialog: object) -> int:
    """Execute a dialog with the Qt6 or legacy Qt5 method name."""

    executor = getattr(dialog, "exec", None)
    if executor is None:
        executor = dialog.exec_
    return executor()


(
    FIELD_TYPE_BOOL,
    FIELD_TYPE_DOUBLE,
    FIELD_TYPE_INT,
    FIELD_TYPE_STRING,
) = _resolve_field_types(QMetaType, QVariant)
QAction = _resolve_qaction(QtGui, QtWidgets)

__all__ = [
    "QAction",
    "FIELD_TYPE_BOOL",
    "FIELD_TYPE_DOUBLE",
    "FIELD_TYPE_INT",
    "FIELD_TYPE_STRING",
    "execute_dialog",
]
