from django import db


class OpenAndCloseDbConnection:
    """Make sure to close the db connection after the context manager is done."""
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        db.connections.close_all()

