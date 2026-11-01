import runpy
import sys

from bootstrap import ROOT


def main():
    commands = {path.stem:path for path in (ROOT/'scripts').glob('*.py') if not path.name.startswith('_')}
    if len(sys.argv)<2 or sys.argv[1] in {'--help','-h'}:
        print('Usage: python manage.py COMMAND [options]')
        print('Commands:', ', '.join(sorted(commands)))
        return
    command = sys.argv[1]
    if command not in commands:
        raise SystemExit('Unknown command. Use python manage.py --help.')
    sys.argv = [str(commands[command]),*sys.argv[2:]]
    runpy.run_path(str(commands[command]),run_name='__main__')


if __name__=='__main__':
    main()
