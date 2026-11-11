"""Regenerate execution notebooks without touching the original downloader."""
from pathlib import Path
import nbformat as nbf

root=Path(__file__).resolve().parents[1]
titles=['data_preprocessing','baseline_training','corruption_cpcr','calibration','final_evaluation']
for i,title in enumerate(titles,1):
    nb=nbf.v4.new_notebook()
    nb.cells=[nbf.v4.new_markdown_cell(f'''# P{i} — {title.replace('_',' ').title()}

PCRR: run stages in order, with the same MODE and BANK_EXTENSION. No P0.
Start SMOKE, then PILOT, then FULL. P5 opens Test **only in FULL after P4 freeze**.
SMOKE/PILOT P5 exports development results; it does not mark P5 PASS.
Read `README.md`, `reports/METHODOLOGY.md` and the generated acceptance report.
Data and checkpoints remain on Drive. Restart runtime after first dependency installation.
'''),nbf.v4.new_code_cell('''from google.colab import drive
from pathlib import Path
drive.mount('/content/drive')
ROOT = Path('/content/drive/MyDrive/FJCAI2027_PCRR').resolve()
assert (ROOT / 'data/raw/dataset_manifest.json').is_file(), 'Missing existing project/manifest'
assert (ROOT / 'run_all.py').is_file(), 'Wait for project files to sync to Drive'
probe = ROOT / '.colab_write_probe'
probe.write_text('ok'); probe.unlink()
print(ROOT)
'''),nbf.v4.new_code_cell('''import subprocess, sys
subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(ROOT/'requirements.txt')], check=True)
print('After initial install, restart runtime, then rerun mount and remaining cells.')
'''),nbf.v4.new_code_cell('''MODE = 'SMOKE'  # SMOKE -> PILOT -> FULL
BANK_EXTENSION = False  # Set True consistently for all FULL stages to include Bank
import os
os.environ['PCRR_ROOT'] = str(ROOT)
os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
'''),nbf.v4.new_code_cell('''import subprocess, sys
subprocess.run([sys.executable, '-m', 'pytest', '-q', str(ROOT/'tests/test_core.py')], cwd=ROOT, check=True)
'''),nbf.v4.new_code_cell(f'''command = [sys.executable, str(ROOT/'run_all.py'), '--root', str(ROOT), '--mode', MODE, '--stage', 'P{i}']
if BANK_EXTENSION: command.append('--bank')
result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
print(result.stdout)
result.check_returncode()
'''),nbf.v4.new_code_cell(f'''from IPython.display import Markdown, display
report = ROOT/'reports/P{i}_ACCEPTANCE.md'
if report.exists(): display(Markdown(report.read_text()))
print('Detailed artifacts and status are under results/<experiment-id>/ and reports/<experiment-id>/.')
''')]
    nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'},'colab':{'name':f'{i:02d}_P{i}_{title}.ipynb'}}
    nbf.validate(nb)
    dest=root/'notebooks'/f'{i:02d}_P{i}_{title}.ipynb'; dest.parent.mkdir(exist_ok=True)
    nbf.write(nb,dest)
    print(dest)
