import pytest

import db
import solves


@pytest.fixture
def conn(tmp_path):
    path = str(tmp_path / "test.db")
    db.init_db(schemas=[solves.SCHEMA], db_path=path)
    connection = db.get_connection(path)
    yield connection
    connection.close()
