"""
Supported column types for SQLAlchemy models
(i.e. for experiment data tables).
"""

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)

TYPE_MAPPING = {
    "INTEGER": Integer,
    "FLOAT": Float,
    "STRING": String(255),
    "TEXT": Text,
    "BOOLEAN": Boolean,
    "DATETIME": DateTime,
    "JSON": JSON,
}
