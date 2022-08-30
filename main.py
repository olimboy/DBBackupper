import logging
import sys

import config
import datetime
import os
import subprocess

from celery import Celery
from celery.schedules import crontab
from pyrogram import Client
from pyrogram.enums import ParseMode

celery = Celery('main', broker=config.REDIS_URL)


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Executes every Hour.
    sender.add_periodic_task(
        crontab(hour='*/1', minute=0),
        backup.s(),
        name='backup'
    )


@celery.task
def backup():
    now = datetime.datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
    today = datetime.datetime.now().strftime('%d-%m-%Y/')
    today_dir = '{}{}'.format(config.BACKUP_DIR, today)
    if not os.path.exists(today_dir):
        os.mkdir(today_dir)
    dump_file_path = '{}{}{}_{}.pgsql'.format(config.BACKUP_DIR, today, config.PGDATABASE, now)
    dump_file_path_gz = '{}{}{}_{}.pgsql.gz'.format(config.BACKUP_DIR, today, config.PGDATABASE, now)
    command_pgsql = 'pg_dump {0} > {1}'.format(config.PGDATABASE, dump_file_path)
    command_gz = 'gzip {}'.format(dump_file_path)
    error_exc = None
    error_msg = None
    try:
        subprocess.run(command_pgsql, shell=True, check=True, capture_output=True)
        subprocess.run(command_gz, shell=True, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        error_msg = '\n\n\n'.join(('Error', str(e), e.stderr.decode('utf8')))
        error_exc = e
        os.system(f'rm {dump_file_path}')
    with Client("my_account",
                config.API_ID,
                config.API_KEY,
                bot_token=config.BOT_TOKEN,
                workdir=config.WORK_DIR) as bot:
        if error_msg and error_exc:
            bot.send_message(config.RECEIVER_ID, f'`{error_msg}`', parse_mode=ParseMode.MARKDOWN)
        else:
            bot.send_document(config.RECEIVER_ID, dump_file_path_gz, caption=f'#{config.PGDATABASE}')


if __name__ == '__main__':
    if '--test' in sys.argv:
        logging.basicConfig(level=logging.INFO)
        backup()
