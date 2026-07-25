"""About dialog presenting release, privacy and authorship information."""

import configparser
from html import escape
from pathlib import Path
from typing import Optional

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .theme import MONOSPACE_FONT_STACK, technical_font, theme_colors


def read_plugin_metadata(plugin_root: Path) -> dict:
    """Read the small public metadata subset shown in the dialog."""

    parser = configparser.ConfigParser()
    metadata_path = plugin_root / "metadata.txt"
    loaded_files = parser.read(metadata_path, encoding="utf-8")
    if not loaded_files or "general" not in parser:
        raise RuntimeError("Nie można odczytać metadanych wtyczki.")

    metadata = parser["general"]
    return {
        "name": metadata["name"],
        "version": metadata["version"],
        "author": metadata["author"],
        "license": "GNU GPL v2",
        "repository": metadata["repository"],
    }


class AboutDialog(QDialog):
    """Show concise, offline information about the installed plugin."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        plugin_root: Optional[Path] = None,
    ) -> None:
        super().__init__(parent)
        self.setFont(technical_font())
        root = plugin_root or Path(__file__).resolve().parents[1]
        metadata = read_plugin_metadata(root)
        colors = theme_colors(self)

        self.setObjectName("aboutDialog")
        self.setWindowTitle(f"O wtyczce — {metadata['name']}")
        self.setWindowIcon(QIcon(str(root / "resources" / "icon.svg")))
        self.setModal(True)
        self.setMinimumWidth(560)
        self.resize(640, 440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(8)
        icon_label = QLabel()
        icon_label.setObjectName("aboutIcon")
        icon_label.setPixmap(self.windowIcon().pixmap(16, 16))
        icon_label.setFixedSize(18, 18)
        header.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(3)
        title_label = QLabel(metadata["name"])
        title_label.setObjectName("aboutTitle")
        version_label = QLabel(f"Wersja {metadata['version']} · QGIS 3.40–3.x")
        version_label.setObjectName("aboutVersion")
        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        title_layout.addStretch(1)
        header.addLayout(title_layout, 1)
        layout.addLayout(header)

        summary = QLabel(
            "Oblicza ustawowe pole działki ewidencyjnej z powierzchniową "
            "poprawką odwzorowawczą w układzie PL-2000."
        )
        summary.setObjectName("aboutSummary")
        summary.setWordWrap(True)
        layout.addWidget(summary)

        privacy_card = QFrame()
        privacy_card.setObjectName("aboutPrivacyCard")
        privacy_layout = QVBoxLayout(privacy_card)
        privacy_layout.setContentsMargins(13, 10, 13, 10)
        privacy_layout.setSpacing(3)
        privacy_title = QLabel("Dane pozostają w QGIS")
        privacy_title.setObjectName("aboutCardTitle")
        privacy_text = QLabel(
            "Wtyczka działa lokalnie, nie łączy się z siecią, nie wymaga "
            "konta i nigdy nie modyfikuje warstwy wejściowej."
        )
        privacy_text.setObjectName("aboutCardText")
        privacy_text.setWordWrap(True)
        privacy_layout.addWidget(privacy_title)
        privacy_layout.addWidget(privacy_text)
        layout.addWidget(privacy_card)

        details = QLabel(
            f"<b>Autor:</b> {escape(metadata['author'])}<br>"
            f"<b>Licencja:</b> {escape(metadata['license'])}<br>"
            f"<b>Repozytorium:</b><br>{escape(metadata['repository'])}"
        )
        details.setObjectName("aboutDetails")
        details.setWordWrap(True)
        layout.addWidget(details)

        disclosure = QLabel(
            "Projekt powstaje z wykorzystaniem podejścia vibe coding. "
            "Zmiany są weryfikowane testami, skanerami bezpieczeństwa "
            "i ręcznym przeglądem."
        )
        disclosure.setObjectName("aboutDisclosure")
        disclosure.setWordWrap(True)
        layout.addWidget(disclosure)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        close_button = QPushButton("Zamknij")
        close_button.setObjectName("aboutCloseButton")
        close_button.setDefault(True)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        self.setStyleSheet(_about_stylesheet(colors))


def _about_stylesheet(colors: dict) -> str:
    return f"""
    QDialog#aboutDialog {{
        background-color: {colors["window"]};
        color: {colors["text"]};
        font-family: {MONOSPACE_FONT_STACK};
        font-size: 9pt;
    }}
    QLabel {{
        background: transparent;
        color: {colors["text"]};
    }}
    QLabel#aboutTitle {{
        font-size: 10.5pt;
        font-weight: 650;
    }}
    QLabel#aboutVersion {{
        color: {colors["muted"]};
        font-size: 9pt;
    }}
    QLabel#aboutSummary {{
        font-size: 9pt;
    }}
    QFrame#aboutPrivacyCard {{
        background-color: {colors["accent_soft"]};
        border: 1px solid {colors["accent"]};
        border-radius: 7px;
    }}
    QLabel#aboutCardTitle {{
        color: {colors["accent"]};
        font-weight: 650;
    }}
    QLabel#aboutDisclosure {{
        color: {colors["muted"]};
        font-size: 8.5pt;
    }}
    QPushButton#aboutCloseButton {{
        color: #ffffff;
        background-color: {colors["accent"]};
        border: 1px solid {colors["accent"]};
        border-radius: 5px;
        min-height: 24px;
        padding: 5px 18px;
        font-weight: 600;
    }}
    QPushButton#aboutCloseButton:hover {{
        background-color: {colors["accent_hover"]};
        border-color: {colors["accent_hover"]};
    }}
    """
