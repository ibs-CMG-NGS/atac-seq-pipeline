# ATAC-seq Pipeline Standardization - Executive Summary

> **최종 업데이트**: 2026-04-24  
> **구현 상태**: Phase 1~3 완료 ✅

## 📌 개요

nf-core/atacseq 파이프라인 실행 후 3차 분석에 필요한 파일들을 표준 디렉토리 구조로 자동 정리하는 Snakemake 기반 post-pipeline 워크플로우를 구축했습니다.  
에이전트 기반 통합 관리(manifest.json)와 재현성을 핵심 목표로 합니다.

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

## 📂 실제 구현된 디렉토리 구조

### analysis_ready 출력 구조
```
/home/ngs/data/ygkim/2026/analysis_ready/
└── 2026-ben-mouse-atac/                  ← batch 이름 (config.yaml의 results_dir)
    ├── CONTROL_REP1/
    │   ├── final_outputs/
    │   │   ├── bam/
    │   │   │   ├── CONTROL_REP1.mLb.clN.sorted.bam     → symlink
    │   │   │   └── CONTROL_REP1.mLb.clN.sorted.bam.bai → symlink
    │   │   ├── peaks/
    │   │   │   ├── CONTROL_REP1_peaks.broadPeak         (복사)
    │   │   │   └── CONTROL_REP1_peaks.annotatePeaks.txt (복사)
    │   │   ├── bigwig/
    │   │   │   └── CONTROL_REP1.mLb.clN.bigWig          → symlink
    │   │   └── qc/
    │   │       └── CONTROL_REP1.ataqv.json              (복사)
    │   └── manifest.json                ← QC 메트릭 + 파일 경로 통합
    ├── CONTROL_REP2/  ...
    ├── consensus/
    │   ├── consensus_peaks.mLb.clN.bed
    │   ├── consensus_peaks.mLb.clN.annotatePeaks.txt
    │   └── consensus_peaks.mLb.clN.boolean.txt
    ├── ben_count_matrix.csv             ← DESeq2 raw counts (144,932 peaks × 18)
    ├── ben_peak_info.csv                ← 피크 좌표 + gene annotation
    ├── ben_sample_metadata.csv          ← 샘플 메타데이터
    └── README.txt                       ← QC 요약 + 사용법
```

### config.yaml 구조
```yaml
analysis_ready_dir: "/home/ngs/data/ygkim/2026/analysis_ready"

datasets_config:
  ben:
    results_dir: "2026-ben-mouse-atac"   # → analysis_ready/2026-ben-mouse-atac/
    genome: "GRCm38"
    peak_type: "broad"
  pym:
    results_dir: "2026-pym-mouse-atac"   # → analysis_ready/2026-pym-mouse-atac/
```

---

## 🔧 구현 방법

### ✅ 실제 구현: Snakemake post-pipeline 워크플로우

계획 단계의 단일 스크립트 방식 대신, Snakemake 워크플로우로 통합 구현되었습니다.

```
/home/ngs/data/ygkim/2026/post_pipeline/
├── Snakefile            # 메인 워크플로우 (3단계)
├── config.yaml          # 데이터셋 설정 (batch 이름, genome, conditions)
├── make_count_matrix.py # featureCounts → DESeq2용 count matrix
└── collect_analysis.py  # 표준 디렉토리 구조 구성 + manifest.json 생성
```

#### 실행 방법
```bash
cd /home/ngs/data/ygkim/2026
conda activate snakemake_env

# 전체 파이프라인 (dry-run)
snakemake -s post_pipeline/Snakefile -n --cores 4

# 전체 실행
snakemake -s post_pipeline/Snakefile --cores 8

# 특정 데이터셋만
snakemake -s post_pipeline/Snakefile --cores 4 \
    --config 'run_datasets=["ben"]'
```

#### 3단계 워크플로우
```
Rule 1: qc_report        → results/atac/atac_pipeline_report.html
Rule 2: count_matrix     → count_matrix/{ds}_count_matrix.csv
                           count_matrix/{ds}_peak_info.csv
                           count_matrix/{ds}_sample_metadata.csv
Rule 3: collect_analysis → analysis_ready/{batch_name}/  ← 표준 구조
```

#### 출력 디렉토리 설계
- `config.yaml`의 `analysis_ready_dir` + `results_dir`(= batch 이름) 조합
- 예: `analysis_ready_dir=/home/ngs/data/ygkim/2026/analysis_ready`, `results_dir=2026-ben-mouse-atac`
- → 최종 출력: `/home/ngs/data/ygkim/2026/analysis_ready/2026-ben-mouse-atac/`

### Phase 1: 변환 스크립트 (✅ 완료)

#### `post_pipeline/collect_analysis.py`  
_(계획 단계의 `bin/reorganize_outputs.py`를 대체)_

```bash
python3 post_pipeline/collect_analysis.py \
    --dataset    ben \
    --results    /home/ngs/data/ygkim/2026/2026-ben-mouse-atac/results \
    --outdir     /home/ngs/data/ygkim/2026/analysis_ready/2026-ben-mouse-atac \
    --matrix-dir /home/ngs/data/ygkim/2026/count_matrix
```

**기능**:
- featureCounts.txt에서 샘플 목록 자동 추출
- 대용량 파일(BAM, bigWig) → 심볼릭 링크
- 소용량 파일(peaks, ATAQv JSON) → 복사
- ATAQv JSON 파싱 → `manifest.json` 자동 생성
- QC 판정 (FRiP < 0.2 또는 TSS < 5.0 → WARN)

---

### Phase 2: manifest.json 생성 (✅ 완료)
```bash
# nf-core 출력을 표준 구조로 재구성 (Snakemake로 자동 실행됨)
python3 post_pipeline/collect_analysis.py \
    --dataset ben --results ./results \
    --outdir  /home/ngs/data/ygkim/2026/analysis_ready/2026-ben-mouse-atac \
    --matrix-dir /home/ngs/data/ygkim/2026/count_matrix
```

**기능**:
- 표준 디렉토리 구조 생성
- nf-core 출력 파일을 표준 위치로 복사/링크
- 샘플별 `manifest.json` 생성 (ATAQv 메트릭 통합)
- README.txt 생성 (QC 요약 포함)

---

### Phase 2: manifest.json 생성 (✅ 완료)

각 샘플의 최종 결과물에 대한 메타데이터를 JSON으로 저장 (`{sample}/manifest.json`):

```json
{
  "sample_id": "CONTROL_REP1",
  "pipeline": "atac-seq",
  "pipeline_tool": "nf-core/atacseq",
  "genome_build": "GRCm38",
  "peak_type": "broad",
  "created_at": "2026-04-24 15:39",
  "condition": "CONTROL",
  "replicate": "1",
  "final_outputs": {
    "bam": {
      "file":    "final_outputs/bam/CONTROL_REP1.mLb.clN.sorted.bam",
      "index":   "final_outputs/bam/CONTROL_REP1.mLb.clN.sorted.bam.bai",
      "size_mb": 3294.1,
      "type":    "symlink"
    },
    "peaks": {
      "broadpeak":  "final_outputs/peaks/CONTROL_REP1_peaks.broadPeak",
      "annotation": "final_outputs/peaks/CONTROL_REP1_peaks.annotatePeaks.txt",
      "type":       "copy"
    },
    "bigwig": {
      "file": "final_outputs/bigwig/CONTROL_REP1.mLb.clN.bigWig",
      "type": "symlink"
    },
    "qc": {
      "ataqv_json": "final_outputs/qc/CONTROL_REP1.ataqv.json",
      "type":       "copy"
    }
  },
  "qc_metrics": {
    "total_reads":     127812292,
    "hqaa":            92410885,
    "duplicate_reads": 22571695,
    "duplicate_rate":  0.1766,
    "mito_reads":      4651793,
    "mito_rate":       0.0364,
    "frip_score":      0.7842,
    "tss_enrichment":  7.811,
    "peak_count":      72177
  },
  "qc_status":       "PASS",
  "qc_warnings":     [],
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

## 📋 구현 현황

| Phase | 작업 | 상태 | 완료일 |
|-------|-----|------|-------|
| **Phase 1** | post-pipeline 스크립트 | ✅ 완료 | 2026-04-23 |
| | - `post_pipeline/collect_analysis.py` | ✅ | |
| | - `post_pipeline/make_count_matrix.py` | ✅ | |
| | - `post_pipeline/Snakefile` | ✅ | |
| | - `post_pipeline/config.yaml` | ✅ | |
| **Phase 2** | manifest.json 생성 | ✅ 완료 | 2026-04-23 |
| | - ATAQv JSON 파싱 (FRiP, TSS, dup_rate) | ✅ | |
| | - QC 자동 판정 (PASS/WARN) | ✅ | |
| **Phase 3** | 기존 결과 표준 구조로 재생성 | ✅ 완료 | 2026-04-24 |
| | - 2026-ben-mouse-atac (18 PASS) | ✅ | |
| | - 2026-pym-mouse-atac (12 WARN, FRiP 낮음) | ✅ | |
| | - 출력 경로: `analysis_ready/{batch_name}/` | ✅ | |
| **Phase 4** | 신규 워크플로우 테스트 | ✅ 완료 | 2026-04-24 |
| | - dry-run 검증 | ✅ | |
| | - ben/pym 전체 실행 | ✅ | |
| **Phase 5** | 문서화 | ✅ 완료 | 2026-04-24 |
| | - ATAC_STANDARDIZATION_SUMMARY.md | ✅ | |

---

## ✅ 성공 기준

### 기술적 기준
- [x] 표준화 문서 작성 완료
- [x] `post_pipeline/collect_analysis.py` 정상 동작
- [x] `post_pipeline/make_count_matrix.py` 정상 동작
- [x] 모든 샘플의 `manifest.json` 생성 (FRiP, TSS, dup_rate 포함)
- [x] ATAQv 데이터 manifest 통합

### 비즈니스 기준
- [x] 에이전트가 manifest.json만으로 QC 평가 가능
- [x] Final/Intermediate 명확 분리 (`final_outputs/` 서브폴더)
- [x] Batch 이름 기반 출력 폴더 (`analysis_ready/2026-ben-mouse-atac/`)
- [ ] RNA-seq, ATAC-seq 디렉토리 구조 통일 (RNA-seq 쪽 미적용)

---

## 🎯 다음 단계

### 신규 배치 추가 시
1. `config.yaml`에 새 dataset 블록 추가
2. nf-core/atacseq 실행
3. Snakemake post-pipeline 실행 → `analysis_ready/{batch_name}/` 자동 생성

### 향후 개선 과제
- [ ] RNA-seq 파이프라인에도 동일한 표준 구조 적용
- [ ] 샘플 시트 통합 변환 (`bin/convert_samplesheet.py`)
- [ ] 프로젝트 전체 QC 대시보드 (여러 batch 비교)

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
