from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# -----------------------------------------------------------------------
# PATH SETUP — src/ klasörünü Python path'e ekle
# -----------------------------------------------------------------------
# Bu dosya: SimuTarget/alembic/env.py
# Proje kökü: SimuTarget/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# -----------------------------------------------------------------------
# DATABASE URL — .env dosyasından oku
# -----------------------------------------------------------------------
from dotenv import load_dotenv
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# .env'deki DATABASE_URL'yi alembic config'e aktar
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL ortam değişkeni tanımlı değil. .env dosyanı kontrol et.")

config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -----------------------------------------------------------------------
# METADATA SETUP — tüm modelleri topla
# -----------------------------------------------------------------------
from src.agent_mining.models import Base as MiningBase

# Mevcut uygulama modelleri varsa onları da dahil et
# (src/database/ içindeki Base — yoksa sorun değil)
metadatas = [MiningBase.metadata]

try:
    from src.database.base import Base as AppBase
    metadatas.append(AppBase.metadata)
except ImportError:
    pass

try:
    from src.database.models import Base as AppBase2
    metadatas.append(AppBase2.metadata)
except ImportError:
    pass

target_metadata = metadatas if len(metadatas) > 1 else metadatas[0]

# -----------------------------------------------------------------------
# MIGRATION FONKSİYONLARI (değiştirilmedi)
# -----------------------------------------------------------------------

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()