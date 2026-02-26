from sqlalchemy import String, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # IMPORTANT:
    # - Python attribute is NOT named `metadata`
    # - Database column can still be named "metadata"
    extra_data: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    zones: Mapped[list["Zone"]] = relationship(
        back_populates="camera",
        cascade="all, delete-orphan"
    )


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    camera_id: Mapped[int] = mapped_column(
        ForeignKey("cameras.id"),
        nullable=False
    )

    camera: Mapped["Camera"] = relationship(
        back_populates="zones"
    )

    zone_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
