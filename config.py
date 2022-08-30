import os

from dotenv import load_dotenv

load_dotenv()

# Start Postgres Environments

PGHOST = os.getenv('PGHOST', 'localhost')
PGPORT = os.getenv('PGPORT', '5432')
PGDATABASE = os.getenv('PGDATABASE', 'postgres')
PGUSER = os.getenv('PGUSER', 'postgres')
PGPASSWORD = os.getenv('PGPASSWORD', '')

os.environ.setdefault('PGHOST', PGHOST)
os.environ.setdefault('PGPORT', PGPORT)
os.environ.setdefault('PGDATABASE', PGDATABASE)
os.environ.setdefault('PGUSER', PGUSER)
os.environ.setdefault('PGPASSWORD', PGPASSWORD)

# End Postgres Environments

BACKUP_DIR = os.getenv('BACKUP_DIR', './')
WORK_DIR = os.path.dirname(os.path.abspath(__file__))

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

API_ID = os.getenv('API_ID')
API_KEY = os.getenv('API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')
RECEIVER_ID = os.getenv('RECEIVER_ID')