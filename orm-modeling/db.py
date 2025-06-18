from contextlib import contextmanager
from typing import Dict, Any, Generator
from sqlalchemy import create_engine, Engine, text, MetaData
from sqlalchemy.orm import sessionmaker, Session
from .model import Base
from pathlib import Path
import shutil


def create_database_engine(database_url: str = "sqlite:///:memory:", echo: bool = False):
    engine = create_engine(database_url, echo=echo)
    
    if 'sqlite' in database_url:
        _optimize_sqlite(engine)
    
    return engine


def _optimize_sqlite(engine):
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.execute(text("PRAGMA synchronous=NORMAL"))
        conn.execute(text("PRAGMA temp_store=MEMORY"))
        conn.execute(text("PRAGMA cache_size=-64000"))
        conn.commit()


def create_session_factory(engine):
    return sessionmaker(bind=engine)


def create_tables(engine):
    Base.metadata.create_all(engine)


class DatabaseManager:
    def __init__(self, database_url: str = "sqlite:///:memory:", echo: bool = False):
        self.database_url = database_url
        self.echo = echo
        self.engine: Engine | None = None
        self.SessionLocal = None

    def initialize(self) -> Engine:
        self.engine = create_engine(self.database_url, echo=self.echo)
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        if 'sqlite' in self.database_url:
            _optimize_sqlite(self.engine)
            
        return self.engine

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save(self, file_path: Path) -> bool:
        if not self.engine:
            raise RuntimeError("Database not initialized. Call initialize() first.")
            
        if 'sqlite' not in self.database_url or self.database_url == "sqlite:///:memory:":
            return self._save_memory_to_file(file_path)
        else:
            source_path = Path(self.database_url.replace("sqlite:///", ""))
            try:
                shutil.copy2(source_path, file_path)
                return True
            except Exception:
                return False

    def _save_memory_to_file(self, file_path: Path) -> bool:
        try:
            if not self.engine:
                return False
                
            file_engine = create_engine(f"sqlite:///{file_path}", echo=self.echo)
            if 'sqlite' in str(file_path):
                _optimize_sqlite(file_engine)
            Base.metadata.create_all(file_engine)
            
            with self.engine.connect() as source_conn:
                with file_engine.connect() as dest_conn:
                    tables = Base.metadata.tables.keys()
                    
                    for table_name in tables:
                        rows = source_conn.execute(text(f"SELECT * FROM {table_name}")).fetchall()
                        if rows:
                            columns = list(rows[0]._mapping.keys())
                            placeholders = ', '.join(['?' for _ in columns])
                            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                            
                            for row in rows:
                                dest_conn.execute(text(insert_sql), list(row))
                    
                    dest_conn.commit()
            
            file_engine.dispose()
            return True
            
        except Exception:
            return False

    def load(self, file_path: Path) -> bool:
        if not file_path.exists():
            return False
            
        try:
            if self.database_url == "sqlite:///:memory:":
                return self._load_file_to_memory(file_path)
            else:
                target_path = Path(self.database_url.replace("sqlite:///", ""))
                shutil.copy2(file_path, target_path)
                
                if self.engine:
                    self.engine.dispose()
                self.initialize()
                
                return True
                
        except Exception:
            return False

    def _load_file_to_memory(self, file_path: Path) -> bool:
        try:
            if not self.engine:
                self.initialize()
            
            if not self.engine:
                return False
                
            file_engine = create_engine(f"sqlite:///{file_path}", echo=self.echo)
            
            with self.engine.connect() as dest_conn:
                tables = Base.metadata.tables.keys()
                
                for table_name in tables:
                    dest_conn.execute(text(f"DELETE FROM {table_name}"))
                
                with file_engine.connect() as source_conn:
                    for table_name in tables:
                        rows = source_conn.execute(text(f"SELECT * FROM {table_name}")).fetchall()
                        if rows:
                            columns = list(rows[0]._mapping.keys())
                            placeholders = ', '.join(['?' for _ in columns])
                            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                            
                            for row in rows:
                                dest_conn.execute(text(insert_sql), list(row))
                
                dest_conn.commit()
            
            file_engine.dispose()
            return True
            
        except Exception:
            return False

    def get_info(self) -> Dict[str, Any]:
        if not self.engine:
            return {"status": "not_initialized"}
            
        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = [row[0] for row in result.fetchall()]
                
                info = {
                    "status": "initialized", 
                    "database_url": self.database_url,
                    "tables": tables,
                    "echo": self.echo
                }
                
                for table in tables:
                    if not table.startswith('sqlite_'):
                        try:
                            count_result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                            info[f"{table}_count"] = count_result.scalar()
                        except:
                            info[f"{table}_count"] = "error"
                
                return info
                
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def close(self):
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None
