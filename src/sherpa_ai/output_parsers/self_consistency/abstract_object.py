from typing import Union

from pydantic import BaseModel


class AbstractObject(BaseModel):
    """
    Class representing  an abstract object (an object that represent a set of objects)
    """

    obj_schema: type[BaseModel]
    """
    Schema of the object, used to validate the object.
    """

    obj_dict: dict[str, Union[list, dict]] = {}
    """
    Dictionary representing the abstract object, where each field is mapped to a list or a dictionary.
    If the field is a primitive type, it will be mapped to a list for storing object values.
    If the field is a nested model, it will be mapped to a dictionary for storing object values.
    """  # noqa: E501

    def __init__(self, obj_schema, **kwargs):
        """
        Initialize the AbstractObject with a schema and additional keyword arguments.

        Args:
            obj_schema (type[BaseModel]): The Pydantic model class representing the schema of the object.
            **kwargs: Additional keyword arguments to initialize the object.
        """  # noqa: E501
        super().__init__(obj_schema=obj_schema, **kwargs)
        self.obj_dict = flatten_model_schema(obj_schema)


def flatten_model_schema(cls: type[BaseModel]) -> dict[str, Union[list, dict]]:
    """
    Flatten the schema of a Pydantic model.

    Args:
        cls (type[BaseModel]): The Pydantic model class to flatten.

    Returns:
        dict[str, Union[list, dict]]: A dictionary representing the flattened schema.
            If the field is a primitive type, it will be map to a list for storing object values
            If the field is a nested model, it will be mapped to a dictionary for storing object values.
    """  # noqa: E501

    fields = cls.model_fields

    result = {}
    for field_name, field in fields.items():
        field_type = field.annotation

        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            # If the field is a nested model, map it to a dictionary recursively
            result[field_name] = flatten_model_schema(field_type)
        else:
            # If it's a primitive type, map it to a list for the abstract object
            result[field_name] = []

    return result
