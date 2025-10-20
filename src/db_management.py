from sqlalchemy import create_engine, text


class TrainsDB:
    
    def __init__(self, db_url):
        
        self.engine = create_engine(DB_URL)
    
    