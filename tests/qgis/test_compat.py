from compat import _resolve_field_types, _resolve_qaction, execute_dialog


def test_field_types_use_qmetatype_api_when_available() -> None:
    class ModernFieldTypes:
        Bool = "modern_bool"
        Double = "modern_double"
        Int = "modern_int"
        QString = "modern_string"

    class ModernMetaType:
        Type = ModernFieldTypes

    class LegacyVariant:
        Bool = "legacy_bool"
        Double = "legacy_double"
        Int = "legacy_int"
        String = "legacy_string"

    assert _resolve_field_types(ModernMetaType, LegacyVariant) == (
        "modern_bool",
        "modern_double",
        "modern_int",
        "modern_string",
    )


def test_field_types_fall_back_to_qvariant_api() -> None:
    class LegacyMetaType:
        pass

    class LegacyVariant:
        Bool = "legacy_bool"
        Double = "legacy_double"
        Int = "legacy_int"
        String = "legacy_string"

    assert _resolve_field_types(LegacyMetaType, LegacyVariant) == (
        "legacy_bool",
        "legacy_double",
        "legacy_int",
        "legacy_string",
    )


def test_qaction_resolves_qt6_and_qt5_locations() -> None:
    class Qt6Gui:
        QAction = "qt6_action"

    class Qt5Gui:
        pass

    class Qt5Widgets:
        QAction = "qt5_action"

    assert _resolve_qaction(Qt6Gui, Qt5Widgets) == "qt6_action"
    assert _resolve_qaction(Qt5Gui, Qt5Widgets) == "qt5_action"


def test_dialog_execution_supports_qt6_and_legacy_qt5_names() -> None:
    class Qt6Dialog:
        def exec(self):
            return 6

    class Qt5Dialog:
        def exec_(self):
            return 5

    assert execute_dialog(Qt6Dialog()) == 6
    assert execute_dialog(Qt5Dialog()) == 5
