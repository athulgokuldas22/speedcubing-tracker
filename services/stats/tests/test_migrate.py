from app.migrate import MIGRATIONS_DIR, split_batches


def test_split_batches_splits_on_go_lines():
    sql = "CREATE TABLE a (id INT);\nGO\nALTER TABLE a ADD b INT;\n  go  \nUPDATE a SET b = 1;\n"
    assert split_batches(sql) == [
        "CREATE TABLE a (id INT);\n",
        "\nALTER TABLE a ADD b INT;\n",
        "\nUPDATE a SET b = 1;\n",
    ]


def test_split_batches_ignores_go_inside_a_line_and_empty_batches():
    assert split_batches("SELECT 'GO' AS word;\nGO\n\nGO\n") == ["SELECT 'GO' AS word;\n"]


def test_migration_files_are_numbered_and_start_at_001():
    names = sorted(p.name for p in MIGRATIONS_DIR.glob("*.sql"))
    assert names[0] == "001_init.sql"
    assert all(name[:3].isdigit() and name[3] == "_" for name in names)
