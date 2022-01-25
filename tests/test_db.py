from sqlalchemy import create_engine


def test_sqlalchemy():
    assert create_engine('mysql+pymysql://wp:wp@127.0.0.1/wp')
