from pathlib import Path
from lxml import etree
from .file_import import FileImportError


def validate_xml(xml_path: Path | str, xsd_path: Path | str) -> None:
    """Validate a local XML document against a local XSD schema."""
    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        schema = etree.XMLSchema(etree.parse(str(xsd_path), parser))
        document = etree.parse(str(xml_path), parser)
        schema.assertValid(document)
    except (OSError, etree.LxmlError) as exc:
        raise FileImportError(f"XML schema validation failed: {exc}") from exc
