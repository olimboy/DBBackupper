import logging
import re
import shutil
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

    # Executes every Day.
    sender.add_periodic_task(
        crontab(hour='1', minute=0),
        clear.s(),
        name='clear'
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


@celery.task
def clear():
    msg = "Cleared all dumps except last 7 days"
    error_exc = None

    for date_dir in os.listdir(config.BACKUP_DIR):
        try:
            date = datetime.datetime.strptime(date_dir, '%d-%m-%Y')

            # save last 7 days, delete if greater than
            if date.date() < (datetime.datetime.now() - datetime.timedelta(days=7)).date():
                shutil.rmtree(os.path.join(config.BACKUP_DIR, date_dir), ignore_errors=True)

            # remove all files except last one if dir is not today's dir
            elif date.date() != datetime.datetime.today().date():
                for filename in os.listdir(os.path.join(config.BACKUP_DIR, date_dir))[:-1]:
                    os.remove(os.path.join(config.BACKUP_DIR, date_dir, filename))

        except Exception as e:
            msg = '\n\n'.join(('Error', str(e)))

    with Client("my_account",
                config.API_ID,
                config.API_KEY,
                bot_token=config.BOT_TOKEN,
                workdir=config.WORK_DIR) as bot:
        msg = '\n\n'.join((f'#clear\n#{config.PGDATABASE}', f'`{msg}`'))
        bot.send_message(config.RECEIVER_ID, msg, parse_mode=ParseMode.MARKDOWN)


if __name__ == '__main__':
    if '--test' in sys.argv:
        logging.basicConfig(level=logging.INFO)
        if '--backup' in sys.argv:
            backup()
        if '--clear' in sys.argv:
            clear()
