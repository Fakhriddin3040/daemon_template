from enum import StrEnum


class ModelFieldsBaseEnum(StrEnum):
    @property
    def as_foreign_key(self) -> str:
        """Return the foreign key field name for the given field."""
        return f"{self.value}_id"

    @staticmethod
    def as_outref() -> str: ...
