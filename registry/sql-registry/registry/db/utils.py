import logging
import os
import time
from contextlib import contextmanager

import sqlalchemy
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import sql
# We need to import sqlalchemy.pool to convert poolclass string to class object
from sqlalchemy.pool import (
    AssertionPool,
    AsyncAdaptedQueuePool,
    FallbackAsyncAdaptedQueuePool,
    NullPool,
    QueuePool,
    SingletonThreadPool,
    StaticPool,
)

from registry.environment_variables import (
    FEATHRUI_SQLALCHEMYSTORE_ECHO,
    FEATHRUI_SQLALCHEMYSTORE_MAX_OVERFLOW,
    FEATHRUI_SQLALCHEMYSTORE_POOL_RECYCLE,
    FEATHRUI_SQLALCHEMYSTORE_POOL_SIZE,
    FEATHRUI_SQLALCHEMYSTORE_POOLCLASS,
)


_logger = logging.getLogger(__name__)

MAX_RETRY_COUNT = 10

POSTGRES = "postgresql"
MYSQL = "mysql"
SQLITE = "sqlite"
MSSQL = "mssql"

DATABASE_ENGINES = [POSTGRES, MYSQL, SQLITE, MSSQL]


def _get_package_dir():
    """Returns directory containing MLflow python package."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(current_dir, os.pardir, os.pardir))


def _get_latest_schema_revision():
    """Get latest schema revision as a string."""
    # We aren't executing any commands against a DB, so we leave the DB URL unspecified
    config = _get_alembic_config(db_url="")
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    if len(heads) != 1:
        raise Exception(
            f"Migration script directory was in unexpected state. Got {len(heads)} head "
            f"database versions but expected only 1. Found versions: {heads}"
        )
    return heads[0]


def _verify_schema(engine):
    head_revision = _get_latest_schema_revision()
    current_rev = _get_schema_version(engine)
    if current_rev != head_revision:
        raise Exception(
            f"Detected out-of-date database schema (found version {current_rev}, "
            f"but expected {head_revision}). Take a backup of your database, then run "
            "'mlflow db upgrade <database_uri>' "
            "to migrate your database to the latest schema. NOTE: schema migration may "
            "result in database downtime - please consult your database's documentation for "
            "more detail."
        )


def _get_managed_session_maker(SessionMaker, db_type):
    """
    Creates a factory for producing exception-safe SQLAlchemy sessions that are made available
    using a context manager. Any session produced by this factory is automatically committed
    if no exceptions are encountered within its associated context. If an exception is
    encountered, the session is rolled back. Finally, any session produced by this factory is
    automatically closed when the session's associated context is exited.
    """

    @contextmanager
    def make_managed_session():
        """Provide a transactional scope around a series of operations."""
        with SessionMaker() as session:
            try:
                if db_type == SQLITE:
                    session.execute(sql.text("PRAGMA foreign_keys = ON;"))
                    session.execute(sql.text("PRAGMA busy_timeout = 20000;"))
                    session.execute(sql.text("PRAGMA case_sensitive_like = true;"))
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            except sqlalchemy.exc.OperationalError as e:
                session.rollback()
                _logger.exception(
                    "SQLAlchemy database error. The following exception is caught.\n%s",
                    e,
                )
                raise Exception(e)
            except sqlalchemy.exc.SQLAlchemyError as e:
                session.rollback()
                raise Exception(e)
            except Exception as e:
                session.rollback()
                raise Exception(e)

    return make_managed_session


def _get_alembic_config(db_url, alembic_dir=None):
    """
    Constructs an alembic Config object referencing the specified database and migration script
    directory.

    Args:
        db_url: Database URL, like sqlite:///<absolute-path-to-local-db-file>. See
            https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls for a full list of
            valid database URLs.
        alembic_dir: Path to migration script directory. Uses canonical migration script
            directory under mlflow/alembic if unspecified. TODO: remove this argument in MLflow 1.1,
            as it's only used to run special migrations for pre-1.0 users to remove duplicate
            constraint names.
    """
    from alembic.config import Config

    final_alembic_dir = (
        os.path.join(_get_package_dir(), "store", "db_migrations")
        if alembic_dir is None
        else alembic_dir
    )
    # Escape any '%' that appears in a db_url. This could be in a password,
    # url, or anything that is part of a potentially complex database url
    db_url = db_url.replace("%", "%%")
    config = Config(os.path.join(final_alembic_dir, "alembic.ini"))
    config.set_main_option("script_location", final_alembic_dir)
    config.set_main_option("sqlalchemy.url", db_url)
    return config


def _upgrade_db(engine):
    """
    Upgrade the schema of an MLflow tracking database to the latest supported version.
    Note that schema migrations can be slow and are not guaranteed to be transactional -
    we recommend taking a backup of your database before running migrations.

    Args:
        url: Database URL, like sqlite:///<absolute-path-to-local-db-file>. See
            https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls for a full list of
            valid database URLs.
    """
    # alembic adds significant import time, so we import it lazily
    from alembic import command

    db_url = str(engine.url)
    _logger.info("Updating database tables")
    config = _get_alembic_config(db_url)
    # Initialize a shared connection to be used for the database upgrade, ensuring that
    # any connection-dependent state (e.g., the state of an in-memory database) is preserved
    # for reference by the upgrade routine. For more information, see
    # https://alembic.sqlalchemy.org/en/latest/cookbook.html#sharing-a-
    # connection-with-a-series-of-migration-commands-and-environments
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "heads")


def _get_schema_version(engine):
    with engine.connect() as connection:
        mc = MigrationContext.configure(connection)
        return mc.get_current_revision()


def create_sqlalchemy_engine_with_retry(db_uri):
    attempts = 0
    while True:
        attempts += 1
        engine = create_sqlalchemy_engine(db_uri)
        try:
            sqlalchemy.inspect(engine)
            return engine
        except Exception as e:
            if attempts < MAX_RETRY_COUNT:
                sleep_duration = 0.1 * ((2**attempts) - 1)
                _logger.warning(
                    "SQLAlchemy engine could not be created. The following exception is caught.\n"
                    "%s\nOperation will be retried in %.1f seconds",
                    e,
                    sleep_duration,
                )
                time.sleep(sleep_duration)
                continue
            raise


def create_sqlalchemy_engine(db_uri):
    pool_size = FEATHRUI_SQLALCHEMYSTORE_POOL_SIZE.get()
    pool_max_overflow = FEATHRUI_SQLALCHEMYSTORE_MAX_OVERFLOW.get()
    pool_recycle = FEATHRUI_SQLALCHEMYSTORE_POOL_RECYCLE.get()
    echo = FEATHRUI_SQLALCHEMYSTORE_ECHO.get()
    poolclass = FEATHRUI_SQLALCHEMYSTORE_POOLCLASS.get()
    pool_kwargs = {}
    # Send argument only if they have been injected.
    # Some engine does not support them (for example sqllite)
    if pool_size:
        pool_kwargs["pool_size"] = pool_size
    if pool_max_overflow:
        pool_kwargs["max_overflow"] = pool_max_overflow
    if pool_recycle:
        pool_kwargs["pool_recycle"] = pool_recycle
    if echo:
        pool_kwargs["echo"] = echo
    if poolclass:
        pool_class_map = {
            "AssertionPool": AssertionPool,
            "AsyncAdaptedQueuePool": AsyncAdaptedQueuePool,
            "FallbackAsyncAdaptedQueuePool": FallbackAsyncAdaptedQueuePool,
            "NullPool": NullPool,
            "QueuePool": QueuePool,
            "SingletonThreadPool": SingletonThreadPool,
            "StaticPool": StaticPool,
        }
        if poolclass not in pool_class_map:
            list_str = " ".join(pool_class_map.keys())
            err_str = (
                f"Invalid poolclass parameter: {poolclass}. Set environment variable "
                f"poolclass to empty or one of the following values: {list_str}"
            )
            _logger.warning(err_str)
            raise ValueError(err_str)
        pool_kwargs["poolclass"] = pool_class_map[poolclass]
    if pool_kwargs:
        _logger.info("Create SQLAlchemy engine with pool options %s", pool_kwargs)
    return sqlalchemy.create_engine(db_uri, pool_pre_ping=True, **pool_kwargs)


def extract_db_type_from_uri(db_uri):
    """
    Parse the specified DB URI to extract the database type. Confirm the database type is
    supported. If a driver is specified, confirm it passes a plausible regex.
    """
    _INVALID_DB_URI_MSG = (
    "Please refer to https://mlflow.org/docs/latest/tracking.html#storage for "
    "format specifications."
    )
    import urllib.parse
    scheme = urllib.parse.urlparse(db_uri).scheme
    scheme_plus_count = scheme.count("+")

    if scheme_plus_count == 0:
        db_type = scheme
    elif scheme_plus_count == 1:
        db_type, _ = scheme.split("+")
    else:
        error_msg = f"Invalid database URI: '{db_uri}'. {_INVALID_DB_URI_MSG}"
        raise Exception(error_msg)

    _validate_db_type_string(db_type)

    return db_type

def _validate_db_type_string(db_type):
    """validates db_type parsed from DB URI is supported"""
    _UNSUPPORTED_DB_TYPE_MSG = "Supported database engines are {%s}" % ", ".join(DATABASE_ENGINES)

    if db_type not in DATABASE_ENGINES:
        error_msg = f"Invalid database engine: '{db_type}'. '{_UNSUPPORTED_DB_TYPE_MSG}'"
        raise Exception(error_msg)
    
