from compat import _resolve_field_types


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
