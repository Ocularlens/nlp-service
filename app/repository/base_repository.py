from sqlalchemy.orm import DeclarativeBase, Session

class BaseRepository:
    def __init__(self, db: Session, model: DeclarativeBase):
        self.db = db
        self.model = model
        
    def create(self, **kwargs):
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance
      
    def get_by_id(self, id):
        return self.db.query(self.model).filter(self.model.id == id).first()
      
    def get_all(self):
        return self.db.query(self.model).all()
      
    def delete(self, id):
        instance = self.get_by_id(id)
        if instance:
            self.db.delete(instance)
            self.db.commit()
            return True
        return False
      
    def update(self, id, **kwargs):
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            self.db.commit()
            self.db.refresh(instance)
            return instance
        return None