from application.models.semantic import Document

default_document = [Document(text="There is no information.", metadata={"type": "text", "score": 0,"url":"","name":""})]

operator_mapping = {
    'eq':'Equal',
    'gt':'GreaterThan',
    'gte':'GreaterThanEqual',
    'lt':'LessThan',
    'lte':'LessThanEqual'
}

value_types = {
    'text':'valueText',
    'int':'valueInt',
    'number':'valueNumber'
}