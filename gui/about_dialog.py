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
    QLayout,
    QPushButton,
    QScrollArea,
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
        "about": metadata["about"],
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
        self.setWindowTitle(metadata["name"])
        self.setWindowIcon(QIcon(str(root / "resources" / "icon.svg")))
        self.setModal(True)
        self.setMinimumWidth(560)
        self.resize(640, 600)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setObjectName("aboutScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("aboutContent")
        layout = QVBoxLayout(content)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll, 1)
        layout.setContentsMargins(24, 22, 24, 12)
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
        version_label = QLabel(
            f"Wersja {metadata['version']} · QGIS 3.40–3.x / 4.x"
        )
        version_label.setObjectName("aboutVersion")
        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        title_layout.addStretch(1)
        header.addLayout(title_layout, 1)
        layout.addLayout(header)

        summary = QLabel(
            "Oblicza pole działki z poprawką PL-2000 według § 16 ust. 2 "
            "i załącznika nr 3 rozporządzenia w sprawie ewidencji gruntów "
            "i budynków (Dz.U. 2024 poz. 219 ze zm.). Pomaga sprawdzać "
            "powierzchnie działek istniejących i projektowanych. To inny "
            "sposób obliczenia niż natywne pole kartezjańskie i pomiar "
            "geodezyjny QGIS; oba pokazuje dla porównania."
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
            "konta i nie modyfikuje warstwy wejściowej. Korzysta tylko "
            "z bibliotek dostarczanych z QGIS i standardowego Pythona; "
            "nie wymaga instalowania dodatkowych zależności."
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
            "Projekt powstał metodą vibe coding, z pomocą AI. "
            "Autor nie bierze odpowiedzialności za wyniki ani skutki ich "
            "wykorzystania, w zakresie dopuszczonym prawem. "
            "Przed użyciem sprawdź dane, CRS i wynik."
        )
        disclosure.setObjectName("aboutDisclosure")
        disclosure.setWordWrap(True)
        layout.addWidget(disclosure)

        checks = QLabel(
            "Lokalne kontrole według zaleceń QGIS — bez wykrytych problemów:\n"
            "• Bandit: bezpieczeństwo kodu Python.\n"
            "• detect-secrets: hasła, klucze i tokeny.\n"
            "• Flake8: błędy i jakość kodu.\n"
            "• ZIP: zawartość, uprawnienia i struktura paczki.\n"
            "Dodatkowo: Ruff, pip-audit oraz testy obliczeń i integracji.\n"
            "Są to kontrole lokalne, nie certyfikat QGIS."
        )
        checks.setObjectName("aboutChecks")
        checks.setWordWrap(True)
        layout.addWidget(checks)

        english = QLabel(
            "ENGLISH / EN\n\n"
            + metadata["about"].partition("\nENGLISH / EN\n")[2]
        )
        english.setObjectName("aboutEnglish")
        english.setWordWrap(True)
        layout.addWidget(english)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(24, 0, 24, 20)
        button_layout.addStretch(1)
        close_button = QPushButton("Zamknij")
        close_button.setObjectName("aboutCloseButton")
        close_button.setDefault(True)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        outer_layout.addLayout(button_layout)

        self.setStyleSheet(_about_stylesheet(colors))


def _about_stylesheet(colors: dict) -> str:
    return f"""
    QDialog#aboutDialog, QWidget#aboutContent {{
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
