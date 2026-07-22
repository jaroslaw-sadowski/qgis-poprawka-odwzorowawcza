import pytest
from qgis.core import QgsApplication


@pytest.fixture(scope="session", autouse=True)
def qgis_application():
    existing_application = QgsApplication.instance()
    owns_application = existing_application is None
    application = existing_application

    if owns_application:
        QgsApplication.setPrefixPath("/usr", True)
        application = QgsApplication([], False)
        application.initQgis()

    yield application

    if owns_application:
        application.exitQgis()
