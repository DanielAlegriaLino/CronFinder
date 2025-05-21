#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Monitor de nuevos procesos Python ejecutados por un usuario específico.
Este script detecta procesos Python iniciados por un usuario dado,
registra los nuevos en un fichero de log con timestamp y los muestra por pantalla.
No requiere módulos externos, sólo estándar de Python 2 y 3.
Parámetros obligatorios: --interval, --user
"""
from __future__ import print_function
import os
import time
import subprocess
import logging
import argparse
try:
    # Python 3
    from datetime import datetime
except ImportError:
    # Python 2 fallback
    from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser(
        description='Monitor procesos Python de un usuario especificado.')
    parser.add_argument('-i', '--interval', type=float, required=True,
                        help='Intervalo de sondeo en segundos (obligatorio)')
    parser.add_argument('-u', '--user', type=str, required=True,
                        help='Usuario cuyos procesos Python monitorizar (obligatorio)')
    parser.add_argument('-d', '--logdir', type=str, default='logs',
                        help='Directorio donde almacenar los logs')
    return parser.parse_args()


def setup_logging(logdir, username):
    if not os.path.isdir(logdir):
        os.makedirs(logdir)
    logfile = os.path.join(logdir, 'procesos_python_{0}.log'.format(username))
    logger = logging.getLogger('monitor_{0}'.format(username))
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(fh)
    return logger


def get_user_python_procs(own_pid, username):
    """
    Retorna conjunto de tuplas (pid_int, cmd_str) de procesos ejecutados por el usuario
    cuyo comando contenga 'python'. Excluye el propio proceso.
    """
    procs = set()
    try:
        output = subprocess.check_output(['ps', '-eo', 'pid,user,cmd'], universal_newlines=True)
    except Exception:
        return procs
    lines = output.strip().split('\n')
    for line in lines[1:]:
        parts = line.strip().split(None, 2)
        if len(parts) < 3:
            continue
        pid_str, user, cmd = parts
        if user != username or 'python' not in cmd.lower():
            continue
        try:
            pid = int(pid_str)
        except ValueError:
            continue
        if pid == own_pid:
            continue
        procs.add((pid, cmd))
    return procs


def main():
    args = parse_args()
    logger = setup_logging(args.logdir, args.user)
    own_pid = os.getpid()

    seen = get_user_python_procs(own_pid, args.user)
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print('[{0}] Monitor iniciado. Procesos Python de "{1}" iniciales: {2}'.format(
        start_time, args.user, len(seen)))

    while True:
        current = get_user_python_procs(own_pid, args.user)
        nuevos = current - seen
        if nuevos:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print('[{0}] === Nuevos procesos Python de "{1}" detectados ==='.format(
                now, args.user))
            for pid, cmd in sorted(nuevos):
                msg = 'PID {0}: {1}'.format(pid, cmd)
                print('[{0}] {1}'.format(now, msg))
                logger.info(msg)
            print('[{0}] ============================================')
        seen = current
        time.sleep(args.interval)


if __name__ == '__main__':
    main()
