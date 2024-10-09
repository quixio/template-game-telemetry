from typing import Callable, Union, Optional, Any
from lxml import etree
import dicttoxml
import xmltodict

from quixstreams.models.serializers.base import Serializer, Deserializer, SerializationContext
from quixstreams.models.serializers.exceptions import SerializationError

__all__ = ("XMLSerializer", "XMLDeserializer")


def default_dumps(value):
    return dicttoxml.dicttoxml(value, custom_root='root', attr_type=False)


def default_loads(value):
    if isinstance(value, bytes):
        value = value.decode('utf-8')
    data = xmltodict.parse(value)
    # If 'root' is the only key, return its value directly
    if 'root' in data and len(data) == 1:
        return data['root']
    return data


class XMLSerializer(Serializer):
    def __init__(
        self,
        dumps: Callable[[Any], Union[str, bytes]] = default_dumps,
        schema: Optional[str] = None,
        validator: Optional[etree.XMLSchema] = None,
    ):
        """
        Serializer that returns data in XML format.
        :param dumps: a function to serialize objects to XML.
            Default - uses dicttoxml to convert dictionaries to XML strings.
        :param schema: An XML Schema definition (XSD) as a string used to validate the data.
            Default - `None`
        :param validator: An lxml.etree.XMLSchema validator used to validate the data. Takes precedence over the schema.
            Default - `None`
        """
        super().__init__()
        self._dumps = dumps
        self._validator = validator

        if schema and not validator:
            xmlschema_doc = etree.fromstring(schema)
            self._validator = etree.XMLSchema(xmlschema_doc)

    def __call__(self, value: Any, ctx: SerializationContext) -> Union[str, bytes]:
        return self._to_xml(value)

    def _to_xml(self, value: Any):
        try:
            xml_bytes = self._dumps(value)
        except (ValueError, TypeError) as exc:
            raise SerializationError(str(exc)) from exc

        if self._validator:
            try:
                xml_doc = etree.fromstring(xml_bytes)
                self._validator.assertValid(xml_doc)
            except etree.DocumentInvalid as exc:
                raise SerializationError(str(exc)) from exc

        return xml_bytes


class XMLDeserializer(Deserializer):
    def __init__(
        self,
        loads: Callable[[Union[bytes, bytearray]], Any] = default_loads,
        schema: Optional[str] = None,
        validator: Optional[etree.XMLSchema] = None,
    ):
        """
        Deserializer that parses data from XML.

        :param loads: function to parse XML from bytes.
            Default - uses xmltodict to parse XML strings to dictionaries.
        :param schema: An XML Schema definition (XSD) as a string used to validate the data.
            Default - `None`
        :param validator: An lxml.etree.XMLSchema validator used to validate the data. Takes precedence over the schema.
            Default - `None`
        """

        super().__init__()
        self._loads = loads
        self._validator = validator

        if schema and not validator:
            xmlschema_doc = etree.fromstring(schema)
            self._validator = etree.XMLSchema(xmlschema_doc)

    def __call__(
        self, value: bytes, ctx: SerializationContext
    ) -> Any:
        if self._validator:
            try:
                xml_doc = etree.fromstring(value)
                self._validator.assertValid(xml_doc)
            except etree.DocumentInvalid as exc:
                raise SerializationError(str(exc)) from exc

        try:
            data = self._loads(value)
        except (ValueError, TypeError) as exc:
            raise SerializationError(str(exc)) from exc

        return data