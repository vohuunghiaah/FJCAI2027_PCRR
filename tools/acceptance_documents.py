"""Vietnamese acceptance documentation; derived tables only, no research mutation."""
import ast,json
from pathlib import Path
import pandas as pd

MODULES={
'data.py':('P1','Đọc và xác thực dữ liệu, biến đổi Bank, chia nhóm hoặc thời gian, chặn truy cập Test','read_frame: đường dẫn → DataFrame; readiness: root/config → dữ liệu và bằng chứng hash; prepare_features: bỏ duration, chuyển pdays; audit: thống kê chất lượng; split_indices: X/y/seed → chỉ số và hàng loại; load_split: đọc split, yêu cầu allow_test cho Test','tests/test_core.py: group_splits, temporal_conflicting_labels, selection_guard'),
'preprocessing.py':('P1–P2','Tạo pipeline tiền xử lý chỉ fit trên Train','make_preprocessor: schema X và scaled → ColumnTransformer; numeric median, scaler tùy mô hình; categorical mode và one-hot, ignore unknown','test_train_only_preprocessor'),
'models.py':('P2, P3–P5 suy luận','Huấn luyện mô hình cơ sở và chuẩn hóa giao diện dự đoán','seed_all: seed → trạng thái RNG; train: Train/Model-Val/config → TabularModel và thời gian; TabularModel.predict_proba: X → ma trận n×K','test_models_reload (không chạy lại khi đóng gói vì có training)'),
'corruptions.py':('P1, P3–P5','Mô phỏng lỗi đo và đo thay đổi phân phối xác suất','normalized: chuẩn hóa tên; geometry_violations: X → số vi phạm; Corruptor.fit: Train → SD/min/max; transform: X/kind/level/seed → X nhiễu; instability: model/X/B → vector JS trung bình chuẩn hóa','test_corruptions_preserve_input_and_categories, test_instability_zero_and_max'),
'cpcr.py':('P3–P5','ECDF có điều kiện và điểm CPCR','ConditionalECDF.fit: Model-Val u/v → biên quantile và mẫu tham chiếu; transform: u/v → q; cpcr: u/q/lambda/gamma → R','test_ecdf_and_direction'),
'risk_baselines.py':('P3–P5','Định nghĩa tập scorer và ablation','score: tên/p/v/q/hệ số → vector risk; MSP dùng 1-max(p); entropy và margin là đối chứng; no_q và uncertainty_only là alias','test_all_risk_scores_and_selection_guard'),
'baselines.py':('P3–P5','Xuất lại API scorer để tương thích import','Không có thuật toán riêng; xuất SCORERS và score từ risk_baselines','Kiểm tra import và đối chiếu module gốc'),
'calibration.py':('P4','Tách chọn hệ số và đặt ngưỡng','candidates: scorer/grid → các cặp; select: Risk-Val → cặp AURC nhỏ nhất và bảng search; calibrate: clean Calibration/coverages → ngưỡng order statistic','test_threshold_ties_and_empty_acceptance, selection_guard'),
'metrics.py':('P2, P4–P5','Phân biệt chất lượng phân loại, thứ hạng và triển khai ngưỡng','probabilities: kiểm tra/chuẩn hóa p; classification: y/p → accuracy/F1/NLL/Brier/ECE/confusion; curve: errors/scores → coverage/risk/generalized risk; ranking: AURC/AUGRC/AUROC; deployment: threshold → coverage/risk thực tế','test_known_risk_values, classification_known, float32_probability_roundoff'),
'evaluation.py':('P5','Tổng hợp kết quả có sẵn, bootstrap theo hàng, xuất biểu đồ và báo cáo','paired_cluster_bootstrap: records/scorer → CI; summarize: bảng/cache → CSV và thống kê; figures: bảng/cache → PNG/PDF; report: bảng/stats → scientific_report.md','test_cluster_bootstrap_identical_scores; integration lịch sử'),
'experiment.py':('P1–P5','Điều phối stage và khóa protocol','Experiment.__init__: root/mode/bank → chữ ký, ID và thư mục (có ghi, không dùng trong audit); p1…p5: các stage; features: split → p/u/v/q/errors; verify_freeze: checksum/signature/artifacts; publish_hashes/verify_hashes: bằng chứng; development_report: bảng phát triển; conditions: tập nhiễu; run/report: gate/trạng thái','test_integration.py là bằng chứng lịch sử, không chạy lúc đóng gói'),
'io.py':('P1–P5','I/O nguyên tử và định danh nội dung','sha256: file → hash; native/canonical/digest: object → JSON/hash ổn định; atomic: writer → replace; write_json/read_json/save/csv: I/O; versions: phiên bản môi trường','test_atomic_serialization'),
'__init__.py':('P1–P5','Đánh dấu package Python','Không có hàm nghiên cứu','Import package')}

def table(df):
    def val(v):
        if isinstance(v,float): return f'{v:.8g}'
        return str(v).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(map(str,df.columns))+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'+'\n'.join('| '+' | '.join(val(x) for x in row)+' |' for row in df.itertuples(index=False,name=None))+'\n'

def write_documents(stage,root,audit):
    def w(rel,text):
        p=stage/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.strip()+'\n',encoding='utf-8')
    D='01_TAI_LIEU_NGHIEN_CUU/'
    w(D+'BAI_TOAN_VA_MUC_TIEU.md','''# Bài toán và mục tiêu

Mỗi hàng dữ liệu bảng là một đối tượng x, mỗi cột là một thuộc tính. Mô hình f trả về p(y=k|x), sau đó chọn lớp có xác suất lớn nhất. Dry Bean và Rice dùng đặc trưng hình học hạt; Bank dự đoán đăng ký tiền gửi.

Feature corruption là lỗi ở đầu vào: thiếu ô, nhiễu số hoặc làm tròn thô. Mẫu bị lệch khỏi phân phối Train có thể đi qua ranh giới quyết định. Mô hình vẫn có thể tự tin khi sai. Vì vậy accuracy trung bình chưa cho biết mẫu nào đáng tin để tự động xử lý.

| Khái niệm | Câu hỏi | Đại lượng trong mã |
|---|---|---|
| Classification accuracy | Bao nhiêu dự đoán đúng? | mean(argmax(p)==y) |
| Prediction confidence | Mô hình tự tin đến đâu? | max(p) |
| Failure detection | Điểm có phân biệt mẫu sai với đúng? | AUROC với sai là lớp dương |
| Risk ranking | Mẫu nào nên được giữ trước? | Sắp risk tăng dần, AURC |
| Selective risk | Trong các mẫu được nhận, tỷ lệ sai bao nhiêu? | errors[accepted].mean() |

Selective prediction nhận mẫu có R≤t, chuyển các mẫu còn lại sang kiểm tra bổ sung. Coverage là tỷ lệ nhận. Từ chối mọi mẫu không phải thành công: risk lúc không nhận mẫu nào là undefined.

Đóng góp đang khảo sát là điểm xếp hạng hậu xử lý CPCR trên mô hình cố định. Không cần kiến trúc mạng mới vì câu hỏi là khai thác độ bất ổn đầu ra để ưu tiên kiểm tra, không thay bộ phân loại. CPCR không đổi argmax, do đó AURC tốt hơn không tự làm accuracy tăng. Tính mới cần khảo sát độc lập; gói này không xác nhận tính mới.
''')
    w(D+'GIAI_THICH_CPCR.md','''# Giải thích CPCR từ mã đã thực thi

Nguồn: [corruptions.py](../02_MA_NGUON/src/corruptions.py), [cpcr.py](../02_MA_NGUON/src/cpcr.py), [risk_baselines.py](../02_MA_NGUON/src/risk_baselines.py). B chính là 8; B=4/16 là ablation được fit/tune/calibrate riêng. Nhiễu nhẹ Gaussian sigma=.01 theo SD Train, seed+b tạo chuỗi lồng nhau.

## 1. Uncertainty u

Đầu vào p là vector xác suất hợp lệ của K lớp; đầu ra u=1−max_k p_k là một số trong [0,1−1/K]. u biểu diễn thiếu tự tin theo MSP, không phải xác suất sai đã hiệu chuẩn. Với p=(.8,.2), u=.2. Python: `u = 1 - p.max(axis=1)`. Hàm thực tế: `risk_baselines.score`, `Experiment.features`. Nếu p sai shape, âm, NaN hoặc tổng không bằng 1, `metrics.probabilities` từ chối; gọi trực tiếp score không thay thế validation.

## 2. Perturbation instability v

Đầu vào gồm mô hình đã fit, X, Corruptor fit trên Train và B. Với mỗi b, tạo x_b nhiễu nhẹ và z_b=p(x_b). Đặt m=(p+z_b)/2, JS=(KL(p||m)+KL(z_b||m))/2. Hàm `corruptions.instability` trả v=mean_b JS/ln(2), trong [0,1]. JS đối xứng và có cận nên dễ so sánh; không có chứng minh đây là lựa chọn tối ưu.

Ví dụ tính tay: p=(1,0), z=(.5,.5), m=(.75,.25). KL(p||m)=ln(4/3)=.287682; KL(z||m)=.5ln(2/3)+.5ln(2)=.143841. JS=.215762, v=.311278 khi B=1. p=z cho v=0; p=(1,0), z=(0,1) cho v=1. Mã dùng natural log, clip mẫu số ở 1e−15 và clip JS chuẩn hóa vào [0,1]; số hạng xác suất 0 đóng góp 0. B phải dương (mã không chặn B=0 trước mean), p phải hợp lệ. NaN đầu vào cần được preprocessor xử lý; cột hằng hoặc clipping có thể làm perturbation không thay đổi dự đoán.

```python
import numpy as np
p=np.array([[1.,0.]])
z=np.array([[.5,.5]])
m=(p+z)/2
kl=lambda a: np.sum(a*np.log(np.clip(a,1e-15,1)/np.clip(m,1e-15,1)),axis=1)
v=(kl(p)+kl(z))/(2*np.log(2))
assert np.allclose(v,[.311278124459])
```

## 3. Conditional instability q

Đầu vào u,v của mẫu và tham chiếu Model-Val. `ConditionalECDF.fit` tạo biên quantile u (10 bins), bỏ biên trùng; `transform` gán bin bằng searchsorted side=right. q là tỷ lệ v tham chiếu ≤v mẫu trong bin. Đầu ra [0,1], biểu diễn mức bất ổn tương đối giữa mẫu có uncertainty tương tự, không phải xác suất sai. Nếu bin dưới 20 mẫu, dùng toàn bộ Model-Val. Ví dụ bin có v=[.01,.02,.04,.08], mẫu v=.03 cho q=2/4=.5; tại v=.04, q=3/4=.75. Với mặc định min_size=20, bin 4 mẫu sẽ fallback, nên ví dụ nhỏ đặt min_size=1 có chủ đích.

```python
from src.cpcr import ConditionalECDF
ref=ConditionalECDF(bins=1,min_size=1).fit([.2]*4,[.01,.02,.04,.08],split='model_val')
assert ref.transform([.2],[.03])[0] == .5
```

Fit trên split khác Model-Val bị chặn. Tham chiếu rỗng, shape khác, giá trị không hữu hạn bị từ chối. Phải fit trước transform. Sparse bins làm mất tính điều kiện; khi phân phối thay đổi, percentile Model-Val có thể không còn hữu ích. Transform không validation đầy đủ mọi kiểu đầu vào, caller cần giữ shape và miền hợp lệ.

## 4. Risk R

Đầu vào u,q và hệ số không âm λ,γ được chọn trên Risk-Val. Đầu ra R=u+λq+γuq, là điểm xếp hạng, có thể lớn hơn 1 và không phải xác suất lỗi. `cpcr.cpcr` thực hiện đúng công thức này. Ví dụ u=.2,q=.5,λ=.25,γ=.5: R=.2+.125+.05=.375.

```python
from src.cpcr import cpcr
assert np.allclose(cpcr([.2],[.5],.25,.5),[.375])
assert np.allclose(cpcr([.2],[.5],0,0),[.2])
```

λ=0 nhưng γ>0 vẫn còn γuq: R=u(1+γq). Ví dụ hai mẫu u=.2,.25 và q=1,0 với γ=1 cho R=.4,.25: thứ tự đảo so với MSP. Chỉ λ=γ=0 đảm bảo R=u cho mọi mẫu. Trong mã, scorer MSP là risk 1−MSP nên nhận điểm thấp trước; tương đương sắp confidence cao trước. Hệ số âm bị chặn; broadcast sai shape hoặc NaN không được cpcr tự kiểm tra đầy đủ. Không diễn giải tích uq là quan hệ nhân quả.

Ngưỡng t lấy ở clean Calibration, nhận R≤t. Ties có thể làm coverage lớn hơn mục tiêu. Demo dùng checkpoint Model-Val và ngưỡng đã khóa; ví dụ tính tay ở trên chỉ để học, không là bằng chứng Test.
''')
    stages=[('P1','Tạo dữ liệu đáng tin trước fit','Raw chỉ dùng kiểm tra shape/label/hash và chia tập; mọi tham số tiền xử lý chỉ Train','readiness, prepare_features, split_indices, make_preprocessor, Experiment.p1','dataset_readiness.json; split_summary.csv; data/splits; processed; p1_hashes','Hash/shape/labels đúng, split không giao nhóm, reload transformer đúng','Tại sao xem raw Test không đồng nghĩa dùng Test để tune? Vì chỉ audit/chia tập theo quy tắc cố định, không fit hoặc đánh giá dự đoán.'),('P2','Đặt bộ phân loại cơ sở cố định','Train để học; Model-Val để chọn epoch MLP và kiểm tra mô hình','models.train, TabularModel.predict_proba, Experiment.p2','model.joblib; model.json; training_log.csv; model_val_metrics.csv; p2_hashes','45 mô hình hợp lệ, checkpoint reload cho cùng xác suất','LR dùng logistic tuyến tính; RF gộp 200 cây; MLP hai tầng 64/32 ReLU. LR/RF không có search kiến trúc ở đây; MLP early stopping patience=10, tối đa 100 epoch.'),('P3','Đo bất ổn và xây tham chiếu không dùng Test','Model-Val fit ECDF; Risk-Val clean/C1/C2 tạo dữ liệu chọn hệ số','Corruptor.transform, instability, ConditionalECDF.fit, Experiment.p3','ecdf_B*.joblib; development_B*.joblib; corruption_manifests; p3_hashes','u/v/q hữu hạn, đúng split, C3 không vào phát triển','Vì sao C3 giữ lại? Để kiểm tra chuyển sang họ nhiễu chưa dùng chọn hệ số.'),('P4','Chọn điểm risk và ngưỡng theo hai tập khác nhau','Risk-Val chọn λ,γ; clean Calibration chọn ngưỡng; không dùng Test','calibration.select/calibrate; Experiment.p4/verify_freeze','parameter_search.csv; frozen_protocol.json; checksum','P1–P3 hash hợp lệ; freeze chứa signature, selections, threshold và hash artifact','Tách Risk-Val/Calibration giảm tái sử dụng cùng mẫu cho hai quyết định. Grid [0,.25,.5,1,2]; hòa AURC chọn λ nhỏ hơn rồi γ nhỏ hơn.'),('P5','Đánh giá protocol đã khóa','Chỉ FULL sau verify_freeze mới predict Test; threshold giữ nguyên dưới corruption','Experiment.p5; metrics.ranking/deployment; evaluation.summarize','per_seed_results; summary; ablation; statistics; figures; scientific_report','450 tổ hợp B8, B4/16 riêng, CSV/cache khớp, frozen intact','AURC là mean risk tại k=1…n; AUGRC là mean cumulative_errors/n. AUROC sai là positive; risk@coverage xếp Test khác risk dùng ngưỡng Calibration.')]
    body='# Quy trình P1–P5\n\nNguồn điều phối: [experiment.py](../02_MA_NGUON/src/experiment.py).\n'
    for s,why,allowed,func,art,gate,qa in stages:
        body+=f'\n## {s}\n\n**Vì sao:** {why}.\n\n**Dữ liệu được phép:** {allowed}.\n\n**Hàm:** `{func}`.\n\n**Artifact:** {art}.\n\n**PASS/FAIL:** {gate}; vi phạm gate là FAIL, thiếu bằng chứng là NOT_VERIFIED.\n\n**Câu hỏi và giải thích:** {qa}\n'
    body+='''
## Corruption và thống kê

Missingness: xác suất ô bị thiếu .05/.10/.20, gồm cả categorical. Gaussian: .01/.05/.10 nhân SD Train, numeric בלבד. Quantization: .02/.05/.10 nhân range Train; làm tròn theo min Train. Gaussian/quantization clip về range và miền cơ bản; không đảm bảo hình học khả thi. Tất cả cùng seed nhiễu theo dataset/seed/split/condition.

Bootstrap 1.000 lần resample row ID chung cho seed/condition/scorer trong mỗi dataset/model. Bank dùng circular blocks dài ceil(sqrt(n)). CI percentile 95% có điều kiện trên mô hình và split đã fit; không bao phủ biến thiên từ Train mới. Không coi 5 seed là 5 tập dữ liệu độc lập. Không có hiệu chỉnh nhiều so sánh. Ablation B=4/16 tune và calibrate riêng trước Test; không chỉ cắt ngắn điểm B8.

Ties khi xếp risk được tính theo kỳ vọng random tie breaking. Failure AUROC undefined khi chỉ có một trạng thái đúng/sai. Selective risk undefined khi không nhận mẫu. Không thay undefined bằng thành công giả.
'''.replace(' בלבד','')
    w(D+'QUY_TRINH_P1_P5.md',body)
    diagrams=[('Overall Research Pipeline','Raw --> P1[readiness + splits + Train preprocessing]\nP1 --> P2[Train LR RF MLP; Model-Val]\nP2 --> P3[perturbation + Model-Val ECDF]\nP3 --> P4[Risk-Val selection + Calibration thresholds]\nP4 --> Freeze[immutable protocol]\nFreeze --> P5[Test evaluation + reporting]'),('Luồng dữ liệu','Raw --> Train\nRaw --> ModelVal[Model-Val]\nRaw --> RiskVal[Risk-Val]\nRaw --> Calibration\nRaw --> Test\nTrain --> Fit[preprocessor + model + corruption scales]\nFit --> ModelVal\nModelVal --> Ref[ECDF reference]\nFit --> RiskVal\nRef --> RiskVal\nRiskVal --> Coeff[lambda gamma]\nCoeff --> Calibration\nCalibration --> Freeze\nFreeze --> Test'),('Tính CPCR','X --> P[predict_proba]\nX --> Noise[Gaussian light B times]\nNoise --> PB[predict_proba perturbed]\nP --> U[1-max p]\nP --> JS\nPB --> JS\nJS --> V[mean JS / ln2]\nU --> Q[Model-Val conditional ECDF]\nV --> Q\nU --> R[u + lambda*q + gamma*u*q]\nQ --> R'),('Chọn mô hình và ngưỡng','Train --> LRRF[fit LR RF]\nTrain --> MLP[fit MLP epochs]\nModelVal[Model-Val loss] --> MLP\nRiskVal[Risk-Val AURC clean C1 C2] --> Select[grid lambda gamma]\nSelect --> Cal[clean Calibration order statistic]\nCal --> Freeze[hashes + selections + thresholds]'),('Đánh giá cuối','Freeze[verify_freeze] --> Predict[Test cache or inference]\nPredict --> Rank[AURC AUGRC failure AUROC]\nPredict --> Deploy[fixed thresholds coverage risk]\nPredict --> Boot[paired row bootstrap or Bank blocks]\nRank --> Tables[CSV]\nDeploy --> Tables\nBoot --> Tables\nTables --> Figures[PNG and scientific report]')]
    w(D+'SO_DO_KIEN_TRUC.md','# Sơ đồ khớp mã nguồn\n\n'+ '\n\n'.join('## '+title+'\n\n```mermaid\nflowchart TD\n'+diagram+'\n```' for title,diagram in diagrams))
    code='# Chỉ mục mã nguồn\n\n| File | Vai trò | Hàm chính và ý nghĩa | P1–P5 |\n|---|---|---|---|\n'
    detail='# Giải thích code theo file\n\nNotebook P1/P3/P4/P5 gọi subprocess tới `run_all.py`; P2 hiện chứa PIPELINE_CODE gọi Experiment trực tiếp để tránh chạy lặp P1/P2. CLI `main` đọc root/mode/bank/stage, tạo Experiment, kiểm tra gate rồi gọi run(stage). Không chạy notebook nguyên trạng khi demo vì MODE có thể đang FULL.\n'
    for name,(phase,role,func,test) in MODULES.items():
        code+=f'| [src/{name}](src/{name}) | {role} | {func} | {phase} |\n'
        tree=ast.parse((root/'src'/name).read_text())
        definitions=[f'{n.name} (dòng {n.lineno})' for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
        detail+=f'\n## src/{name}\n\n[Đọc mã](../02_MA_NGUON/src/{name}). {role}. Được gọi ở {phase}.\n\n**Đầu vào/đầu ra và hàm:** {func}.\n\n**Định nghĩa thực tế:** '+', '.join(definitions)+f'.\n\n**Kiểm tra:** `{test}`.\n\n**Lý do thiết kế:** tách trách nhiệm này khỏi điều phối để kiểm tra độc lập và giữ split guard rõ ràng. **Rủi ro:** phải truyền đúng split, schema và phiên bản; xem các điều kiện lỗi trong mã. Không khẳng định mọi rủi ro đã được kiểm thử.\n'
    code+='\nCác file ngoài src: `run_all.py` điều phối CLI; `configs/*.yaml` là protocol; `notebooks/*.ipynb` là giao diện Colab; `scripts/create_notebooks.py` tái tạo notebook; `scripts/validate_workspace.py` audit nhưng ghi bảng gốc; `scripts/prepare_acceptance.py` tạo báo cáo SMOKE lịch sử. Không chạy hai script sau trên experiment khóa khi chỉ cần đọc bằng chứng. `tests/test_core.py` kiểm tra toán/split, test_integration có training synthetic, test_notebook_p2/p4 và test_runner dùng mock.\n'
    w('02_MA_NGUON/CODE_INDEX.md',code);w('06_CHUAN_BI_BAO_VE/GIAI_THICH_CODE_THEO_FILE.md',detail+'\nLỗi từng xử lý được ghi nhận trong IMPLEMENTATION lịch sử: float32 softmax gây cảnh báo normalization, đã chuẩn hóa float64 trước metric. Rủi ro còn lại: drift thư viện thay ID, Colab shortcut, quy trình ghi đồng thời, và metadata báo cáo cũ.\n')
    manifest=json.loads((root/'data/raw/dataset_manifest.json').read_text())
    rows=[]
    for ds,e in manifest['datasets'].items():rows.append([ds,e['verified_shape'][0],e['verified_shape'][1],e['verified_classes'],e['sha256'],e['source_url']])
    w('03_DU_LIEU/DATASET_PROVENANCE.md','# Nguồn dữ liệu và quyền phân phối\n\nKiểm tra trang UCI ngày 2026-11-10: cả ba dataset được ghi CC BY 4.0; được chia sẻ khi ghi công. [Điều khoản](https://creativecommons.org/licenses/by/4.0/). Tệp raw được sao chép byte-for-byte, chỉ tên chuẩn hóa từ bản tải đã có; không thay giá trị. Dữ liệu Bank là bộ nghiên cứu công khai, không kèm ID tài khoản cá nhân của chủ workspace.\n\n'+table(pd.DataFrame(rows,columns=['Dataset','Rows','Features','Classes','SHA-256','Source']))+'''
## Trích dẫn

- Dry Bean [Dataset] (2020), UCI, DOI [10.24432/C50S4B](https://doi.org/10.24432/C50S4B). Công trình liên quan: Koklu và Özkan (2020), Multiclass classification of dry beans using computer vision and machine learning techniques. [Trang nguồn và license](https://archive.ics.uci.edu/dataset/602/dry+bean+dataset).
- Rice (Cammeo and Osmancik) [Dataset] (2019), UCI, DOI [10.24432/C5MW4Z](https://doi.org/10.24432/C5MW4Z). Công trình: Cinar và Koklu (2019), Classification of Rice Varieties Using Artificial Intelligence Methods. [Trang nguồn và license](https://archive.ics.uci.edu/dataset/545/rice+cammeo+and+osmancik).
- Moro, Rita và Cortez (2014), Bank Marketing [Dataset], UCI, DOI [10.24432/C5K306](https://doi.org/10.24432/C5K306). [Trang nguồn và license](https://archive.ics.uci.edu/dataset/222/bank+marketing).

Chọn đúng bank-additional-full.csv: 41.188 hàng, 20 input; không nhầm bank-full.csv 45.211 hàng. UCI mô tả thứ tự ngày từ 05/2008 đến 11/2010; file không đủ timestamp để tái dựng độc lập. Để tải lại, dùng source_url trong manifest, giải nén đúng ARFF/CSV, đặt tên raw_file và đối chiếu SHA-256. Các archive gốc không cần cho pipeline readiness. Bank bỏ duration trong prepare_features và thêm previously_contacted nên số input sau xử lý vẫn 20, nhưng ý nghĩa đã đổi. Không fit lại dữ liệu khi đọc bằng chứng.
''')
    return w

def write_defense(w,results):
    limits='''# Hạn chế và hướng phát triển

Hiệu quả không đồng đều giữa mô hình và dataset. Một số hệ số bằng 0 làm CPCR suy biến thành MSP nhưng vẫn tính perturbation nên còn overhead. Rice có trường hợp AURC tăng; Dry Bean RF cải thiện trung bình nhưng C3 có delta dương. Không diễn giải trung bình toàn điều kiện thành thắng ở từng điều kiện.

Chi phí tăng vì B lần dự đoán thêm, preprocessing và ECDF; tỷ lệ risk_seconds/inference_seconds trong báo cáo là overhead, không phải tổng latency. Tổng chi phí gần base+overhead, phụ thuộc phần cứng. Không benchmark lại trong đóng gói.

Nhiễu tổng hợp không bao quát cơ chế thiếu dữ liệu thật, lỗi thu thập có cấu trúc, drift nhãn hay tấn công. Clipping theo Train có thể làm mất tín hiệu ngoại suy; đặc trưng hình học nhiễu độc lập không nhất thiết tương ứng một hạt khả thi.

Bank chia theo thứ tự thời gian có dịch chuyển tỷ lệ yes. Không có client ID và timestamp đầy đủ nên không thể loại hết repeated-client leakage hoặc chứng minh nguyên nhân drift. Accuracy cao trên Train/Model-Val mất cân bằng không đảm bảo Macro-F1 hoặc recall yes tốt; phải xem confusion matrix Test đã lưu.

Năm seed không độc lập vì lặp lại các hàng; Bank cùng một split. CI bootstrap có điều kiện trên mô hình và dữ liệu đã quan sát, không mô tả Train mới, không hiệu chỉnh nhiều so sánh. Không kết luận hiệu quả tổng quát từ ba dataset.

Tính mới chưa được xác nhận bằng khảo sát công trình liên quan độc lập. Cần khảo sát uncertainty, consistency, selective prediction và conditional ranking; thêm nhiều dataset, cơ chế nhiễu thật, baseline mạnh, calibration theo drift, sensitivity bins/min_size, ngân sách latency và đánh giá ngoài miền. Những việc này là kế hoạch tương lai trên protocol mới, không sửa kết quả Test đã xem.

Gói nghiệm thu giữ bảng và bằng chứng có chọn lọc, không chứa toàn bộ model/cache. Đọc lại các bảng và chạy demo là tái lập kiểm tra; tái tạo FULL từ đầu cần huấn luyện và môi trường tương thích, không nằm trong lần nghiệm thu này. Đồng bộ cloud và chạy Colab trực tiếp chưa được xác minh.
'''
    w('06_CHUAN_BI_BAO_VE/HAN_CHE_VA_HUONG_PHAT_TRIEN.md',limits)
    groups={
'A. Kiến thức Machine Learning':[
('Phân loại dữ liệu bảng là gì?','Học ánh xạ từ vector thuộc tính tới nhãn rời rạc. Trong dự án, predict_proba trả phân phối, argmax cho nhãn; CPCR chỉ thay thứ tự ưu tiên kiểm tra.'),
('Accuracy khác confidence thế nào?','Accuracy cần nhãn thật và đo tỷ lệ đúng. Confidence là max xác suất dự đoán của từng mẫu, có thể cao khi sai.'),
('Feature corruption khác label noise thế nào?','Dự án làm thiếu, nhiễu hoặc lượng tử hóa X, giữ y. Không đánh giá nhiễu nhãn huấn luyện.'),
('Selective prediction là gì?','Nhận mẫu có risk≤ngưỡng, từ chối phần còn lại. Phải báo cả coverage và risk, vì giảm coverage thường giúp giảm risk.'),
('Tại sao không cần mạng mới?','Câu hỏi nghiên cứu là điểm hậu xử lý trên mô hình cố định. LR, RF, MLP cung cấp các họ mô hình để kiểm tra mức phụ thuộc mô hình.'),
('Leakage xảy ra khi nào?','Khi thông tin từ Test tác động vào fit, chọn hệ số hoặc threshold. Việc audit schema và chia tập cố định khác với dùng kết quả dự đoán Test để lựa chọn.')],
'B. LR, RF, MLP':[
('LR hoạt động thế nào?','Logistic Regression học điểm tuyến tính và xác suất lớp; C=1, max_iter=2000 trong configs/models.yaml. Nó cần scaling số để tối ưu ổn định.'),
('RF hoạt động thế nào?','Random Forest gộp nhiều cây; cấu hình 200 cây và min_samples_leaf=2. Pipeline RF không StandardScaler; median/one-hot vẫn có.'),
('MLP có kiến trúc gì?','Hai tầng ẩn 64 và 32, ReLU, Adam lr=.001, batch=128; tối đa 100 epoch, patience=10 theo Model-Val cross entropy.'),
('Checkpoint MLP chọn theo Test không?','Không. models.train lưu best theo val loss từ Model-Val; Test không được truyền vào train.'),
('Categorical chưa thấy xử lý thế nào?','OneHotEncoder(handle_unknown=ignore) mã hóa thành các số 0 của nhóm cột đó. Đây không phải học thêm category từ Test.'),
('Tại sao inference CPU dù train có GPU?','Mã đưa estimator MLP về CPU khi lưu; benchmark inference nhất quán CPU. Không suy ra latency GPU/production từ số đo này.')],
'C. CPCR và công thức':[
('Tại sao cần CPCR nếu MSP đã khá tốt?','Giả thuyết là bất ổn dưới nhiễu nhẹ bổ sung tín hiệu lỗi ngoài confidence. Kết quả chỉ hỗ trợ ở một số cặp dataset/model; không có bảo đảm hơn MSP.'),
('Nếu λ=γ=0 thì phương pháp mới đóng góp gì?','Điểm đúng bằng MSP risk. Cấu hình đó không chứng minh lợi ích của thành phần mới; nó cho thấy lựa chọn phát triển đã quay về baseline. Chi phí hiện tại vẫn có thể tăng.'),
('λ=0 có đủ để thành MSP không?','Không khi γ≠0: còn γuq. Ví dụ u=.2,q=.5,γ=1 cho R=.3 thay vì .2.'),
('Tại sao dùng Jensen–Shannon divergence?','JS đối xứng, hữu hạn và có cận ln2 với natural log. Chia ln2 cho thang [0,1]; đó là lý do toán học hợp lý, chưa phải bằng chứng JS tối ưu.'),
('Tại sao cần conditional ECDF?','So sánh instability giữa mẫu có uncertainty tương tự để giảm ảnh hưởng mức confidence nền. Bin nhỏ dùng pooled Model-Val; lợi ích thực tế cần so ablation raw_instability.'),
('q có phải xác suất sai không?','Không. q là tỷ lệ instability tham chiếu không vượt giá trị đang xét. Nó không dùng nhãn sai/đúng để ước lượng trực tiếp posterior lỗi.')],
'D. Quy trình P1–P5':[
('Vì sao phải tách Risk-Val và Calibration?','Risk-Val dùng tối ưu hệ số; Calibration đặt order statistic ngưỡng trên tập riêng. Tách vai trò tránh đặt ngưỡng ngay trên dữ liệu đã tối ưu risk.'),
('Vì sao không dùng Test để chọn λ và γ?','Sẽ gây selection bias và phá ý nghĩa held-out. select chỉ cho risk_val, không nhận quantization; Test chỉ sau freeze.'),
('Frozen protocol chứa gì?','Experiment ID, signature source/config/versions/raw manifest, hash artifacts, selections và thresholds, development conditions, ECDF policy, test_opened=False tại thời điểm P4.'),
('BANK_EXTENSION=False trong config có mâu thuẫn không?','Experiment.__init__ quyết định Bank bằng đối số bank và mode FULL. Danh sách datasets trong signature chính thức có Bank; giá trị YAML false không tự quyết định run này. Cần truyền --bank khi tái tạo.'),
('450 tổ hợp được đếm ra sao?','3 dataset×3 model×5 seed×10 điều kiện tại B=8. Các scorer, target coverage và B4/16 tạo nhiều dòng CSV nhưng không tăng số tổ hợp chính.'),
('Vì sao giữ experiment cũ?','Làm lịch sử và truy vết. full-37245e523b162876 chỉ hai dataset, không trộn với full-62500e11e892b899 để đưa ra kết luận chính.')],
'E. Metric':[
('AURC tính thế nào?','Sắp risk tăng dần; tại k lấy cumulative errors/k; AURC là mean qua k=1…n. Mã dùng discrete right sum, không trapezoid.'),
('AUGRC khác AURC ở đâu?','Generalized risk chia cumulative errors cho n thay vì k. AUGRC là mean các giá trị đó, xem metrics.curve/ranking.'),
('Failure AUROC là gì?','Mẫu dự đoán sai là positive, score cao nên tương ứng sai. Undefined khi chỉ có một lớp correctness; không đổi thành 0 hay 1.'),
('AURC giảm có đồng nghĩa accuracy tăng không?','Không. Cùng dự đoán và nhãn, đổi risk chỉ đổi thứ tự nhận. Ở coverage 100%, mọi scorer có cùng tỷ lệ lỗi phân loại.'),
('Risk@90% khác realized risk ở target .9 thế nào?','Risk@90% chọn ceil(.9n) trên thứ hạng Test. Realized risk dùng ngưỡng Calibration cố định; coverage Test có thể khác .9 do drift hoặc ties.'),
('Xử lý điểm bằng nhau thế nào?','curve dùng cumulative error kỳ vọng của thứ tự ngẫu nhiên trong nhóm đồng điểm; deployment nhận tất cả mẫu ≤threshold, nên có thể vượt target.')],
'F. Kết quả Dry Bean, Rice, Bank':[
('Dry Bean RF cải thiện bao nhiêu?','Delta AURC trung bình CPCR−MSP khoảng −.00107813 ở B8; C3 lại +.000100523. Cải thiện toàn điều kiện không đồng nghĩa chuyển tốt sang C3.'),
('Vì sao Dry Bean LR và MLP trùng MSP?','Đối chiếu selections B8 trong freeze: các cặp λ=γ=0 làm risk đúng bằng u. Đây là kết quả chọn trên Risk-Val, không giải thích bằng việc mô hình hoàn hảo.'),
('Rice có tốt hơn không?','LR delta +.0000124433, MLP +.0000624486, RF −.000167598 trung bình; RF C3 +.000157145. Không thể kết luận thắng đồng đều hoặc lợi ích mạnh.'),
('Bank có Accuracy cao nhưng Macro-F1 thấp vì sao?','Mất cân bằng nhãn có thể thưởng mô hình thiên về no; Macro-F1 cho hai lớp trọng số ngang nhau. Phải chỉ rõ split và xem bảng confusion matrix trích cache trong RESULTS_EXPLAINED, không lấy accuracy Model-Val thay Test.'),
('Vì sao Bank có thay đổi phân phối nhãn lớn?','Tỷ lệ yes theo split được tính trực tiếp từ CSV và split indices. UCI xác nhận thứ tự thời gian; nguyên nhân chiến dịch/kinh tế là giả thuyết chưa được chứng minh bằng dữ liệu này.'),
('Có thể nói Bank chỉ dự đoán no không?','Chỉ được nói trong những model/seed/condition mà predicted_counts lớp yes bằng 0. Báo cáo có số đếm từ cache; không suy rộng một confusion matrix sang mọi điều kiện.')],
'G. Ablation, thống kê, tái lập':[
('B4/B16 có chỉ thay số lần perturb không?','Mỗi B có ECDF, lựa chọn hệ số và threshold riêng, tất cả trước Test. Đây là so sánh pipeline được tune riêng theo ngân sách B.'),
('no_q và uncertainty_only khác nhau không?','Không, cùng trả u trong risk_baselines.score; phải ghi rõ alias để tránh trình bày thành hai bằng chứng độc lập.'),
('Tại sao bootstrap theo row ID?','Một hàng xuất hiện ở nhiều seed/condition; resample đồng bộ giữ phụ thuộc và ghép cặp scorer. Bank dùng block thời gian cố định theo sqrt(n).'),
('CI có chứng minh tổng quát không?','Không. Là CI có điều kiện trên model/split và samples hiện có, không mô tả Train mới, không hiệu chỉnh đa kiểm định.'),
('Tại sao chi phí suy luận tăng?','B=8 cần thêm 8 lượt predict với preprocessing, tính JS và ECDF. Ngay hệ số 0 pipeline hiện vẫn tính, nên risk bằng MSP không đồng nghĩa chi phí bằng MSP.'),
('Tái lập tuyệt đối trên máy khác được không?','Không bảo đảm bitwise. Hash source/config/data và phiên bản giúp truy vết; Python/hardware/library drift có thể đổi ID và giá trị. Demo được kiểm thử riêng, không thay chứng cứ môi trường gốc.')],
'H. Phản biện khoa học':[
('Tính mới của phương pháp đã được chứng minh chưa?','Chưa. Gói audit kiểm tra thực thi và bằng chứng nội bộ; cần khảo sát tài liệu độc lập và so sánh phương pháp liên quan.'),
('Tại sao CPCR thất bại hoặc không cải thiện?','Instability có thể không bổ sung tín hiệu, ECDF sparse/fallback, hoặc phân phối Test khác phát triển. Đây là các giả thuyết; bằng chứng trực tiếp là delta và selections, chưa có kiểm định nhân quả.'),
('Nghiên cứu còn thiếu thực nghiệm gì?','Dataset rộng hơn, nhiễu thực tế/có cấu trúc, baseline mạnh, sensitivity bins/min_size, external validation và ngân sách latency. Thực hiện ở protocol mới, không tune lại Test hiện có.'),
('Có dấu hiệu kết quả giả không?','Audit đối chiếu checksum, tổ hợp, metric CSV với cache lưu. Không phát hiện bất nhất nếu các check PASS; điều đó không phải chứng thực độc lập toàn bộ lịch sử chạy hoặc loại trừ mọi can thiệp ngoài log.'),
('Có nên chỉ báo kết quả tốt?','Không. Báo cả Rice tăng AURC, cấu hình suy biến MSP, C3 bất lợi, CI và overhead; bảng theo dataset/model tránh che khuất hiệu quả không đồng đều.'),
('Đóng góp nào hiện có bằng chứng?','Có pipeline thực thi P1–P5, cơ chế scoring, so sánh có khóa protocol trên ba dataset, kết quả có điều kiện và giới hạn rõ. Chưa có chứng minh novelty, ưu thế phổ quát hoặc lợi ích triển khai thực tế.')]
}
    text='# 48 câu hỏi giảng viên và đáp án\n\nĐọc kèm RESULTS_EXPLAINED, GIAI_THICH_CPCR và mã nguồn. Số liệu chỉ experiment chính thức B8, trừ khi ghi khác.\n';n=0
    for group,items in groups.items():
        text+='\n## '+group+'\n'
        for q,a in items:n+=1;text+=f'\n### {n}. {q}\n\n{a}\n'
    w('06_CHUAN_BI_BAO_VE/CAU_HOI_GIANG_VIEN.md',text)
    w('06_CHUAN_BI_BAO_VE/KICH_BAN_THUYET_TRINH_5_PHUT.md','''# Kịch bản 5 phút

**0:00–0:45 — Bài toán.** Em nghiên cứu độ tin cậy của phân loại dữ liệu bảng khi thuộc tính bị thiếu, nhiễu hoặc làm tròn. Accuracy cho biết tỷ lệ đúng chung, nhưng chưa chỉ ra mẫu nào nên chuyển cho người kiểm tra.

**0:45–1:30 — Động lực.** MSP xếp mẫu tự tin trước. Một mẫu tự tin vẫn có thể thay đổi mạnh dưới nhiễu nhẹ. Em kiểm tra liệu tín hiệu bất ổn có bổ sung giá trị cho xếp hạng rủi ro hay không, trên bộ phân loại cố định.

**1:30–2:20 — CPCR.** u=1−max p. v là mean JS giữa đầu ra gốc và B=8 đầu ra nhiễu, chia ln2. q là percentile v trong nhóm uncertainty tương tự trên Model-Val. Điểm R=u+λq+γuq. Nếu cả hai hệ số bằng 0, đây đúng là MSP risk. Điểm thấp được ưu tiên nhận.

**2:20–3:10 — Thiết kế.** Ba dataset, ba mô hình LR/RF/MLP, năm seed, mười điều kiện tạo 450 tổ hợp chính. Model-Val fit ECDF, Risk-Val chọn hệ số, Calibration đặt ngưỡng. Test chỉ dùng sau frozen protocol. B4/B16 là ablation riêng.

**3:10–4:20 — Kết quả.** Dry Bean RF có delta AURC khoảng −.001078; LR/MLP trùng MSP. Rice LR/MLP tăng AURC nhẹ. Bank LR/MLP giảm khoảng .011624/.037847; RF trùng MSP. Các số này là trung bình toàn điều kiện. C3 trên Dry Bean RF lại bất lợi. AURC giảm không làm accuracy tăng vì classifier không đổi. Trình bảng RESULTS_EXPLAINED để chỉ rõ CI, nhãn Bank và confusion matrix.

**4:20–5:00 — Giới hạn.** Hiệu quả phụ thuộc mô hình, chi phí tăng và Bank có drift theo split. CI có điều kiện, chỉ ba dataset, tính mới chưa xác nhận. Em đề xuất khảo sát liên quan, nhiễu thực tế và đánh giá ngoài miền trong protocol mới. Gói hiện tại phục vụ kiểm tra học thuật, không tuyên bố thắng phổ quát.
''')
    w('06_CHUAN_BI_BAO_VE/KICH_BAN_THUYET_TRINH_15_PHUT.md','''# Kịch bản 15 phút

**0–2 phút: phát biểu bài toán.** Cho classifier f đã fit, p=f(x) và lỗi e=1[argmax p≠y]. Tìm điểm R(x) tăng theo rủi ro, nhận mẫu R≤t. Phân biệt accuracy, confidence, failure detection, risk ranking và selective risk. Mục tiêu thực nghiệm là AURC thấp hơn trên cùng dự đoán.

**2–5 phút: công thức và ví dụ.** Viết u=1−max p; v=(1/B)Σ JS(p,p_b)/ln2; q=ECDF(v|bin(u)); R=u+λq+γuq. Trình ví dụ u=.2,q=.5,λ=.25,γ=.5 cho .375. Giải thích Model-Val quantile bins, right-continuity, fallback dưới 20 mẫu, JS clip và B=8. Chứng minh λ=0 chưa đủ, λ=γ=0 cho MSP. Demo 8 mẫu Model-Val bằng checkpoint LR; thứ hạng trùng là kết quả đúng khi hệ số đều 0.

**5–7 phút: dữ liệu và mô hình.** Dry Bean 13.611×16, Rice 3.810×7, Bank additional 41.188×20. Raw checksum/CC BY 4.0; split 60/10/10/10/10 gần đúng, nhóm đặc trưng trùng không giao nhau. Bank giữ thứ tự, bỏ duration, xử lý pdays=999, purge trùng về sau. LR C=1, RF 200 cây, MLP 64/32; Model-Val chọn epoch, preprocessing chỉ Train.

**7–9 phút: protocol và leakage.** Trình sơ đồ năm split. Risk-Val trung bình AURC clean/C1/C2 chọn hệ số grid [0,.25,.5,1,2], hòa lấy hệ số nhỏ. Calibration clean order statistic ceil(nc), ties nhận toàn bộ. P4 đóng hash dữ liệu/artifacts/code/config/versions và selections; P5 kiểm tra trước Test. Không dùng C3 để chọn hệ số. Audit chỉ đọc cache, không đánh giá Test lại.

**9–12 phút: bảng kết quả thật.** Dùng bảng sau; delta âm có lợi. Chỉ rõ cấu hình trùng MSP qua selections. Đọc thêm CI toàn điều kiện và C3 trong RESULTS_EXPLAINED; không gộp dataset. Giải thích Bank bằng tỷ lệ yes theo split và predicted_counts, tránh khẳng định mọi mô hình chỉ no. So sánh accuracy với Macro-F1 trên cùng split.

'''+results+'''
**12–13:30: ablation và thống kê.** B4/B16 được tune riêng; no_interaction bỏ γ, raw_instability thay q bằng v; no_q/uncertainty_only là alias. Xem bảng ablation đầy đủ thay vì chọn một hàng thuận lợi. Bootstrap theo row ID, Bank circular block, 1.000 lần, CI percentile; không coi seed độc lập, không hiệu chỉnh nhiều so sánh. Overhead là risk/base, tổng latency còn gồm base.

**13:30–15: giới hạn và đóng góp.** Đã có bằng chứng cho pipeline khóa, tính toán score và kết quả có điều kiện trong bảng. Chưa chứng minh novelty, vượt MSP phổ quát, hoặc đủ tốt cho triển khai. Hướng tiếp theo: literature review, thêm dataset/nhiễu thật, baseline mạnh và latency budget. Không tune lại Test hiện tại sau khi thấy kết quả.
''')
