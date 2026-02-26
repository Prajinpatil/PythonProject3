from sqlalchemy.orm import Session

from app.database.session import engine, SessionLocal
from app.database.base import Base
from app.models.camera_model import Camera, Zone


def initialize_demo_data():
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    if db.query(Camera).first():
        db.close()
        return

    camera = Camera(
        name="Main Gate Camera",
        location="North Border",
        extra_data={"resolution": "4K"}
    )

    zone = Zone(
        name="Restricted Zone",
        camera=camera,
        zone_data={"radius": 50}
    )

    db.add(camera)
    db.add(zone)
    db.commit()
    db.close()
