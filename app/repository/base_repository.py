from sqlalchemy import and_
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
      
    def get_all(self, sort_by=None, sort_order='asc', where=None, page=1, size=10):
        query = self.db.query(self.model)
        if sort_by:
            if sort_order == 'desc':
                query = query.order_by(getattr(self.model, sort_by).desc())
            else:
                query = query.order_by(getattr(self.model, sort_by).asc())
        if where:
            if isinstance(where, list):
                query = query.filter(and_(*where))  # unpack list properly
            else:
                query = query.filter(where)
                
        total = query.count()  # Get total count before pagination    
                
        if page is not None and size is not None:
            query = query.offset((page - 1) * size).limit(size)
        return {
            "totalPages": (total + size - 1) // size,  # Calculate total pages
            "currentPage": page,
            "pageSize": size,
            "totalItems": total,
            self.model.__tablename__: query.all()
        }
      
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