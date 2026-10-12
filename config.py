"""FHGL only. Configure BOT_TOKEN and SUPER_ADMINS via Railway Variables."""
import os
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
SUPER_ADMINS = [int(x) for x in os.getenv('SUPER_ADMINS', '8222147822').replace('，', ',').split(',') if x.strip().isdigit()]
DATA_DIR = os.getenv('FHGL_DATA_DIR', '.').strip() or '.'
