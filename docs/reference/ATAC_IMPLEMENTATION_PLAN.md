# ATAC-seq Pipeline Standardization - Implementation Plan

## 🎯 목표
RNA-seq 파이프라인에 적용된 표준화를 ATAC-seq 파이프라인에 동일하게 적용하여 에이전트 기반 관리 체계 구축

---

## 📋 현재 상태 분석

### 현재 ATAC-seq 파이프라인
- **워크플로우 엔진**: Nextflow (nf-core/atacseq v2.1.2)
- **샘플 시트**: `samplesheet.csv` (condition, fastq_1, fastq_2, replicate)
- **출력 구조**: nf-core 기본 구조 (파이프라인 중심, 샘플별 분산)
- **메타데이터**: 최소한 (params.yaml에 일부 포함)

### RNA-seq 파이프라인 (표준 적용 완료)
- **워크플로우 엔진**: Snakemake
- **샘플 시트**: `samples.csv` (마스터) + `samples.tsv` (파이프라인용)
- **출력 구조**: 표준화됨 (`{project}/{sample}/{pipeline}/final_outputs/`)
- **메타데이터**: `manifest.json`, `qc_summary.json`

---

## 🔧 구현 단계

### Phase 1: 기반 스크립트 작성 (1-2일)

#### Task 1.1: 샘플 시트 변환 스크립트
**파일**: `bin/convert_samplesheet.py`

**기능**:
- `samples.csv` → `samplesheet.csv` 변환
- 파이프라인별 형식 지원 (Nextflow, Snakemake, WDL)
- 검증 로직 (FASTQ 존재 확인, 필수 컬럼 체크)

**구현 우선순위**: ⭐⭐⭐ (최우선)

**테스트 케이스**:
```bash
# H2O2 astrocyte 프로젝트로 테스트
python bin/convert_samplesheet.py \
    samples_master.csv \
    -o samplesheet_nextflow.csv \
    -p nextflow-atac
```

**Expected Output**:
```
📖 Read 15 samples from samples_master.csv
✅ Master sheet validation passed
✅ Converted 15 samples to Nextflow format: samplesheet_nextflow.csv

📊 Sample Summary:
   Total samples: 15
   Conditions: 5
   Condition breakdown:
      - Control: 3 replicates
      - H2O2_100uM: 3 replicates
      - H2O2_200uM: 3 replicates
      - D1: 3 replicates
      - D3: 3 replicates
```

---

#### Task 1.2: 출력 디렉토리 재구성 스크립트
**파일**: `bin/reorganize_outputs.py`

**기능**:
- nf-core/atacseq 출력 → 표준 구조로 재구성
- 샘플별 디렉토리 생성 (`final_outputs/`, `intermediate/`, `metadata/`)
- 프로젝트 전체 요약 디렉토리 생성
- `manifest.json` 생성

**구현 우선순위**: ⭐⭐⭐ (최우선)

**테스트 케이스**:
```bash
# 기존 H2O2 astrocyte 결과로 테스트
python bin/reorganize_outputs.py \
    /home/ngs/data/atac-seq-pipeline-results \
    /home/ngs/data/results \
    samples_master.csv \
    --project-id H2O2_Astrocyte_2025
```

**Expected Directory Structure**:
```
/home/ngs/data/results/H2O2_Astrocyte_2025/
├── CONTROL_REP1/atac-seq/final_outputs/
│   ├── bam/aligned.sorted.bam
│   ├── peaks/broad_peaks.bed
│   └── manifest.json
├── CONTROL_REP2/atac-seq/final_outputs/
└── project_summary/qc/multiqc_report.html
```

---

#### Task 1.3: manifest.json 생성기
**파일**: `bin/generate_manifest.py`

**기능**:
- 샘플별 최종 결과물 메타데이터 생성
- QC 메트릭 추출 (FRiP, peak count, alignment rate)
- 파일 크기, 경로 등 메타데이터 추가

**구현 우선순위**: ⭐⭐ (중요)

**Schema**:
```json
{
  "sample_id": "CONTROL_REP1",
  "project_id": "H2O2_Astrocyte_2025",
  "pipeline": "atac-seq",
  "pipeline_version": "nf-core/atacseq v2.1.2",
  "completion_date": "2026-02-03T17:38:00",
  "genome_build": "GRCm39",
  "aligner": "bwa",
  
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
    "duplicate_rate": 0.015,
    "mitochondrial_rate": 0.032
  },
  
  "analysis_status": "complete"
}
```

---

### Phase 2: 마스터 샘플 시트 생성 (0.5일)

#### Task 2.1: H2O2 Astrocyte 프로젝트용 samples.csv 생성
**파일**: `samples_H2O2_astrocyte.csv`

**내용**: 현재 `samplesheet_H2O2_astrocyte.csv` 기반으로 확장

**Before (현재)**:
```csv
sample,fastq_1,fastq_2,replicate
CONTROL,/home/ngs/data/.../Cont_1_1.fastq.gz,/home/ngs/data/.../Cont_1_2.fastq.gz,1
```

**After (표준)**:
```csv
project_id,sample_id,sample_name,condition,replicate,sequencing_platform,library_type,read_type,fastq_1,fastq_2,species,genome_build,cell_type,treatment,treatment_dose,time_point,notes
H2O2_Astrocyte_2025,CONTROL_REP1,Control_Rep1,Control,1,Illumina,ATAC-seq,paired-end,/home/ngs/data/.../Cont_1_1.fastq.gz,/home/ngs/data/.../Cont_1_2.fastq.gz,mouse,GRCm39,astrocyte,none,0,baseline,Control replicate 1
```

**구현 방법**:
1. 수동으로 작성 (15개 샘플이므로 빠름)
2. 또는 변환 스크립트 작성: `upgrade_samplesheet.py`

---

### Phase 3: 기존 결과 재구성 테스트 (1일)

#### Task 3.1: H2O2 Astrocyte 결과 재구성
**목표**: 이미 완료된 H2O2 astrocyte 분석 결과를 표준 구조로 변환

**현재 위치**: `/home/ngs/data/atac-seq-pipeline-results/`

**표준 위치**: `/home/ngs/data/results/H2O2_Astrocyte_2025/`

**실행 계획**:
```bash
# 1. 마스터 샘플 시트 생성
cd ~/ngs-pipeline/atac-seq-pipeline
nano samples_H2O2_astrocyte.csv

# 2. 재구성 실행
python bin/reorganize_outputs.py \
    /home/ngs/data/atac-seq-pipeline-results \
    /home/ngs/data/results \
    samples_H2O2_astrocyte.csv \
    --project-id H2O2_Astrocyte_2025

# 3. 검증
tree -L 4 /home/ngs/data/results/H2O2_Astrocyte_2025/
cat /home/ngs/data/results/H2O2_Astrocyte_2025/CONTROL_REP1/atac-seq/final_outputs/manifest.json
```

**검증 항목**:
- [ ] 15개 샘플 디렉토리 생성 확인
- [ ] BAM 파일 복사 확인 (aligned.sorted.bam)
- [ ] Peak 파일 복사 확인 (broad_peaks.bed)
- [ ] manifest.json 생성 확인
- [ ] MultiQC 리포트 복사 확인

---

#### Task 3.2: QC 메트릭 추출 테스트
**목표**: MultiQC 데이터를 manifest.json에 통합

**데이터 소스**: `/home/ngs/data/atac-seq-pipeline-results/multiqc/broad_peak/multiqc_data/`

**필요 메트릭**:
- FRiP score: `multiqc_mlib_frip_score-plot.txt`
- Peak count: `multiqc_mlib_peak_count-plot.txt`
- Alignment rate: `multiqc_picard_AlignmentSummaryMetrics.txt`

**구현**:
```python
def extract_qc_metrics(multiqc_dir, sample_id):
    """MultiQC 데이터에서 QC 메트릭 추출"""
    metrics = {}
    
    # FRiP score
    frip_file = multiqc_dir / 'multiqc_mlib_frip_score-plot.txt'
    df_frip = pd.read_csv(frip_file, sep='\t', index_col=0)
    metrics['frip_score'] = df_frip.loc[sample_id, sample_id]
    
    # Peak count
    peak_file = multiqc_dir / 'multiqc_mlib_peak_count-plot.txt'
    df_peak = pd.read_csv(peak_file, sep='\t', index_col=0)
    metrics['peak_count'] = int(df_peak.loc[sample_id].sum())
    
    return metrics
```

---

### Phase 4: 새 프로젝트 워크플로우 테스트 (1일)

#### Task 4.1: 전체 워크플로우 테스트 (소규모)
**시나리오**: 새로운 ATAC-seq 프로젝트 시뮬레이션

**테스트 데이터**: H2O2 astrocyte 중 3개 샘플만 선택 (CONTROL_REP1, D1_REP1, D3_REP1)

**워크플로우**:
```bash
# 1. 마스터 샘플 시트 작성
nano samples_test.csv

# 2. Nextflow samplesheet 변환
python bin/convert_samplesheet.py \
    samples_test.csv \
    -o samplesheet_test.csv \
    -p nextflow-atac

# 3. Nextflow 실행
nextflow run . \
    -profile singularity \
    -params-file params_test.yaml \
    --input samplesheet_test.csv \
    --outdir results_test

# 4. 표준 구조로 재구성
python bin/reorganize_outputs.py \
    results_test \
    /home/ngs/data/results \
    samples_test.csv \
    --project-id Test_ATAC_2026

# 5. 검증
ls -la /home/ngs/data/results/Test_ATAC_2026/*/atac-seq/final_outputs/manifest.json
```

**Expected Timeline**: 
- 준비: 30분
- Nextflow 실행: 2-3시간 (3개 샘플)
- 재구성: 10분
- 검증: 20분

---

### Phase 5: 문서화 및 통합 (0.5일)

#### Task 5.1: README 업데이트
**파일**: `README.md`

**추가 섹션**:
```markdown
## 표준화된 워크플로우

### 1. 마스터 샘플 시트 작성
모든 프로젝트는 `samples.csv`로 시작합니다:
...

### 2. Nextflow samplesheet 변환
...

### 3. 파이프라인 실행
...

### 4. 결과 재구성
...
```

---

#### Task 5.2: 에이전트 가이드 작성
**파일**: `docs/AGENT_GUIDE.md`

**내용**:
- 에이전트가 수행할 작업 순서
- manifest.json 파싱 방법
- QC 평가 기준
- 3차 분석으로 전달할 파일 목록

---

## 📅 타임라인

| Phase | Tasks | 예상 소요 시간 | 우선순위 |
|-------|-------|---------------|---------|
| Phase 1 | Task 1.1-1.3 (스크립트 작성) | 1-2일 | ⭐⭐⭐ |
| Phase 2 | Task 2.1 (마스터 샘플 시트) | 0.5일 | ⭐⭐⭐ |
| Phase 3 | Task 3.1-3.2 (기존 결과 재구성) | 1일 | ⭐⭐ |
| Phase 4 | Task 4.1 (새 프로젝트 테스트) | 1일 | ⭐⭐ |
| Phase 5 | Task 5.1-5.2 (문서화) | 0.5일 | ⭐ |

**총 예상 기간**: 4-5일

---

## ✅ 체크리스트

### Phase 1: 스크립트 개발
- [ ] `bin/convert_samplesheet.py` 작성
  - [ ] 기본 변환 기능
  - [ ] 검증 로직
  - [ ] 테스트 케이스
- [ ] `bin/reorganize_outputs.py` 작성
  - [ ] 디렉토리 구조 생성
  - [ ] 파일 복사 로직
  - [ ] 샘플별 재구성
  - [ ] 프로젝트 요약 생성
- [ ] `bin/generate_manifest.py` 작성
  - [ ] manifest.json 스키마
  - [ ] QC 메트릭 추출
  - [ ] 파일 메타데이터

### Phase 2: 마스터 데이터
- [ ] `samples_H2O2_astrocyte.csv` 생성
  - [ ] 15개 샘플 정보 입력
  - [ ] 메타데이터 추가 (cell_type, treatment 등)
  - [ ] 검증

### Phase 3: 기존 결과 재구성
- [ ] H2O2 Astrocyte 결과 재구성
  - [ ] `reorganize_outputs.py` 실행
  - [ ] 15개 샘플 디렉토리 확인
  - [ ] manifest.json 확인
  - [ ] MultiQC 복사 확인
- [ ] QC 메트릭 통합
  - [ ] FRiP score 추출
  - [ ] Peak count 추출
  - [ ] Alignment rate 추출

### Phase 4: 신규 워크플로우
- [ ] 테스트 프로젝트 실행
  - [ ] samples_test.csv 작성
  - [ ] samplesheet 변환 테스트
  - [ ] Nextflow 실행 (3개 샘플)
  - [ ] 재구성 테스트
  - [ ] 검증

### Phase 5: 문서화
- [ ] `README.md` 업데이트
- [ ] `docs/AGENT_GUIDE.md` 작성
- [ ] `docs/reference/ATAC_STANDARDIZATION.md` 완성

---

## 🎯 성공 기준

### 기술적 성공 기준
1. ✅ `convert_samplesheet.py`가 오류 없이 변환 수행
2. ✅ `reorganize_outputs.py`가 표준 구조 생성
3. ✅ 모든 샘플의 `manifest.json` 생성 완료
4. ✅ MultiQC 데이터가 manifest에 통합
5. ✅ 새 프로젝트 전체 워크플로우 성공

### 비즈니스 성공 기준
1. ✅ RNA-seq와 동일한 디렉토리 구조
2. ✅ 에이전트가 manifest.json만으로 QC 평가 가능
3. ✅ Final outputs와 intermediate 파일 명확히 분리
4. ✅ 3개 파이프라인(RNA-seq, ATAC-seq, WGS) 구조 통일

---

## 🚧 리스크 및 대응

| 리스크 | 영향도 | 대응 방안 |
|--------|--------|----------|
| MultiQC 데이터 형식 변경 | 중 | 버전별 파서 작성 |
| 대용량 파일 복사 시간 | 중 | 심볼릭 링크 옵션 추가 |
| 기존 분석 재실행 필요 | 낮 | 재구성 스크립트로 기존 결과 재활용 |
| FASTQ 파일 이동/삭제 | 높 | 절대 경로 사용, 백업 권장 |

---

## 📝 다음 단계 (Phase 1 시작)

### 즉시 시작 가능한 작업
1. **`bin/convert_samplesheet.py` 작성**
   - 파일 생성
   - 기본 변환 로직 구현
   - 테스트

2. **`samples_H2O2_astrocyte.csv` 작성**
   - 기존 samplesheet 기반으로 확장
   - 메타데이터 추가

### 필요한 의사결정
- [ ] 표준 base directory 위치 확정: `/home/ngs/data/results/`
- [ ] Project ID 네이밍 규칙: `{Treatment}_{Species}_{Year}` 형식 사용?
- [ ] 기존 결과 보존: 재구성 후 원본 유지 또는 삭제?

---

## 📚 참고 문서

- [ATAC_STANDARDIZATION.md](./ATAC_STANDARDIZATION.md) - 표준화 가이드
- RNA-seq 표준화: `~/ngs-pipeline/rna-seq-pipeline/docs/reference/STANDARDIZATION.md`
- nf-core/atacseq 문서: https://nf-co.re/atacseq/2.1.2
