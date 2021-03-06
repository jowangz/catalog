from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from flask import session as login_session


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(500))


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
              'name': self.name,
              'id': self.id,
                }


class Item(Base):
    __tablename__ = 'item'

    name = Column(String(100), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(500))
    picture = Column(String(500))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
           'name': self.name,
           'description': self.description,
           'picture': self.picture,
           'id': self.id,
                }

if __name__ == '__main__':
    engine = create_engine('sqlite:///categoryitemwithuserandpicture.db')
    Base.metadata.create_all(engine)

    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    session.add(Category(name="Soccer"))
    session.add(Category(name="Basketball"))
    session.add(Category(name="Baseball"))

    session.commit()
