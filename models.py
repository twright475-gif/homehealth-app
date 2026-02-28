from sqlalchemy import Column, Integer, String, Float, Boolean
from database import Base

class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    nurse_name = Column(String)
    patient_name = Column(String)
    date = Column(String)
    hours = Column(Float)
    mileage = Column(Float)
    notes = Column(String)
    approved = Column(Boolean, default=False)