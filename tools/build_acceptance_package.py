"""Build one acceptance ZIP from immutable experiment evidence. No training/Test run."""
import argparse,ast,hashlib,json,os,re,shutil,subprocess,sys,tempfile,zipfile,time
from pathlib import Path
import pandas as pd
from acceptance_documents import write_documents,write_defense,table
ID='full-62500e11e892b899'; OLD='full-37245e523b162876'
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser();parser.add_argument('--audit',type=Path,default=ROOT/'deliverables/acceptance_audit_evidence.json');args=parser.parse_args()
    out=ROOT/'results'/ID
    required=['summary.csv','per_seed_results.csv','metrics_by_corruption.csv','ablation_results.csv','statistical_summary.csv','scientific_report.md','parameter_search.csv']
    for name in required:
        assert (out/name).is_file() and (out/name).stat().st_size>0,name
        if name.endswith('.csv'):assert len(pd.read_csv(out/name))>0,name
    local=Path(os.environ.get('LOCALAPPDATA',tempfile.gettempdir()))/'PCRR_acceptance'
    local.mkdir(exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='stage_',dir=local)); print('STAGING',stage,flush=True)
    sources={}; redactions=[]
    def cp(src,dst):
        src=Path(src);target=stage/dst;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
        sources[dst]={'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src),'packaged_sha256':sha(target)}
    for folder in ['src','configs','scripts','tests','notebooks']:
        for p in (ROOT/folder).rglob('*'):
            if not p.is_file() or any(x.startswith('.') or x=='__pycache__' for x in p.relative_to(ROOT).parts) or p.suffix not in ['.py','.yaml','.ipynb']:continue
            dest='02_MA_NGUON/'+p.relative_to(ROOT).as_posix()
            if p.suffix=='.ipynb':
                nb=read(p); originals=[c.get('source') for c in nb['cells']]
                nb['metadata']={k:v for k,v in nb.get('metadata',{}).items() if k in ['kernelspec','language_info']}
                for c in nb['cells']:
                    c['metadata']={}
                    if c['cell_type']=='code':c['outputs']=[];c['execution_count']=None
                assert originals==[c.get('source') for c in nb['cells']]
                target=stage/dest;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(nb,ensure_ascii=False,indent=1),encoding='utf-8')
                sources[dest]={'source':p.relative_to(ROOT).as_posix(),'source_sha256':sha(p),'packaged_sha256':sha(target),'transformation':'remove outputs/execution metadata, preserve source cells'};redactions.append(dest)
            else:cp(p,dest)
    for n in ['run_all.py','requirements.txt','pytest.ini']:cp(ROOT/n,'02_MA_NGUON/'+n)
    cp(ROOT/'README.md','05_BANG_CHUNG_NGHIEM_THU/lich_su/README_ORIGINAL.md')
    for p in (ROOT/'data/raw').iterdir():
        if p.name in ['dry_bean.arff','rice.arff','bank-additional-full.csv','dataset_manifest.json']:cp(p,'03_DU_LIEU/'+p.name)
    for p in (ROOT/'data/splits'/ID).rglob('*.json'):cp(p,'03_DU_LIEU/splits/'+p.relative_to(ROOT/'data/splits'/ID).as_posix())
    for p in out.iterdir():
        if p.is_file():
            dest=('05_BANG_CHUNG_NGHIEM_THU/' if p.suffix=='.json' else '04_KET_QUA_THUC_NGHIEM/')+p.name
            cp(p,dest)
    for p in (out/'figures').glob('*.png'):cp(p,'04_KET_QUA_THUC_NGHIEM/figures/'+p.name)
    for p in (ROOT/'reports'/ID).glob('*.md'):cp(p,'05_BANG_CHUNG_NGHIEM_THU/'+p.name)
    for n in ['METHODOLOGY.md','IMPLEMENTATION.md']:
        cp(ROOT/'reports'/n,'05_BANG_CHUNG_NGHIEM_THU/lich_su/'+n)
    for p in (ROOT/'reports').glob('*.xml'):cp(p,'05_BANG_CHUNG_NGHIEM_THU/kiem_thu_lich_su/'+p.name)
    for n in ['experiment.json','status.json','frozen_protocol.sha256.json']:
        cp(ROOT/'results'/OLD/n,'05_BANG_CHUNG_NGHIEM_THU/lich_su/'+OLD+'/'+n)
    for p in (ROOT/'reports'/OLD).glob('*.md'):cp(p,'05_BANG_CHUNG_NGHIEM_THU/lich_su/'+OLD+'/'+p.name)
    # One small, official LR checkpoint and development split for executable demo.
    checkpoint=ROOT/'checkpoints'/ID/'dry_bean/lr/13';processed=ROOT/'data/processed'/ID/'dry_bean/13'
    for n in ['model.joblib','ecdf_B8.joblib','model.json']:cp(checkpoint/n,'DEMO/'+n)
    for n in ['corruptor.joblib','model_val.joblib']:cp(processed/n,'DEMO/'+n)
    frozen=read(out/'frozen_protocol.json')
    selected=next(s for s in frozen['selections'] if (s['dataset'],s['model'],s['seed'],s['B'],s['scorer'])==('dry_bean','lr',13,8,'cpcr'))
    meta={'experiment':ID,'split':'model_val','selection':selected,'labels':frozen['signature']['config']['datasets']['dry_bean']['labels'],'hashes':{p.name:sha(p) for p in (stage/'DEMO').iterdir()}}
    (stage/'DEMO/metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    cp(ROOT/'tools/demo_acceptance.py','tools/demo_acceptance.py')
    for n in ['build_acceptance_package.py','acceptance_documents.py','audit_acceptance.py']:cp(ROOT/'tools'/n,'tools/'+n)
    # Read-only derived evidence contains no raw personal account metadata.
    if not args.audit.exists():
        print('Waiting for read-only audit evidence before generating audit conclusions...',flush=True)
        deadline=time.monotonic()+3600
        while not args.audit.exists():
            if time.monotonic()>deadline:raise TimeoutError('Audit evidence not ready; staging retained')
            time.sleep(2)
    audit=read(args.audit)
    cleaned=json.loads(json.dumps(audit))
    for r in cleaned['raw']:r['file']='03_DU_LIEU/'+Path(r['file']).name
    (stage/'05_BANG_CHUNG_NGHIEM_THU/acceptance_audit_evidence.json').write_text(json.dumps(cleaned,ensure_ascii=False,indent=2),encoding='utf-8')
    w=write_documents(stage,ROOT,audit)
    frame=pd.read_csv(out/'per_seed_results.csv');main=frame[(frame.B==8)&(frame.target_coverage==.9)]
    expected_scorers={'msp','entropy','margin','instability','weighted','cpcr','no_q','no_interaction','uncertainty_only','instability_only','raw_instability'}
    cells=frame.groupby(['B','scorer','target_coverage']).size()
    grid_checks={'rows_44550':len(frame)==44550,'scorers_11':set(frame.scorer)==expected_scorers,'all_B_scorer_coverage_450':len(cells)==99 and bool((cells==450).all()),'mandatory_metrics_finite':bool(frame[['aurc','augrc','threshold']].notna().all().all()),'datasets_official_only':set(frame.dataset)==set(frozen['signature']['datasets'])}
    w('05_BANG_CHUNG_NGHIEM_THU/TABLE_GRID_CHECKS.json',json.dumps(grid_checks,indent=2))
    audit['checks'].update(grid_checks)
    comparison=main[main.scorer.isin(['msp','cpcr'])].groupby(['dataset','model','scorer']).aurc.mean().unstack().reset_index()
    comparison['CPCR-MSP']=comparison.cpcr-comparison.msp
    result_table=table(comparison)
    stats=pd.read_csv(out/'statistical_summary.csv');stats=stats[stats.scorer=='cpcr'][['dataset','model','condition_group','mean_paired_delta_aurc','ci95_low','ci95_high']]
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(13,5),sharey=True)
    for ax,group in zip(axes,['all','quantization']):
        s=stats[stats.condition_group==group].reset_index(drop=True)
        for i,r in s.iterrows():
            ax.plot([r.ci95_low,r.ci95_high],[i,i],color='tab:blue')
            ax.plot(r.mean_paired_delta_aurc,i,'o',color='tab:blue')
        ax.axvline(0,color='black',linestyle='--');ax.set_yticks(range(len(s)),s.dataset+' / '+s.model)
        ax.set_title(group+'; stored conditional 95% CI');ax.set_xlabel('CPCR minus MSP AURC (B=8)')
    fig.tight_layout();fig.savefig(stage/'04_KET_QUA_THUC_NGHIEM/figures/audit_statistical_comparisons.png',dpi=180);plt.close(fig)
    select=pd.DataFrame(audit['selected_cpcr_B8'])[['dataset','model','seed','lambda','gamma']]
    cl=pd.DataFrame(audit['classification']);clean=cl[cl.condition=='clean']
    banklabels=pd.DataFrame([{'split':r['split'],'rows':r['rows'],'counts':r['counts'],'yes_rate':r['yes_rate']} for r in audit['labels'] if r['dataset']=='bank_marketing'])
    runtime=main[main.scorer=='cpcr'].groupby(['dataset','model'])[['risk_seconds','inference_seconds']].sum();runtime['overhead_ratio']=runtime.risk_seconds/runtime.inference_seconds
    ab=frame[(frame.target_coverage==.9)&(frame.scorer.isin(['cpcr','raw_instability','no_interaction','no_q','instability_only']))].groupby(['dataset','model','B','scorer']).aurc.mean().reset_index()
    w('04_KET_QUA_THUC_NGHIEM/RESULTS_EXPLAINED.md','# Giải thích kết quả chính thức\n\nExperiment '+ID+'. Tất cả bảng dưới chỉ tổng hợp lại CSV/cache đã lưu; không dự đoán hoặc chạy Test lại. AURC thấp tốt hơn. Trung bình cân bằng 5 seed×10 điều kiện, B8; lọc target .9 để tránh đếm ba lần cùng AURC.\n\n'+result_table+'\n## Khoảng tin cậy và C3\n\n'+table(stats)+'\n## Hệ số B8 theo seed\n\n'+table(select)+'''
## Diễn giải

**Dry Bean:** RF có lợi trung bình nhưng delta C3 dương. LR/MLP trùng MSP khi cả λ và γ đều 0 trong bảng selections; không phải vì λ=0 một mình. Kết luận được giới hạn theo dữ liệu/mô hình.

**Rice:** LR/MLP có AURC tăng nhẹ; RF lợi nhỏ trung bình nhưng C3 tăng và seed không đồng nhất. Giả thuyết tín hiệu instability không bổ sung đủ hoặc khác phân phối phát triển chưa được kiểm định nhân quả.

**Bank:** LR/MLP giảm AURC trung bình, RF trùng MSP. CPCR không đổi dự đoán lớp. Không suy ra classifier tốt chỉ từ delta; xem accuracy, Macro-F1 và số dự đoán yes bên dưới. Một seed MLP có delta dương dù trung bình âm. Tỷ lệ nhãn thay đổi theo split là quan sát trực tiếp; nguyên nhân kinh tế/chiến dịch chưa được xác minh. Source UCI cho biết thứ tự thời gian, không cho đủ timestamp để tái dựng ngày từng hàng.

## Nhãn Bank theo split thật

'''+table(banklabels)+'\n## Phân loại clean Test đã lưu (B8, toàn bộ seed)\n\n'+table(clean[['dataset','model','seed','accuracy','macro_f1','confusion_matrix','predicted_counts']])+'''
Hàng confusion matrix là nhãn thật, cột là nhãn dự đoán; Bank thứ tự [no,yes]. predicted_counts=[số no,số yes]. Chỉ hàng có yes=0 mới chứng minh toàn bộ dự đoán no cho điều kiện đó. Bảng đầy đủ mọi điều kiện trong classification_from_saved_cache.csv. Accuracy Model-Val và Test không được trộn. Accuracy có thể cao do lớp đa số, trong khi Macro-F1 phạt việc bỏ lớp yes; Test có drift nên accuracy có thể thấp hơn rõ.

## Ablation

'''+table(ab)+'\nCác B được tune/calibrate riêng; bảng là so sánh pipeline, không cô lập duy nhất số lần suy luận. no_q=uncertainty_only là alias.\n\n## Overhead CPU đã đo\n\n'+table(runtime.reset_index())+'\nTỷ số trên là thời gian tính risk bổ sung/base, tổng latency xấp xỉ 1+tỷ số lần base; không phải benchmark mới.\n\nBiểu đồ gốc PNG trong figures. Risk–coverage chỉ là một seed clean đại diện ghi trên title, không phải trung bình 5 seed. CI xem bảng trên; không suy ra ý nghĩa thống kê phổ quát.\n')
    result_path=stage/'04_KET_QUA_THUC_NGHIEM/RESULTS_EXPLAINED.md'
    mv=pd.read_csv(out/'model_val_metrics.csv')
    with result_path.open('a',encoding='utf-8') as handle:
        handle.write('\n## Bank: không nhầm Model-Val với Test\n\n'+table(mv[mv.dataset=='bank_marketing'][['model','seed','accuracy','macro_f1']]))
        handle.write('\nModel-Val có accuracy khoảng 89.85% nhưng Macro-F1 khoảng .4733. Train có 1.188/24.712 yes (~4.81%), Model-Val 418/4.118 (~10.15%), còn Test 1.892/4.119 (~45.93%). Đây là thay đổi tỷ lệ nhãn quan sát được, chưa xác định cơ chế nhân quả. Dùng bảng Test/confusion matrix phía trên để đánh giá classifier; không dùng accuracy 89.85% của Model-Val làm kết quả Test.\n')
        handle.write('\nBiểu đồ audit_statistical_comparisons.png được vẽ khi đóng gói trực tiếp từ statistical_summary.csv, không chạy lại bootstrap. Các hình khác là bản gốc của experiment.\n')
        handle.write('\nClean Test Bank: MLP dự đoán toàn bộ no ở cả 5 seed. LR dự đoán 18 yes ở mỗi seed (14 đúng, 4 sai). RF chỉ dự đoán no tại seed 13/21/101; seed 42 có 7 yes, seed 87 có 1 yes. Accuracy clean Test khoảng 54%, không phải 89.85% của Model-Val. Không suy rộng nhận định clean sang mọi corruption.\n')
    cl.to_csv(stage/'04_KET_QUA_THUC_NGHIEM/classification_from_saved_cache.csv',index=False)
    write_defense(w,result_table)
    problems='''
- Kiểm thử hiện tại: 3 test P4 notebook FAIL, 18 PASS, 3 deselected (training). Mock SimpleNamespace trong test_notebook_p4.py thiếu returncode; notebook hiện còn yêu cầu status.json P4=PASS. Test và notebook không đồng bộ. Không sửa test để che lỗi; log đầy đủ trong source_tests.log. Không gọi đây là toàn bộ PASS kỹ thuật.
- Notebook P4 hiện tự chạy P1–P3 còn thiếu nếu P4 báo thiếu prerequisite. Vì vậy Run all notebook P4 có thể kích hoạt training khi môi trường đổi ID; demo không gọi notebook này.
- Báo cáo IMPLEMENTATION/README gốc có câu FULL NOT_RUN từ giai đoạn trước; được giữ ở lich_su, không thay kết luận experiment chính thức.
- Stage command trong P1–P5_ACCEPTANCE thiếu --bank dù signature chính thức có ba dataset. Đây là hạn chế template báo cáo; lệnh tái tạo phải thêm --bank.
- configs/experiments.yaml có bank_extension:false, nhưng code dùng đối số bank; danh sách datasets trong signature xác nhận Bank đã được đưa vào run.
- Notebook có metadata người dùng/output cũ. Bản ZIP chỉ loại metadata/output và giữ nguyên ô mã; file gốc không sửa. Một số output cũ thuộc experiment khác đã loại bỏ.
- Môi trường gốc Python 3.13.16; máy kiểm thử dùng 3.11.9 hoặc phiên bản thực tế trong packaging_tests.json. Không tuyên bố tái lập bitwise hay chạy lại FULL.
- Không có kiểm toán độc lập lịch sử thực thi. Kiểm tra nội bộ mã/hash/cache không chứng minh tuyệt đối không có thao tác thủ công ngoài log. Không thấy đường chọn phương pháp dựa Test trong mã đã đọc.
- Chưa xác minh cloud sync, Colab thực thi, novelty hay hiệu quả ngoài ba dataset.
'''
    checks=pd.DataFrame([{'Hạng mục':k,'Trạng thái':'PASS' if v else 'FAIL','Bằng chứng':'acceptance_audit_evidence.json','Cách xác minh':'tools/audit_acceptance.py đọc hash, split hoặc bảng/cache'} for k,v in audit['checks'].items()])
    w('ACCEPTANCE_AUDIT.md','# Kiểm toán nghiệm thu\n\n'+table(checks)+problems+'\nCác artifact hash mismatch/missing được giữ nguyên và ghi chi tiết trong evidence. Không sửa kết quả. Các PASS ở đây là tính nhất quán nội bộ đã kiểm tra, không chứng nhận tính mới.\n')
    w('05_BANG_CHUNG_NGHIEM_THU/ACCEPTANCE_MATRIX.md','# Ma trận nghiệm thu\n\n'+table(checks)+'''
| Hạng mục | Trạng thái | File bằng chứng | Cách xác minh |
|---|---|---|---|
| P1–P5 trạng thái lịch sử | PASS nếu checks all_status_pass | P1–P5_ACCEPTANCE.md, status.json | Đối chiếu ID và các gate; không chạy stage lại |
| PASS kỹ thuật đóng gói | Xem packaging_tests.json | Test log/XML, demo log | Chạy trên bản giải nén |
| PASS thực nghiệm về tính đầy đủ | Theo 450_primary_cells và primary_csv_matches_cache | CSV, receipt audit | Đối chiếu tổ hợp và metric đã lưu |
| Tính mới | NOT_VERIFIED | HAN_CHE_VA_HUONG_PHAT_TRIEN | Chưa khảo sát độc lập |
| Hiệu quả tổng quát | NOT_VERIFIED | RESULTS_EXPLAINED | Ba dataset không đủ chứng minh phổ quát |
| Cloud sync/Colab | NOT_VERIFIED | PACKAGE_VERIFICATION_REPORT | Chưa có kiểm tra remote |
''')
    w('HUONG_DAN_CHAY_DEMO.md','''# Giải nén và chạy demo

Giải nén ZIP vào thư mục bất kỳ. Mở terminal tại thư mục chứa PACKAGE_MANIFEST.json. Cài Python 3.11 hoặc môi trường tương thích requirements; demo đã kiểm tra với Python hiện tại ghi trong packaging_tests.json, môi trường nghiên cứu gốc trong experiment.json.

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r 02_MA_NGUON/requirements.txt
.venv\Scripts\python.exe tools/demo_acceptance.py
```

Linux/macOS: `python3 -m venv .venv`, rồi `.venv/bin/python -m pip install -r 02_MA_NGUON/requirements.txt` và `.venv/bin/python tools/demo_acceptance.py`.

Demo kiểm hash rồi load checkpoint LR Dry Bean seed 13 chính thức, lấy 8 mẫu Model-Val, in mẫu đầu, xác suất, nhãn, mẫu nhiễu nhẹ, u/v/q/R, thứ hạng MSP/CPCR và accept R≤ngưỡng Calibration .9 đã khóa. Đây không phải kết quả Test mới. Với λ=γ=0 thứ hạng trùng là hành vi đúng, không tạo cải thiện giả. Ví dụ .375 cuối output là bài toán tính tay, ghi nhãn riêng.

Không fit model, không chọn lại hệ số, không chạy FULL. Chỉ load joblib thuộc gói có manifest đã kiểm; không tải checkpoint tùy ý. Cần các dependency đã cài, không cần đường dẫn Google Drive. Demo log kiểm thử thực tế nằm trong 05_BANG_CHUNG_NGHIEM_THU/demo_test.log.

Kiểm thử không training: từ 02_MA_NGUON chạy `python -m pytest tests/test_core.py tests/test_notebook_p2.py tests/test_notebook_p4.py tests/test_runner.py -k "not models_reload" -q -p no:cacheprovider`. Không chạy toàn bộ tests nếu muốn giữ điều kiện không training vì integration và models_reload có fit mô hình.
''')
    w('02_MA_NGUON/README.md','''# Chạy mã sau giải nén

Đọc ../HUONG_DAN_CHAY_DEMO.md để kiểm tra không huấn luyện. Mã src/config/scripts/tests và run_all.py giữ nguyên byte; notebooks chỉ bỏ metadata/output cá nhân, không đổi source cell. CODE_INDEX.md mô tả hàm. Notebook hiện giữ MODE cũ có thể FULL, vì vậy không dùng Run all cho demo.

## Tái tạo pipeline trong bản sao làm việc mới (không thực hiện khi đóng gói)

Chép thư mục 02_MA_NGUON thành một thư mục làm việc mới; chép nội dung 03_DU_LIEU gồm raw files/manifest vào `<working>/data/raw/` (không cần splits để chạy mới). Tạo `<working>/reports/` và nếu cần đọc tài liệu từ notebook, chép METHODOLOGY.md/IMPLEMENTATION.md lịch sử vào đó. Cài requirements. CLI suy ra ROOT từ vị trí run_all.py; hoặc truyền `--root <working>`.

Phát triển: `python run_all.py --root . --mode SMOKE --stage all`, sau đó PILOT tương tự. Các lệnh này huấn luyện trong bản sao, không nằm trong kiểm thử nghiệm thu. Muốn tái tạo FULL sau một quyết định nghiên cứu mới: lần lượt `python run_all.py --root . --mode FULL --bank --stage P1` tới P4, kiểm freeze rồi P5. P5 dùng Test, không dùng để chọn lại phương pháp. Không sao chép status/ID cũ để vượt gate. Phiên bản khác tạo ID khác; gói không kèm mọi checkpoint/cache nên không resume toàn bộ experiment gốc từ ZIP.

## Colab và shortcut

Mount Drive và tìm ROOT thực tế; không giả định đường dẫn shortcut. Ví dụ đọc-only:

```python
from pathlib import Path
base=Path('/content/drive')
candidates=[base/'MyDrive/FJCAI2027_PCRR']
shortcut=base/'Shareddrives'
for search_root in [base/'MyDrive/.shortcut-targets-by-id', base/'.shortcut-targets-by-id', shortcut]:
    if search_root.exists():
        candidates += [p.parent for p in search_root.rglob('run_all.py') if (p.parent/'data/raw/dataset_manifest.json').is_file()]
valid=list(dict.fromkeys(p.resolve() for p in candidates if (p/'run_all.py').is_file() and (p/'data/raw/dataset_manifest.json').is_file()))
assert len(valid)==1, f'Can chon ROOT khi co {len(valid)} ung vien: {valid}'
ROOT=valid[0]
print(ROOT)
```

Sau đó đối chiếu checksum raw manifest. Nếu nhiều bản sao, chọn rõ workspace phát triển, không ghi vào bản khóa. Phát hiện shortcut này là hướng dẫn; chưa chạy Colab trong nghiệm thu. scripts/create_notebooks.py có thể tạo lại notebook và mất chỉnh sửa gần đây; không chạy khi chỉ kiểm tra.
''')
    w('README_NGHIEM_THU.md','''# Gói nghiệm thu FJCAI 2027

Đề tài: Perturbation-Consistency Risk Ranking for Reliable Tabular Classification Under Feature Corruption. Phương pháp CPCR. Nguồn chính thức full-62500e11e892b899; lịch sử full-37245e523b162876 tách riêng.

Đọc theo thứ tự: ACCEPTANCE_AUDIT → 01_TAI_LIEU_NGHIEN_CUU → 04_KET_QUA_THUC_NGHIEM/RESULTS_EXPLAINED → 06_CHUAN_BI_BAO_VE → HUONG_DAN_CHAY_DEMO. Kiểm hash bằng tools/verify_package.py. PACKAGE_VERIFICATION_REPORT bản ngoài ZIP chứa SHA-256 và kích thước cuối cùng của chính ZIP; không thể ghi hash ZIP vào bên trong nó mà không thay hash.

Đây là đóng gói/audit, không training, không chạy Test, không tune lại. PASS kỹ thuật không đồng nghĩa novelty hay hiệu quả tổng quát. Mọi giới hạn xem ACCEPTANCE_AUDIT và báo cáo kiểm tra.
''')
    w('05_BANG_CHUNG_NGHIEM_THU/SOURCE_CONFIGURATION_MANIFEST.json',json.dumps({'official_signature':frozen['signature'],'packaged_sources':sources,'notebook_privacy_redactions':redactions,'scope':'src is byte-identical; notebooks preserve source cells; external run_all/scripts/notebooks not covered by original src signature'},ensure_ascii=False,indent=2))
    # Standalone stdlib manifest validator, supports arbitrary extraction location.
    w('tools/verify_package.py','''import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
m=json.loads((root/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
for name,item in m['files'].items():
    p=root/name
    assert p.is_file(),name
    assert p.stat().st_size==item['bytes'],name
    assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],name
assert {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}==set(m['files'])|{'PACKAGE_MANIFEST.json'}
print('PASS:',len(m['files']),'payload files; manifest excludes itself to avoid self-reference')
''')
    # Preflight before archive; never add pycache to package.
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONIOENCODING']='utf-8'
    logs={}
    testcmd=[sys.executable,'-m','pytest','tests/test_core.py','tests/test_notebook_p2.py','tests/test_notebook_p4.py','tests/test_runner.py','-k','not models_reload','-q','-p','no:cacheprovider']
    def run(cmd,cwd):
        r=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        return {'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    # Extract a preliminary ZIP to genuinely test relocation.
    preliminary=local/(stage.name+'_preflight.zip')
    with zipfile.ZipFile(preliminary,'w',zipfile.ZIP_DEFLATED) as z:
        for p in stage.rglob('*'):
            if p.is_file():z.write(p,p.relative_to(stage).as_posix())
    extracted=Path(tempfile.mkdtemp(prefix='extract_',dir=local))
    with zipfile.ZipFile(preliminary) as z:assert z.testzip() is None;z.extractall(extracted)
    logs['unit_tests']=run(testcmd,extracted/'02_MA_NGUON')
    logs['demo']=run([sys.executable,str(extracted/'tools/demo_acceptance.py')],extracted)
    logs['environment']=run([sys.executable,'-c','import sys;sys.path.insert(0,"02_MA_NGUON");from src.io import versions;print(versions())'],extracted)
    logs['not_run']=['models_reload tests: train models','integration tests: train and synthetic FULL','real FULL Test','training or parameter reselection','remote Colab/cloud sync','independent novelty review']
    logs['relocated_extraction_test']=True
    w('05_BANG_CHUNG_NGHIEM_THU/packaging_tests.json',json.dumps(logs,ensure_ascii=False,indent=2))
    for key,name in [('unit_tests','source_tests.log'),('demo','demo_test.log')]:w('05_BANG_CHUNG_NGHIEM_THU/'+name,logs[key]['stdout']+'\n'+logs[key]['stderr'])
    # Source syntax and notebook cell validity without executing notebook cells.
    import nbformat
    for p in (stage/'02_MA_NGUON').rglob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'))
    for p in (stage/'02_MA_NGUON/notebooks').glob('*.ipynb'):
        nb=nbformat.read(p,as_version=4);nbformat.validate(nb)
        for c in nb.cells:
            if c.cell_type=='code':ast.parse(c.source)
    forbidden=[]
    for p in stage.rglob('*'):
        if not p.is_file():continue
        if p.suffix.lower() in ['.py','.json','.md','.ipynb','.yaml','.txt','.xml']:
            t=p.read_text(encoding='utf-8',errors='replace')
            if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|AIza[0-9A-Za-z_-]{30,}|sk-[A-Za-z0-9]{32,}|"private_key"\s*:|"refresh_token"\s*:',t):forbidden.append(p.relative_to(stage).as_posix())
            if p.suffix=='.ipynb':assert 'executionInfo' not in t and 'userId' not in t and 'displayName' not in t
    assert not forbidden,forbidden
    w('05_BANG_CHUNG_NGHIEM_THU/PACKAGING_CHECKS.md',f'''# Kiểm tra đóng gói

- Python AST và notebook schema/cell syntax: PASS.
- Quét định dạng secret phổ biến trong file text được chọn: PASS; không tìm khóa private/API/refresh token theo mẫu kiểm. Không là chứng minh toán học mọi secret bất kỳ.
- Notebook metadata/output cá nhân: đã loại, source cell giữ nguyên.
- Pytest không training returncode: {logs['unit_tests']['returncode']}.
- Demo checkpoint Model-Val returncode: {logs['demo']['returncode']}.
- Chạy trên bản giải nén ở thư mục cục bộ khác: có.
- Danh sách chưa chạy: {', '.join(logs['not_run'])}.
''')
    excluded='Prediction caches đầy đủ (dung lượng lớn, giữ receipt/hash và trích classification); toàn bộ checkpoint trừ demo LR; processed đầy đủ trừ Model-Val demo/corruptor; archive raw trùng dữ liệu; PNG/PDF trùng chọn PNG; cache Python/pytest, .git, môi trường; log/notebook output cá nhân; bảng kết quả experiment cũ để tránh trộn.'
    w('PACKAGE_VERIFICATION_REPORT.md',f'''# Báo cáo kiểm tra gói

ZIP xuất dự kiến: deliverables/PCRR_FJCAI2027_NGHIEM_THU.zip. Kích thước, SHA-256 cuối cùng và số file được ghi ở PACKAGE_VERIFICATION_REPORT.md bên cạnh ZIP sau khi xây xong; hash ZIP không thể tự nằm trong chính ZIP.

Đã tạo ZIP tạm, kiểm CRC và giải nén ở thư mục khác, chạy kiểm thử mã nguồn và demo tại đó. Kết quả chi tiết: 05_BANG_CHUNG_NGHIEM_THU/packaging_tests.json; source_tests.log và demo_test.log. Pytest returncode={logs['unit_tests']['returncode']}; demo returncode={logs['demo']['returncode']}. Test training/integration/FULL không chạy. Kiểm syntax và notebook schema PASS. Manifest liệt kê mọi payload file trừ chính manifest để tránh vòng tự tham chiếu; SHA-256 cuối ZIP bao gồm manifest.

Không đóng gói: {excluded}

Không thiếu src, config, bảng kết quả bắt buộc, công thức, raw/provenance, P1–P5. Demo dùng đường dẫn tương đối và không cần Drive. Không đủ cache để resume FULL cũ; hướng dẫn tạo bản làm việc mới ở README mã nguồn. Audit consistency xem ACCEPTANCE_AUDIT. Novelty/hiệu quả tổng quát/cloud sync/Colab NOT_VERIFIED.
''')
    paths=sorted(p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file())
    w('PACKAGE_CONTENTS.md','# Nội dung gói\n\n'+ '\n'.join('- `'+p+'`' for p in paths+['PACKAGE_CONTENTS.md','PACKAGE_MANIFEST.json']))
    manifest={'experiment':ID,'algorithm':'sha256','self_exclusion':'PACKAGE_MANIFEST.json only; ZIP external hash covers it','files':{p.relative_to(stage).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(stage.rglob('*')) if p.is_file()}}
    w('PACKAGE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    dest=ROOT/'deliverables/PCRR_FJCAI2027_NGHIEM_THU.zip'; tempzip=local/(stage.name+'_final.zip')
    with zipfile.ZipFile(tempzip,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(stage.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(stage).as_posix())
    final_extract=Path(tempfile.mkdtemp(prefix='final_verify_',dir=local))
    with zipfile.ZipFile(tempzip) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(set(z.namelist()))
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
        count=len(z.namelist());z.extractall(final_extract)
    verification=run([sys.executable,str(final_extract/'tools/verify_package.py')],final_extract)
    assert verification['returncode']==0,verification
    # Final artifact demo too, avoids treating the preliminary archive as the final ZIP.
    final_demo=run([sys.executable,str(final_extract/'tools/demo_acceptance.py')],final_extract)
    shutil.copyfile(tempzip,dest);assert sha(dest)==sha(tempzip)
    report=f'''# PACKAGE VERIFICATION REPORT

- ZIP: `{dest}`
- Bytes: {dest.stat().st_size}; MiB: {dest.stat().st_size/1048576:.3f}
- SHA-256: `{sha(dest)}`
- Files: {count}
- ZIP CRC/integrity: PASS.
- Paths relative, no duplicate member names: PASS.
- Final extraction and every payload SHA-256: PASS ({count-1} files; manifest self-excluded).
- Source tests on relocated extraction: {'PASS' if logs['unit_tests']['returncode']==0 else 'FAIL'}; {logs['unit_tests']['stdout'].strip()}
- Demo in final extraction: {'PASS' if final_demo['returncode']==0 else 'FAIL'}.
- Source AST/notebook schema: PASS.
- Research checks: {json.dumps(audit['checks'])}
- Main folders: 01_TAI_LIEU_NGHIEN_CUU, 02_MA_NGUON, 03_DU_LIEU, 04_KET_QUA_THUC_NGHIEM, 05_BANG_CHUNG_NGHIEM_THU, 06_CHUAN_BI_BAO_VE, DEMO, tools.
- Excluded: {excluded}
- Training, FULL evaluation, retuning: NOT_RUN by instruction.
- Cloud synchronization / Colab / novelty / general effectiveness: NOT_VERIFIED.
- Local staging retained for recovery: `{stage}`.
- Test environment: {logs['environment']['stdout'].strip()}

Không sửa hai experiment nguồn. Mã nghiên cứu byte-identical; notebook chỉ bỏ metadata/output để bảo vệ thông tin cá nhân. Các bảng mới là tổng hợp audit từ evidence đã lưu, không thay số liệu nghiên cứu.
'''
    (dest.parent/'PACKAGE_VERIFICATION_REPORT.md').write_text(report,encoding='utf-8')
    (dest.parent/'PCRR_FJCAI2027_NGHIEM_THU.sha256').write_text(sha(dest)+'  '+dest.name+'\n',encoding='ascii')
    print(report,flush=True)
if __name__=='__main__':main()
