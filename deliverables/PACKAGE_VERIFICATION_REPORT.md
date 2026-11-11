# PACKAGE VERIFICATION REPORT

- ZIP: `G:\My Drive\FJCAI2027_PCRR\deliverables\PCRR_FJCAI2027_NGHIEM_THU.zip`
- Bytes: 10920647; MiB: 10.415
- SHA-256: `b0e8db5127ce2b64a9d13577854b08467aa18478a069b7074bb8f2d3cd8499b4`
- Files: 194
- ZIP CRC/integrity: PASS.
- Paths relative, no duplicate member names: PASS.
- Final extraction and every payload SHA-256: PASS (193 files; manifest self-excluded).
- Source tests on relocated extraction: FAIL; ...............FFF...                                                    [100%]
================================== FAILURES ===================================
_____________ test_p4_notebook_respects_configuration[FULL-False] _____________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000024213C8AC50>
tmp_path = WindowsPath('C:/Users/vhn/AppData/Local/Temp/pytest-of-vhn/pytest-47/test_p4_notebook_respects_conf0')
mode = 'FULL', bank = False

    @pytest.mark.parametrize('mode,bank', [('FULL',False),('FULL',True),('PILOT',False)])
    def test_p4_notebook_respects_configuration(monkeypatch,tmp_path,mode,bank):
        notebook=json.loads((Path(__file__).resolve().parents[1]/'notebooks/04_P4_calibration.ipynb').read_text(encoding='utf-8'))
        calls=[]
        def fake_run(command,**kwargs):
            calls.append(command)
            return SimpleNamespace(stdout=f'Experiment: {mode.lower()}-fixture\nP4: PASS\n',check_returncode=lambda:None)
        monkeypatch.setattr(subprocess,'run',fake_run)
        scope={'ROOT':tmp_path,'MODE':mode,'BANK_EXTENSION':bank}
>       exec(''.join(notebook['cells'][5]['source']),scope)

tests\test_notebook_p4.py:17: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

>   ???
E   AttributeError: 'types.SimpleNamespace' object has no attribute 'returncode'

<string>:35: AttributeError
---------------------------- Captured stdout call -----------------------------
Requested mode: FULL; stage: P4; bank extension: False
Experiment: full-fixture
P4: PASS

_____________ test_p4_notebook_respects_configuration[FULL-True] ______________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000024213C88CD0>
tmp_path = WindowsPath('C:/Users/vhn/AppData/Local/Temp/pytest-of-vhn/pytest-47/test_p4_notebook_respects_conf1')
mode = 'FULL', bank = True

    @pytest.mark.parametrize('mode,bank', [('FULL',False),('FULL',True),('PILOT',False)])
    def test_p4_notebook_respects_configuration(monkeypatch,tmp_path,mode,bank):
        notebook=json.loads((Path(__file__).resolve().parents[1]/'notebooks/04_P4_calibration.ipynb').read_text(encoding='utf-8'))
        calls=[]
        def fake_run(command,**kwargs):
            calls.append(command)
            return SimpleNamespace(stdout=f'Experiment: {mode.lower()}-fixture\nP4: PASS\n',check_returncode=lambda:None)
        monkeypatch.setattr(subprocess,'run',fake_run)
        scope={'ROOT':tmp_path,'MODE':mode,'BANK_EXTENSION':bank}
>       exec(''.join(notebook['cells'][5]['source']),scope)

tests\test_notebook_p4.py:17: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

>   ???
E   AttributeError: 'types.SimpleNamespace' object has no attribute 'returncode'

<string>:35: AttributeError
---------------------------- Captured stdout call -----------------------------
Requested mode: FULL; stage: P4; bank extension: True
Experiment: full-fixture
P4: PASS

____________ test_p4_notebook_respects_configuration[PILOT-False] _____________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000024213BC7050>
tmp_path = WindowsPath('C:/Users/vhn/AppData/Local/Temp/pytest-of-vhn/pytest-47/test_p4_notebook_respects_conf2')
mode = 'PILOT', bank = False

    @pytest.mark.parametrize('mode,bank', [('FULL',False),('FULL',True),('PILOT',False)])
    def test_p4_notebook_respects_configuration(monkeypatch,tmp_path,mode,bank):
        notebook=json.loads((Path(__file__).resolve().parents[1]/'notebooks/04_P4_calibration.ipynb').read_text(encoding='utf-8'))
        calls=[]
        def fake_run(command,**kwargs):
            calls.append(command)
            return SimpleNamespace(stdout=f'Experiment: {mode.lower()}-fixture\nP4: PASS\n',check_returncode=lambda:None)
        monkeypatch.setattr(subprocess,'run',fake_run)
        scope={'ROOT':tmp_path,'MODE':mode,'BANK_EXTENSION':bank}
>       exec(''.join(notebook['cells'][5]['source']),scope)

tests\test_notebook_p4.py:17: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

>   ???
E   AttributeError: 'types.SimpleNamespace' object has no attribute 'returncode'

<string>:35: AttributeError
---------------------------- Captured stdout call -----------------------------
Requested mode: PILOT; stage: P4; bank extension: False
Experiment: pilot-fixture
P4: PASS

=========================== short test summary info ===========================
FAILED tests/test_notebook_p4.py::test_p4_notebook_respects_configuration[FULL-False]
FAILED tests/test_notebook_p4.py::test_p4_notebook_respects_configuration[FULL-True]
FAILED tests/test_notebook_p4.py::test_p4_notebook_respects_configuration[PILOT-False]
3 failed, 18 passed, 3 deselected in 4.18s
- Demo in final extraction: PASS.
- Source AST/notebook schema: PASS.
- Research checks: {"freeze_checksum": true, "experiment_id": true, "signature": true, "source_hashes": true, "config": true, "raw_manifest": true, "frozen_artifacts": true, "split_disjointness": true, "450_primary_cells": true, "unique_rows": true, "B_ablations": true, "all_status_pass": true, "development_no_C3": true, "450_prediction_receipts": true, "primary_csv_matches_cache": true, "rows_44550": true, "scorers_11": true, "all_B_scorer_coverage_450": true, "mandatory_metrics_finite": true, "datasets_official_only": true}
- Main folders: 01_TAI_LIEU_NGHIEN_CUU, 02_MA_NGUON, 03_DU_LIEU, 04_KET_QUA_THUC_NGHIEM, 05_BANG_CHUNG_NGHIEM_THU, 06_CHUAN_BI_BAO_VE, DEMO, tools.
- Excluded: Prediction caches đầy đủ (dung lượng lớn, giữ receipt/hash và trích classification); toàn bộ checkpoint trừ demo LR; processed đầy đủ trừ Model-Val demo/corruptor; archive raw trùng dữ liệu; PNG/PDF trùng chọn PNG; cache Python/pytest, .git, môi trường; log/notebook output cá nhân; bảng kết quả experiment cũ để tránh trộn.
- Training, FULL evaluation, retuning: NOT_RUN by instruction.
- Cloud synchronization / Colab / novelty / general effectiveness: NOT_VERIFIED.
- Local staging retained for recovery: `C:\Users\vhn\AppData\Local\PCRR_acceptance\stage_j1s93n5q`.
- Test environment: {'python': '3.11.9', 'numpy': '2.2.6', 'pandas': '2.2.3', 'scipy': '1.15.3', 'scikit-learn': '1.6.1', 'torch': '2.7.1', 'joblib': '1.4.2', 'PyYAML': '6.0.2'}

Không sửa hai experiment nguồn. Mã nghiên cứu byte-identical; notebook chỉ bỏ metadata/output để bảo vệ thông tin cá nhân. Các bảng mới là tổng hợp audit từ evidence đã lưu, không thay số liệu nghiên cứu.
