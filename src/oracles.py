"""Expectation oracles computed from the AWS documentation, not from
the emulator. If an oracle and the emulator disagree, the emulator
is what gets scored down, never the oracle.
"""

import hashlib
import struct


def md5_hex_of_body(body):
    if isinstance(body, str):
        body = body.encode("utf-8")
    return hashlib.md5(body).hexdigest()


def md5_of_message_attributes(attributes):
    """The documented SQS MD5 of message attributes.

    Source: Amazon SQS Developer Guide, message attributes, MD5
    checksum section. For each attribute in name order, append:
    the 4-byte big-endian length and bytes of the attribute name;
    the 4-byte length and bytes of the data type; one transport
    byte (1 when the value travels as a string, which covers the
    String and Number types; 2 for Binary); the 4-byte length and
    bytes of the value (raw bytes for Binary, UTF-8 of the string
    form otherwise). The checksum is the MD5 of the concatenation.
    """
    buf = bytearray()
    for name in sorted(attributes):
        attr = attributes[name]
        data_type = attr["DataType"]
        if "StringValue" in attr:
            value_bytes = attr["StringValue"].encode("utf-8")
            transport = 1
        else:
            value_bytes = attr["BinaryValue"]
            transport = 2
        for part in (name.encode("utf-8"), data_type.encode("utf-8")):
            buf += struct.pack(">I", len(part))
            buf += part
        buf.append(transport)
        buf += struct.pack(">I", len(value_bytes))
        buf += value_bytes
    return hashlib.md5(bytes(buf)).hexdigest()
