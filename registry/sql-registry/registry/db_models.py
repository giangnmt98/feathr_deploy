from sqlalchemy.orm import declarative_base

Base = declarative_base()

import sqlalchemy as sa
from sqlalchemy import (
    Column,
    PrimaryKeyConstraint,
    String,
)


class Entity(Base):
    """
    DB model for Entity.
    These are recorded in ``entities`` table.
    """

    __tablename__ = "entities"

    entity_id = Column(String(50), nullable=True, primary_key=True)
    """
    entity_id: `String` (limit 50 characters). *Primary Key* for ``tags`` table.
    """
    qualified_name = Column(String(200), nullable=False)
    """
    qualified_name associated with tag: `String` (limit 200 characters). Couldn't be *null*.
    """
    entity_type = Column(String(100), nullable=False)
    """
    entity_type associated with tag: `String` (limit 100 characters). Couldn't be *null*.
    """
    attributes = Column(String(2000), nullable=False) 
    """
    attributes associated with tag: `String` (limit 2000 characters). Couldn't be *null*.
    """

    __table_args__ = (PrimaryKeyConstraint("entity_id", name="entity_id_pk"),)

    def __repr__(self):
        return f"<Entity({self.entity_id}, {self.qualified_name}, {self.entity_type}, {self.attributes})>"
    

class Edge(Base):
    """
    DB model for Edge.
    These are recorded in ``edges`` table.
    """

    __tablename__ = "edges"

    edge_id = Column(String(50), nullable=True, primary_key=True)
    """
    edge_id: `String` (limit 50 characters). *Primary Key* for ``tags`` table.
    """
    from_id = Column(String(50), nullable=False)
    """
    from_id associated with tag: `String` (limit 200 characters). Couldn't be *null*.
    """
    to_id = Column(String(50), nullable=False)
    """
    to_id associated with tag: `String` (limit 100 characters). Couldn't be *null*.
    """
    conn_type = Column(String(50), nullable=False) 
    """
    conn_type associated with tag: `String` (limit 2000 characters). Couldn't be *null*.
    """

    __table_args__ = (PrimaryKeyConstraint("edge_id", name="edge_id_pk"),)

    def __repr__(self):
        return f"<Entity({self.edge_id}, {self.from_id}, {self.to_id}, {self.conn_type})>"

