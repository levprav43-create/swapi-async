from sqlalchemy import Column, String, MetaData
from sqlalchemy.orm import declarative_base

Base = declarative_base()
metadata = MetaData()

class SwapiPeople(Base):
    __tablename__ = 'people'

    id = Column(String, primary_key=True)
    name = Column(String)
    birth_year = Column(String)
    eye_color = Column(String)
    films = Column(String)
    gender = Column(String)
    hair_color = Column(String)
    height = Column(String)
    homeworld = Column(String)
    mass = Column(String)
    skin_color = Column(String)
    starships = Column(String)
    vehicles = Column(String)