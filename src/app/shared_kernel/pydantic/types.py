from pydantic import BaseModel, ConfigDict


class BasePydanticModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)
