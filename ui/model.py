from typing import Optional, Any
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from geoalchemy2 import Geometry

class Base(DeclarativeBase):
    ...

class SpatialRecord(Base):
    __tablename__ = "spatial_elements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    geom: Mapped[Geometry] = mapped_column(
            Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
            nullable=False
        )
    
    def __repr__(self) -> str:
        return f"<SpatialRecord(id={self.id}, geom={self.geom})>"

