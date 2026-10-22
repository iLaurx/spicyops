"""PostgreSQL propio del proyecto, solo loopback; no modifica instalaciones globales."""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / '.local'

def binaries():
    supplied = os.environ.get('SPICYOPS_PG_BIN')
    if supplied: return Path(supplied)
    if shutil.which('pg_ctl'): return Path(shutil.which('pg_ctl')).parent
    for version in ('18', '17', '16', '15', '14'):
        path = Path('C:/Program Files/PostgreSQL') / version / 'bin'
        if (path / 'pg_ctl.exe').exists(): return path
    raise SystemExit('No hay PostgreSQL local. Configura SPICYOPS_PG_BIN o PostgreSQL externo mediante PG*.')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['setup', 'start', 'stop', 'status'])
    args = parser.parse_args()
    LOCAL.mkdir(exist_ok=True)
    config = LOCAL / 'settings.json'
    if not config.exists():
        config.write_text(json.dumps({'DJANGO_SECRET_KEY': secrets.token_urlsafe(50), 'DJANGO_DEBUG': '1',
            'PGUSER': 'spicyops', 'PGPASSWORD': secrets.token_urlsafe(32), 'PGHOST': '127.0.0.1',
            'PGPORT': '55432', 'PGDATABASE': 'spicyops'}, indent=2))
    values = json.loads(config.read_text())
    if values['PGHOST'] != '127.0.0.1' or values['PGDATABASE'] != 'spicyops':
        raise SystemExit('Esta utilidad administra únicamente el clúster aislado de loopback.')
    pg = binaries()
    executable = '.exe' if os.name == 'nt' else ''
    def run(name, *parts, check=True, capture=False):
        return subprocess.run([str(pg / (name + executable)), *map(str, parts)], check=check,
                              capture_output=capture, text=True, cwd=ROOT)
    data = LOCAL / 'pgdata'
    if args.action in ('stop', 'status'):
        run('pg_ctl', '-D', data, args.action, check=False)
        return
    if not (data / 'PG_VERSION').exists():
        pwfile = LOCAL / 'init-password.tmp'
        try:
            pwfile.write_text(values['PGPASSWORD'])
            run('initdb', '-D', data, '-U', values['PGUSER'], '--auth=scram-sha-256', '--pwfile', pwfile,
                '--encoding=UTF8', '--locale=C')
        finally:
            pwfile.unlink(missing_ok=True)
    # Configuración solo del clúster de este proyecto; no toca otros servicios.
    conf = data / 'postgresql.conf'
    text = conf.read_text()
    marker = '# SpicyOps local (gestionado por scripts/setup_local.py)'
    text = text.split(marker)[0].rstrip() + '\n' + marker + '\n'
    text += "listen_addresses = '127.0.0.1'\nport = " + str(values['PGPORT']) + "\nmax_connections = 30\nshared_buffers = '32MB'\n"
    conf.write_text(text)
    if run('pg_ctl', '-D', data, 'status', check=False, capture=True).returncode:
        run('pg_ctl', '-D', data, '-l', LOCAL / 'postgres.log', '-o',
            '-h 127.0.0.1 -p ' + str(values['PGPORT']) + ' -c shared_buffers=32MB -c max_connections=30', '-w', 'start')
    if args.action == 'setup':
        with psycopg.connect(dbname='postgres', user=values['PGUSER'], password=values['PGPASSWORD'],
                host='127.0.0.1', port=values['PGPORT'], autocommit=True) as conn:
            # Migrar también un clúster recién creado manualmente con trust, sin exponer la clave.
            conn.execute(sql.SQL('ALTER ROLE {} PASSWORD {}').format(sql.Identifier(values['PGUSER']), sql.Literal(values['PGPASSWORD'])))
            if not conn.execute("SELECT 1 FROM pg_database WHERE datname='spicyops'").fetchone():
                conn.execute('CREATE DATABASE spicyops')
            (data / 'pg_hba.conf').write_text('host all all 127.0.0.1/32 scram-sha-256\nhost all all ::1/128 scram-sha-256\n')
            conn.execute('SELECT pg_reload_conf()')
        print('PostgreSQL aislado preparado en 127.0.0.1:' + str(values['PGPORT']))

if __name__ == '__main__': main()
