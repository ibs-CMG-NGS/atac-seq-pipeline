# ATAC-seq Pipeline Standardization - Executive Summary

## 📌 개요

RNA-seq 파이프라인에 적용된 입출력 표준화를 ATAC-seq 파이프라인에도 동일하게 적용하여 에이전트 기반 통합 관리 체계를 구축합니다.

---

## 🎯 핵심 목표

### 1. 샘플 시트 통일
- **Before**: 각 파이프라인마다 다른 형식 사용
  - Nextflow ATAC-seq: `samplesheet.csv` (sample, fastq_1, fastq_2, replicate)
  - Snakemake RNA-seq: `samples.tsv` (sample_id, condition, replicate, fastq_r1, fastq_r2)
  - WDL WGS: `inputs.json`

- **After**: 모든 파이프라인이 동일한 `samples.csv` 사용
  - 마스터 샘플 시트: `samples.csv` (project_id, sample_id, condition, replicate, ...)
  - 에이전트가 파이프라인별 형식으로 자동 변환

### 2. 출력 디렉토리 구조 강제
- **Before**: 파이프라인마다 다른 출력 구조
  ```
  # nf-core/atacseq
  results/
  ├── fastqc/
  ├── bwa/
  └── multiqc/
  
  # Snakemake RNA-seq
  results/
  ├── trimmed/
  ├── aligned/
  └── counts/
  ```

- **After**: 표준 구조로 통일
  ```
  /home/ngs/data/results/
  └── {PROJECT_ID}/
      ├── metadata/
      ├── {SAMPLE_ID}/
      │   └── {PIPELINE_TYPE}/
      │       ├── final_outputs/      # ⭐ 에이전트가 읽을 파일
      │       ├── intermediate/        # 중간 파일
      │       └── metadata/
      └── project_summary/             # 프로젝트 전체 요약
  ```

### 3. Final vs Intermediate 명확한 분리
- **Final outputs**: 에이전트가 3차 분석에 사용할 최종 결과물
  - BAM 파일, Peak 파일, BigWig, QC 리포트
- **Intermediate**: 분석 과정에서 생성된 중간 파일
  - Trimmed FASTQ, 중간 로그, 임시 파일

---

## 📂 표준 디렉토리 구조

### ATAC-seq 예시
```
/home/ngs/data/results/
└── H2O2_Astrocyte_2025/                    # PROJECT_ID
    │
    ├── metadata/
    │   ├── samples_master.csv              # 마스터 샘플 시트
    │   └── samplesheet_nextflow.csv        # Nextflow용 변환 시트
    │
    ├── CONTROL_REP1/                       # SAMPLE_ID
    │   └── atac-seq/                       # PIPELINE_TYPE
    │       ├── final_outputs/              # ⭐ 최종 결과물
    │       │   ├── bam/
    │       │   │   ├── aligned.sorted.bam
    │       │   │   └── aligned.sorted.bam.bai
    │       │   ├── peaks/
    │       │   │   └── broad_peaks.bed
    │       │   ├── bigwig/
    │       │   │   └── coverage.bigWig
    │       │   ├── qc/
    │       │   │   └── qc_summary.json
    │       │   └── manifest.json           # 메타데이터
    │       ├── intermediate/
    │       │   ├── trimmed/
    │       │   ├── fastqc/
    │       │   └── logs/
    │       └── metadata/
    │
    ├── CONTROL_REP2/
    │   └── atac-seq/ ...
    │
    └── project_summary/                    # 프로젝트 전체
        ├── qc/
        │   └── multiqc_report.html
        └── peaks/
            └── consensus_peaks_all.bed
```

---

## 🔧 구현 방법

### Phase 1: 변환 스크립트 작성

#### 1. 샘플 시트 변환 (`bin/convert_samplesheet.py`)
```bash
# 마스터 샘플 시트를 Nextflow 형식으로 변환
python bin/convert_samplesheet.py \
    samples.csv \
    -o samplesheet.csv \
    -p nextflow-atac
```

**기능**:
- `samples.csv` 읽기 및 검증
- ATAC-seq 샘플만 필터링
- Nextflow samplesheet.csv 형식으로 변환
- FASTQ 파일 존재 확인

#### 2. 출력 재구성 (`bin/reorganize_outputs.py`)
```bash
# nf-core 출력을 표준 구조로 재구성
python bin/reorganize_outputs.py \
    ./results \
    /home/ngs/data/results \
    samples.csv \
    --project-id H2O2_Astrocyte_2025
```

**기능**:
- 표준 디렉토리 구조 생성
- nf-core 출력 파일을 표준 위치로 복사/이동
- 샘플별 `manifest.json` 생성
- 프로젝트 전체 요약 생성

---

### Phase 2: manifest.json 생성

각 샘플의 최종 결과물에 대한 메타데이터를 JSON으로 저장:

```json
{
  "sample_id": "CONTROL_REP1",
  "project_id": "H2O2_Astrocyte_2025",
  "pipeline": "atac-seq",
  "pipeline_version": "nf-core/atacseq v2.1.2",
  "genome_build": "GRCm39",
  
  "final_outputs": {
    "bam": {
      "aligned_bam": "bam/aligned.sorted.bam",
      "file_size_mb": 4521,
      "read_count": 504804
    },
    "peaks": {
      "broad_peaks": "peaks/broad_peaks.bed",
      "peak_count": 3767,
      "frip_score": 0.7796
    }
  },
  
  "qc_metrics": {
    "frip_score": 0.7796,
    "peak_count": 3767,
    "alignment_rate": 1.0,
    "duplicate_rate": 0.015
  },
  
  "analysis_status": "complete"
}
```

**에이전트 활용**:
- QC 평가: `qc_metrics.frip_score > 0.3` → PASS
- 파일 위치: `final_outputs.bam.aligned_bam` 경로 확인
- 다음 분석: `analysis_status == "complete"` 확인

---

## 📊 적용 전후 비교

### Before: 에이전트가 겪는 어려움
```
❌ 문제 1: "이 샘플의 BAM 파일이 어디 있지?"
   → results/bwa/mergedLibrary/CONTROL_REP1.mLb.clN.sorted.bam
   → 파이프라인마다 경로가 달라서 찾기 어려움

❌ 문제 2: "FRiP score가 얼마지?"
   → results/multiqc/broad_peak/multiqc_data/multiqc_mlib_frip_score-plot.txt
   → 파싱 복잡, 포맷 다양

❌ 문제 3: "어떤 파일이 최종 결과물이지?"
   → trimmed FASTQ, intermediate BAM, final BAM 모두 혼재
   → 에이전트가 판단하기 어려움
```

### After: 에이전트 친화적 구조
```
✅ 해결 1: "BAM 파일 위치"
   → {sample}/atac-seq/final_outputs/bam/aligned.sorted.bam
   → 항상 동일한 경로

✅ 해결 2: "QC 메트릭"
   → {sample}/atac-seq/final_outputs/manifest.json
   → 구조화된 JSON, 파싱 간단

✅ 해결 3: "최종 결과물 구분"
   → final_outputs/ : 최종 결과
   → intermediate/ : 중간 파일
   → 명확한 분리
```

---

## 🚀 에이전트 워크플로우

### 1단계: 사용자 요청
```
User: "H2O2 astrocyte ATAC-seq 분석해줘"
```

### 2단계: 에이전트 준비
```python
# 1. samples.csv 확인 또는 생성
if not exists("samples.csv"):
    create_from_user_input()

# 2. 프로젝트 디렉토리 생성
project_dir = f"/home/ngs/data/results/{project_id}"
create_directory(project_dir)

# 3. Nextflow samplesheet 변환
run("python bin/convert_samplesheet.py samples.csv -o samplesheet.csv")
```

### 3단계: 파이프라인 실행
```bash
nextflow run . \
    -profile singularity \
    --input samplesheet.csv \
    --outdir results_temp
```

### 4단계: 결과 재구성
```bash
python bin/reorganize_outputs.py \
    results_temp \
    /home/ngs/data/results \
    samples.csv \
    --project-id H2O2_Astrocyte_2025
```

### 5단계: QC 평가 및 리포트
```python
# manifest.json 읽기
for sample in samples:
    manifest = read_json(f"{sample}/atac-seq/final_outputs/manifest.json")
    
    # QC 평가
    if manifest['qc_metrics']['frip_score'] < 0.3:
        warn(f"Low FRiP score: {sample}")
    
    if manifest['qc_metrics']['peak_count'] < 1000:
        warn(f"Low peak count: {sample}")

# MultiQC 리포트 확인
open_browser(f"{project_dir}/project_summary/qc/multiqc_report.html")
```

---

## 📋 구현 타임라인

| Phase | 작업 | 소요 시간 | 상태 |
|-------|-----|----------|------|
| **Phase 1** | 스크립트 작성 | 1-2일 | 📝 계획 |
| | - convert_samplesheet.py | 0.5일 | |
| | - reorganize_outputs.py | 1일 | |
| | - generate_manifest.py | 0.5일 | |
| **Phase 2** | 마스터 샘플 시트 | 0.5일 | 📝 계획 |
| | - samples_H2O2_astrocyte.csv | 0.5일 | |
| **Phase 3** | 기존 결과 재구성 | 1일 | 📝 계획 |
| | - H2O2 결과 재구성 테스트 | 0.5일 | |
| | - QC 메트릭 추출 | 0.5일 | |
| **Phase 4** | 신규 워크플로우 테스트 | 1일 | 📝 계획 |
| | - 3개 샘플 테스트 | 1일 | |
| **Phase 5** | 문서화 | 0.5일 | ✅ 완료 |
| | - ATAC_STANDARDIZATION.md | ✅ | |
| | - ATAC_IMPLEMENTATION_PLAN.md | ✅ | |

**총 예상 기간**: 4-5일

---

## ✅ 성공 기준

### 기술적 기준
- [x] 표준화 문서 작성 완료
- [ ] `convert_samplesheet.py` 정상 동작
- [ ] `reorganize_outputs.py` 정상 동작
- [ ] 모든 샘플의 `manifest.json` 생성
- [ ] MultiQC 데이터 manifest 통합

### 비즈니스 기준
- [ ] RNA-seq, ATAC-seq 디렉토리 구조 통일
- [ ] 에이전트가 manifest.json만으로 QC 평가 가능
- [ ] Final/Intermediate 명확 분리
- [ ] 3개 파이프라인(RNA, ATAC, WGS) 표준 일치

---

## 🎯 다음 단계

### 즉시 시작 가능
1. **`bin/convert_samplesheet.py` 작성** (0.5일)
2. **`samples_H2O2_astrocyte.csv` 작성** (0.5일)
3. **기존 H2O2 결과 재구성 테스트** (1일)

### 의사결정 필요
- [ ] 표준 base directory: `/home/ngs/data/results/` 사용?
- [ ] Project ID 네이밍: `{Treatment}_{Species}_{Year}` 형식?
- [ ] 기존 결과 보존: 재구성 후 원본 유지?

---

## 📚 관련 문서

- **표준화 가이드**: [ATAC_STANDARDIZATION.md](./ATAC_STANDARDIZATION.md)
- **구현 계획**: [ATAC_IMPLEMENTATION_PLAN.md](./ATAC_IMPLEMENTATION_PLAN.md)
- **RNA-seq 표준화**: `~/ngs-pipeline/rna-seq-pipeline/docs/reference/STANDARDIZATION.md`
- **H2O2 QC 분석**: [이전 대화 참조] - FRiP 0.76-0.83, Peak 2,200-4,600

---

## 💡 핵심 이점

### For Human Users
- ✅ 모든 프로젝트가 동일한 구조
- ✅ 결과 찾기 쉬움
- ✅ 파이프라인 변경 시에도 일관성 유지

### For AI Agents
- ✅ 예측 가능한 경로
- ✅ 구조화된 메타데이터 (manifest.json)
- ✅ Final/Intermediate 자동 구분
- ✅ QC 자동 평가 가능

### For Collaboration
- ✅ 파이프라인 간 결과 비교 용이
- ✅ 데이터 공유 표준화
- ✅ 재현성 향상
