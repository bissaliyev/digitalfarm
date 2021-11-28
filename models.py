import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Status(enum.Enum):
    READY = 1
    SENT = 2

class Count(Base):
    __tablename__ = 'count'
    id = Column(Integer, primary_key=True)
    company = Column("company", String)
    created_date = Column("created_date", DateTime, default=datetime.datetime.utcnow)
    tag_id = Column("tag_id", String)
    length = Column("length", Integer)
    ant1 = Column("ant1", Integer)
    ant2 = Column("ant2", Integer)
    ant3 = Column("ant3", Integer)
    ant4 = Column("ant4", Integer)
    cnt = Column("cnt", Integer)
    rssi = Column("rssi", String)
    weight = Column("weight", Integer)
    status = Column(enum.Enum(Status), default=Status.READY)

    def __init__(self, company, tag_id, length, ant1, ant2, ant3, ant4, cnt, rssi, weight):
        self.company = company
        self.tag_id = tag_id
        self.length = length
        self.ant1 = ant1
        self.ant2 = ant2
        self.ant3 = ant3
        self.ant4 = ant4
        self.cnt = cnt
        self.rssi = rssi
        self.weight = weight

