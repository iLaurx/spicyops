from pathlib import Path
import argparse
import subprocess
import sys
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from portal.version import VERSION
parser = argparse.ArgumentParser()
parser.add_argument('--dist-dir', default=f'dist/SpicyOps-{VERSION}-Windows')
parser.add_argument('--work-dir', default=f'build/release-{VERSION}')
args = parser.parse_args()
icon = Image.new('RGBA',(256,256),(0,0,0,0))
draw = ImageDraw.Draw(icon)
draw.rounded_rectangle((0,0,255,255),radius=70,fill='#18213d')
draw.polygon([(147,48),(76,141),(128,141),(109,209),(187,101),(128,101)],fill='#6fc0ba')
icon.save(root/'portal/static/portal/app.ico',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--distpath',args.dist_dir,
    '--workpath',args.work_dir,'SpicyOps.spec'],cwd=root,check=True)
