from typing import Union, get_origin, get_args
from pydantic import BaseModel


class ObjectAggregator(BaseModel):
    """
    Class representing an aggregation of objects by capture their attributes values 
    as a list
    """

    obj_schema: type[BaseModel]
    """
    Schema of the object, used to validate the object.
    """

    value_weight_map: dict[str, Union[dict, float]] = {}
    """
    Dictionary mapping each field to a dictionary of values and their weights.
    If the field is a primitive type, it will be mapped to a dictionary with values as keys and their weights as values.
    If the field is a nested model, it will be mapped to a dictionary for storing object values. The default weight is 1.0.
    """  # noqa: E501

    obj_dict: dict[str, Union[list, dict]] = {}
    """
    Dictionary representing the object aggregator, where each field is mapped to a list or a dictionary.
    If the field is a primitive type, it will be mapped to a list for storing object values.
    If the field is a nested model, it will be mapped to a dictionary for storing object values.
    """  # noqa: E501

    def __init__(self, obj_schema, **kwargs):
        """
        Initialize the ObjectAggregator with a schema and additional keyword arguments.

        Args:
            obj_schema (type[BaseModel]): The Pydantic model class representing the schema of the object.
        """  # noqa: E501
        super().__init__(obj_schema=obj_schema, **kwargs)
        self.obj_dict = flatten_model_schema(obj_schema)

    def add_object(self, obj: BaseModel):
        """
        Add an object to the aggregation of objects.

        Args:
            obj (BaseModel): The object to add, must conform to the schema defined by obj_schema.
        """  # noqa: E501

        def add_to_dict(obj_dict: dict[str, Union[list, dict]], dict_to_add: dict):
            """
            Recursively add the object dictionary to a dictionary.
            Args:
                obj_dict (dict[str, Union[list, dict]]): The abstract object's dictionary.
                dict_to_add (dict): The dictionary representation of the object to add.
            """  # noqa: E501
            for key, value in dict_to_add.items():
                if key in obj_dict:
                    if isinstance(obj_dict[key], list):
                        # If the field is a list, append the value
                        obj_dict[key].append(value)
                    else:
                        # If the field is a dictionary, recursively add the value
                        add_to_dict(obj_dict[key], value)
                else:
                    # Honest this should not happen since the schema is checked
                    raise KeyError(
                        f"Field '{key}' not found in the abstract object's schema."
                    )

        if not isinstance(obj, self.obj_schema):
            raise ValueError(f"Object must be of type {self.obj_schema.__name__}")

        dict_to_add = obj.model_dump()
        add_to_dict(self.obj_dict, dict_to_add)


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

        # Check if it's a list type
        if get_origin(field_type) is list or field_type == list:
            # For list fields, we'll store lists of lists (each object's list becomes one item)
            result[field_name] = []
        elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
            # If the field is a nested model, map it to a dictionary recursively
            result[field_name] = flatten_model_schema(field_type)
        else:
            # If it's a primitive type, map it to a list for the abstract object
            result[field_name] = []

    return result
