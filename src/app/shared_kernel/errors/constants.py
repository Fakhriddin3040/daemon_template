from enum import IntEnum, StrEnum


class AppExceptionStatusCodes(IntEnum):
    # ===== VALIDATION =====
    UNIQUE_CONSTRAINT = 200
    DUPLICATED = 201
    REQUIRED_VALUE = 202
    STRING_RANGE_LIMIT_EXCEEDED = 203
    REGEX_NOT_MATCH = 204
    INVALID_TYPE = 205
    NUMERIC_RANGE_LIMIT_EXCEEDED = 206
    LIST_INVALID_RANGE = 207
    VALIDATION_ERROR = 208
    INVALID_VALUE = 209

    # ===== COMMON =====
    OBJECT_NOT_FOUND = 400
    INVALID_INPUT = 403
    NOT_FOUND = 404
    RESOURCE_HAS_DEPENDENCIES = 411

    # ===== UNKNOWN =====
    UNKNOWN_ERROR = 1900

    # ===== EXTERNAL / RUNTIME =====
    DETAILED_ERROR = 10000
    NETWORK_ERROR = 10001
    UNEXPECTED_RESPONSE = 10002
    TIMEOUT = 10003


class AppExceptionMessage(StrEnum):
    NOT_FOUND = "Not found"
    INVALID_VALUE = "Value format is invalid"
    UNIQUE_CONSTRAINT = "Unique constraint violated. One or more constraints violated"
    REQUIRED_VALUE = "Value is required"

    # ===== UNKNOWN =====
    UNKNOWN_ERROR = "Unknown error"

    # ===== COMMON =====
    DETAILED_ERROR = "Detailed error. See details"

    def add_prefix(self, prefix: str) -> str:
        return f"{prefix.capitalize()} {self.value.lower()}"


class AppExceptionDetailPayloadKeys(StrEnum):
    DUPLICATES = "duplicates"
    VALUE = "value"
    VALUES = "values"
    RANGES = "ranges"


class AppExceptionDetailCodes(StrEnum):
    IDENTIFIER_DUPLICATED = "identifier_duplicated"
