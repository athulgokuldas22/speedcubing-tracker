import pytest

import db
import solves
import stats


@pytest.fixture
def conn(tmp_path):
    path = str(tmp_path / "test.db")
    db.init_db(schemas=[solves.SCHEMA, stats.SCHEMA], db_path=path)
    connection = db.get_connection(path)
    yield connection
    connection.close()
