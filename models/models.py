from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date

Base = declarative_base()


class Count(Base):
    __tablename__ = 'count'
    id = Column(Integer, primary_key=True)
    type = Column(String)
    author = Column(String)
    pages = Column(Integer)
    published = Column(Date)

    def __repr__(self):
        return "<Book(title='{}', author='{}', pages={}, published={})>" \
            .format(self.title, self.author, self.pages, self.published)

data_list = {
        "date": strftime("%Y-%m-%d"),
        "company_code": str(name),
        "data": [
            {
                "time": strftime("%H:%M:%S"),
                "tag_id": id_list[0],
                "length": length_list[0],
                "ant1": cnt1_list[0],
                "ant2": cnt2_list[0],
                "ant3": cnt3_list[0],
                "ant4": cnt4_list[0],
                "cnt": str(cnt1_list[0] + cnt2_list[0] + cnt3_list[0] + cnt4_list[0]),
                "RSSI": rssi_list[0]
            }
        ]
    }