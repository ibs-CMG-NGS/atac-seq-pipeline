# ATAC-seq Pipeline Standardization Guide

## 🎯 목적
RNA-seq 파이프라인과 동일한 표준을 적용하여 에이전트 기반 파이프라인 관리 체계 구축

---

## 1. 샘플 시트 표준화

### 1.1 마스터 샘플 시트 (`samples.csv`)

**모든 NGS 파이프라인에서 공통으로 사용하는 최상위 샘플 정의 파일**

#### 필수 컬럼:
- `project_id`: 프로젝트 식별자
- `sample_id`: 고유한 샘플 ID (파일명 기반이 아닌 의미있는 ID)
- `sample_name`: 샘플 이름 (분석 결과 표시용)
- `condition`: 실험 조건/그룹 (Control, Treatment 등)
- `replicate`: 생물학적 반복 번호 (1, 2, 3, ...)
- `sequencing_platform`: 시퀀싱 플랫폼 (Illumina, PacBio 등)
- `library_type`: 라이브러리 타입 (ATAC-seq, RNA-seq, WGS)
- `read_type`: single-end 또는 paired-end
- `fastq_1`: Read 1 FASTQ 파일 경로 (절대경로)
- `fastq_2`: Read 2 FASTQ 파일 경로 (paired-end인 경우)
- `species`: 생물종 (human, mouse, rat 등)
- `genome_build`: 참조 유전체 버전 (GRCh38, GRCm39 등)

#### ATAC-seq 특화 선택 컬럼:
- `batch`: 배치 효과 보정용
- `cell_type`: 세포 타입
- `tissue`: 조직 타입
- `treatment`: 처리 조건 (H2O2, Drug 등)
- `treatment_dose`: 처리 농도 (100uM, 200uM 등)
- `time_point`: 시간대 (D1, D3 등)
- `cell_count`: 세포 수 (ATAC-seq QC에 중요)
- `fragmentation_method`: 단편화 방법 (Tn5, sonication 등)
- `notes`: 추가 메모

---

### 1.2 예시: H2O2 Astrocyte ATAC-seq 프로젝트

#### `samples.csv` (마스터 샘플 시트)
```csv
project_id,sample_id,sample_name,condition,replicate,sequencing_platform,library_type,read_type,fastq_1,fastq_2,species,genome_build,cell_type,treatment,treatment_dose,time_point,notes
H2O2_Astrocyte_2025,CONTROL_REP1,Control_Rep1,Control,1,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/Cont_1_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/Cont_1_2.fastq.gz,mouse,GRCm39,astrocyte,none,0,baseline,Control replicate 1
H2O2_Astrocyte_2025,CONTROL_REP2,Control_Rep2,Control,2,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/Cont_2_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/Cont_2_2.fastq.gz,mouse,GRCm39,astrocyte,none,0,baseline,Control replicate 2
H2O2_Astrocyte_2025,CONTROL_REP3,Control_Rep3,Control,3,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/Cont_3_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/Cont_3_2.fastq.gz,mouse,GRCm39,astrocyte,none,0,baseline,Control replicate 3
H2O2_Astrocyte_2025,H2O2_100uM_REP1,100uM_Rep1,H2O2_100uM,1,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/100_1_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/100_1_2.fastq.gz,mouse,GRCm39,astrocyte,H2O2,100uM,24h,100uM H2O2 treatment
H2O2_Astrocyte_2025,H2O2_100uM_REP2,100uM_Rep2,H2O2_100uM,2,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/100_2_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/100_2_2.fastq.gz,mouse,GRCm39,astrocyte,H2O2,100uM,24h,100uM H2O2 treatment
H2O2_Astrocyte_2025,H2O2_100uM_REP3,100uM_Rep3,H2O2_100uM,3,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/100_3_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/100_3_2.fastq.gz,mouse,GRCm39,astrocyte,H2O2,100uM,24h,100uM H2O2 treatment
H2O2_Astrocyte_2025,H2O2_200uM_REP1,200uM_Rep1,H2O2_200uM,1,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/200_1_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/200_1_2.fastq.gz,mouse,GRCm39,astrocyte,H2O2,200uM,24h,200uM H2O2 treatment
H2O2_Astrocyte_2025,H2O2_200uM_REP2,200uM_Rep2,H2O2_200uM,2,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/200_2_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/200_2_2.fastq.gz,mouse,GRCm39,astrocyte,H2O2,200uM,24h,200uM H2O2 treatment
H2O2_Astrocyte_2025,H2O2_200uM_REP3,200uM_Rep3,H2O2_200uM,3,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/200_3_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/200_3_2.fastq.gz,mouse,GRCm39,astrocyte,H2O2,200uM,24h,200uM H2O2 treatment
H2O2_Astrocyte_2025,D1_REP1,D1_Rep1,D1,1,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/D1_1_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/D1_1_2.fastq.gz,mouse,GRCm39,astrocyte,time_course,0,D1,Day 1 time point
H2O2_Astrocyte_2025,D1_REP2,D1_Rep2,D1,2,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/D1_2_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/D1_2_2.fastq.gz,mouse,GRCm39,astrocyte,time_course,0,D1,Day 1 time point
H2O2_Astrocyte_2025,D1_REP3,D1_Rep3,D1,3,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/D1_3_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/D1_3_2.fastq.gz,mouse,GRCm39,astrocyte,time_course,0,D1,Day 1 time point
H2O2_Astrocyte_2025,D3_REP1,D3_Rep1,D3,1,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/D3_1_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/D3_1_2.fastq.gz,mouse,GRCm39,astrocyte,time_course,0,D3,Day 3 time point
H2O2_Astrocyte_2025,D3_REP2,D3_Rep2,D3,2,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/D3_2_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/D3_2_2.fastq.gz,mouse,GRCm39,astrocyte,time_course,0,D3,Day 3 time point
H2O2_Astrocyte_2025,D3_REP3,D3_Rep3,D3,3,Illumina,ATAC-seq,paired-end,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/D3_3_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/D3_3_2.fastq.gz,mouse,GRCm39,astrocyte,time_course,0,D3,Day 3 time point
```

---

### 1.3 Nextflow 파이프라인용 변환

에이전트는 `samples.csv`를 읽어서 nf-core/atacseq 형식의 `samplesheet.csv`로 변환:

#### 현재 Nextflow 형식 (`samplesheet.csv`)
```csv
sample,fastq_1,fastq_2,replicate
CONTROL,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/Cont_1_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/Cont_1_2.fastq.gz,1
CONTROL,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/Cont_2_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/Cont_2_2.fastq.gz,2
D1,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/D1_1_1.fastq.gz,/home/ngs/data/ygkim/2025/H2O2_astrocyte_atac/raw/D1_1_2.fastq.gz,1
```

#### 변환 로직 (Python)
```python
import pandas as pd

def convert_master_to_nextflow(master_csv, output_csv):
    """
    마스터 samples.csv를 Nextflow samplesheet.csv로 변환
    """
    df = pd.read_csv(master_csv)
    
    # ATAC-seq만 필터링
    df_atac = df[df['library_type'] == 'ATAC-seq'].copy()
    
    # Nextflow 형식으로 변환
    nf_df = pd.DataFrame({
        'sample': df_atac['condition'],  # condition을 sample로 그룹핑
        'fastq_1': df_atac['fastq_1'],
        'fastq_2': df_atac['fastq_2'],
        'replicate': df_atac['replicate']
    })
    
    nf_df.to_csv(output_csv, index=False)
    print(f"✅ Converted {len(nf_df)} samples to Nextflow format: {output_csv}")

# 사용 예시
convert_master_to_nextflow('samples.csv', 'samplesheet.csv')
```

---

## 2. 출력 디렉토리 표준화

### 2.1 표준 디렉토리 구조

```
/home/ngs/data/results/
└── {PROJECT_ID}/                           # 예: H2O2_Astrocyte_2025
    │
    ├── metadata/                           # 프로젝트 메타데이터
    │   ├── samples_master.csv              # 마스터 샘플 시트
    │   ├── samplesheet_nextflow.csv        # Nextflow용 변환 시트
    │   ├── analysis_log.json               # 분석 이력
    │   └── pipeline_config.yaml            # 파이프라인 설정 백업
    │
    ├── {SAMPLE_ID}/                        # 예: CONTROL_REP1, H2O2_100uM_REP1
    │   └── atac-seq/                       # 파이프라인 타입
    │       │
    │       ├── final_outputs/              # ⭐ 최종 결과물 (에이전트가 읽을 파일)
    │       │   ├── bam/
    │       │   │   ├── aligned.sorted.bam
    │       │   │   └── aligned.sorted.bam.bai
    │       │   ├── peaks/
    │       │   │   ├── narrow_peaks.bed        # Narrow peak calling 결과
    │       │   │   ├── broad_peaks.bed         # Broad peak calling 결과
    │       │   │   ├── peak_summits.bed        # Peak summits
    │       │   │   └── consensus_peaks.bed     # Consensus peaks (replicate 통합)
    │       │   ├── bigwig/
    │       │   │   ├── coverage.bigWig         # Genome browser용
    │       │   │   └── normalized.bigWig       # 정규화된 coverage
    │       │   ├── qc/
    │       │   │   ├── qc_summary.json         # 구조화된 QC 메트릭
    │       │   │   ├── ataqv_report.html       # ATAQV QC 리포트
    │       │   │   ├── frip_score.txt          # FRiP score
    │       │   │   └── fragment_size_dist.pdf  # Fragment size distribution
    │       │   └── manifest.json               # 최종 결과물 목록 및 메타데이터
    │       │
    │       ├── intermediate/                   # 중간 파일 (분석 중 생성)
    │       │   ├── trimmed/
    │       │   │   ├── sample_1.fastq.gz
    │       │   │   └── sample_2.fastq.gz
    │       │   ├── aligned/
    │       │   │   ├── raw.bam
    │       │   │   └── filtered.bam
    │       │   ├── fastqc/
    │       │   │   ├── raw_1_fastqc.html
    │       │   │   ├── raw_2_fastqc.html
    │       │   │   ├── trimmed_1_fastqc.html
    │       │   │   └── trimmed_2_fastqc.html
    │       │   └── logs/
    │       │       ├── trim_galore.log
    │       │       ├── bwa_align.log
    │       │       ├── macs2_callpeak.log
    │       │       └── picard_markdup.log
    │       │
    │       └── metadata/
    │           ├── sample_info.yaml             # 샘플 메타데이터
    │           ├── peak_annotation.txt          # Peak annotation
    │           └── library_complexity.txt       # Library complexity metrics
    │
    ├── project_summary/                        # 프로젝트 전체 요약
    │   ├── peaks/
    │   │   ├── consensus_peaks_all.bed         # 모든 샘플의 consensus peaks
    │   │   ├── differential_peaks.bed          # Differential accessibility
    │   │   └── peak_overlap_matrix.txt         # Replicate 간 peak overlap
    │   ├── qc/
    │   │   ├── multiqc_report.html             # MultiQC 통합 리포트
    │   │   └── qc_summary_all.csv              # 모든 샘플 QC 요약
    │   ├── differential_accessibility/
    │   │   ├── deseq2_results.csv              # DESeq2 결과
    │   │   ├── ma_plot.pdf                     # MA plot
    │   │   └── pca_plot.pdf                    # PCA plot
    │   ├── motif_analysis/
    │   │   ├── homer_results/                  # HOMER motif enrichment
    │   │   └── meme_results/                   # MEME motif enrichment
    │   └── igv_session/
    │       └── project.igv.xml                 # IGV session file
    │
    └── logs/
        ├── nextflow.log                        # Nextflow 실행 로그
        ├── execution_report.html               # Nextflow execution report
        └── timeline.html                       # Nextflow timeline
```

---

### 2.2 현재 nf-core/atacseq 출력 vs 표준 구조 매핑

#### 현재 구조 (nf-core/atacseq v2.1.2)
```
results/
├── genome/                     # Reference genome files
├── fastqc/                     # FastQC reports (모든 샘플 혼재)
├── trimgalore/                 # Trim Galore results
├── bwa/                        # BWA alignment
│   └── mergedLibrary/          # Merged replicate BAMs
│       ├── macs2/              # Peak calling
│       │   ├── broadPeak/
│       │   └── narrowPeak/
│       ├── bigwig/
│       └── picard_metrics/
├── multiqc/
│   ├── broadPeak/
│   │   └── multiqc_report.html
│   └── narrowPeak/
└── pipeline_info/
```

#### 표준 구조로의 변환 매핑

| 현재 경로 | 표준 경로 | 파일 타입 |
|----------|----------|----------|
| `bwa/mergedLibrary/{sample}.mLb.clN.sorted.bam` | `{sample}/atac-seq/final_outputs/bam/aligned.sorted.bam` | **Final** |
| `bwa/mergedLibrary/macs2/broadPeak/{sample}_peaks.broadPeak` | `{sample}/atac-seq/final_outputs/peaks/broad_peaks.bed` | **Final** |
| `bwa/mergedLibrary/bigwig/{sample}.bigWig` | `{sample}/atac-seq/final_outputs/bigwig/coverage.bigWig` | **Final** |
| `trimgalore/{sample}_1_val_1.fq.gz` | `{sample}/atac-seq/intermediate/trimmed/sample_1.fastq.gz` | Intermediate |
| `fastqc/{sample}_1_fastqc.html` | `{sample}/atac-seq/intermediate/fastqc/raw_1_fastqc.html` | Intermediate |
| `multiqc/broadPeak/multiqc_report.html` | `project_summary/qc/multiqc_report.html` | **Final** |
| `bwa/mergedLibrary/macs2/broadPeak/consensus/` | `project_summary/peaks/consensus_peaks_all.bed` | **Final** |

---

### 2.3 manifest.json 구조 (샘플별)

각 샘플의 `final_outputs/manifest.json`은 최종 결과물을 에이전트가 쉽게 파악할 수 있도록 메타데이터 제공:

```json
{
  "sample_id": "CONTROL_REP1",
  "project_id": "H2O2_Astrocyte_2025",
  "pipeline": "atac-seq",
  "pipeline_version": "nf-core/atacseq v2.1.2",
  "completion_date": "2026-02-03T17:38:00",
  "genome_build": "GRCm39",
  "aligner": "bwa",
  "peak_caller": "macs2",
  
  "final_outputs": {
    "bam": {
      "aligned_bam": "bam/aligned.sorted.bam",
      "bam_index": "bam/aligned.sorted.bam.bai",
      "file_size_mb": 4521,
      "read_count": 512822,
      "alignment_rate": 1.0
    },
    "peaks": {
      "broad_peaks": "peaks/broad_peaks.bed",
      "peak_count": 3767,
      "frip_score": 0.7796
    },
    "bigwig": {
      "coverage": "bigwig/coverage.bigWig",
      "normalized": "bigwig/normalized.bigWig"
    },
    "qc": {
      "summary": "qc/qc_summary.json",
      "ataqv_report": "qc/ataqv_report.html",
      "frip_score_file": "qc/frip_score.txt"
    }
  },
  
  "qc_metrics": {
    "total_reads": 60086478,
    "trimmed_reads": 58234521,
    "aligned_reads": 512822,
    "unique_reads": 504804,
    "duplicate_rate": 0.015,
    "mitochondrial_rate": 0.032,
    "frip_score": 0.7796,
    "peak_count": 3767,
    "nsc": 1.25,
    "rsc": 0.98
  },
  
  "analysis_status": "complete",
  "warnings": [],
  "errors": []
}
```

---

## 3. 구현 단계

### Phase 1: 샘플 시트 변환 스크립트 작성 ✅

**파일**: `bin/convert_samplesheet.py`

```python
#!/usr/bin/env python3
"""
Convert master samples.csv to pipeline-specific format
"""

import pandas as pd
import argparse
import sys
from pathlib import Path

def validate_master_sheet(df):
    """마스터 샘플 시트 검증"""
    required_cols = [
        'project_id', 'sample_id', 'condition', 'replicate',
        'library_type', 'read_type', 'fastq_1', 'species', 'genome_build'
    ]
    
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # FASTQ 파일 존재 확인
    for idx, row in df.iterrows():
        if not Path(row['fastq_1']).exists():
            print(f"⚠️  Warning: {row['fastq_1']} not found (sample: {row['sample_id']})")
        
        if row['read_type'] == 'paired-end' and 'fastq_2' in row:
            if pd.notna(row['fastq_2']) and not Path(row['fastq_2']).exists():
                print(f"⚠️  Warning: {row['fastq_2']} not found (sample: {row['sample_id']})")

def convert_to_nextflow_atac(df, output_file):
    """
    Convert master samples.csv to nf-core/atacseq samplesheet.csv
    
    Format:
    sample,fastq_1,fastq_2,replicate
    """
    # Filter ATAC-seq samples only
    df_atac = df[df['library_type'] == 'ATAC-seq'].copy()
    
    if len(df_atac) == 0:
        raise ValueError("No ATAC-seq samples found in master sheet")
    
    # Create Nextflow format
    nf_df = pd.DataFrame({
        'sample': df_atac['condition'],      # Group by condition
        'fastq_1': df_atac['fastq_1'],
        'fastq_2': df_atac['fastq_2'] if 'fastq_2' in df_atac.columns else '',
        'replicate': df_atac['replicate']
    })
    
    nf_df.to_csv(output_file, index=False)
    print(f"✅ Converted {len(nf_df)} samples to Nextflow format: {output_file}")
    
    # Print summary
    print(f"\n📊 Sample Summary:")
    print(f"   Total samples: {len(nf_df)}")
    print(f"   Conditions: {nf_df['sample'].nunique()}")
    print(f"   Condition breakdown:")
    for cond, count in nf_df['sample'].value_counts().items():
        print(f"      - {cond}: {count} replicates")

def main():
    parser = argparse.ArgumentParser(
        description='Convert master samples.csv to pipeline-specific format'
    )
    parser.add_argument(
        'master_csv',
        help='Path to master samples.csv'
    )
    parser.add_argument(
        '-o', '--output',
        default='samplesheet.csv',
        help='Output samplesheet file (default: samplesheet.csv)'
    )
    parser.add_argument(
        '-p', '--pipeline',
        default='nextflow-atac',
        choices=['nextflow-atac', 'snakemake-rna', 'wdl-wgs'],
        help='Target pipeline format (default: nextflow-atac)'
    )
    
    args = parser.parse_args()
    
    # Read master sheet
    try:
        df = pd.read_csv(args.master_csv)
        print(f"📖 Read {len(df)} samples from {args.master_csv}")
    except Exception as e:
        print(f"❌ Error reading master sheet: {e}")
        sys.exit(1)
    
    # Validate
    try:
        validate_master_sheet(df)
        print("✅ Master sheet validation passed")
    except ValueError as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)
    
    # Convert
    if args.pipeline == 'nextflow-atac':
        convert_to_nextflow_atac(df, args.output)
    else:
        print(f"❌ Pipeline format '{args.pipeline}' not yet implemented")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

**사용법**:
```bash
# 마스터 샘플 시트를 Nextflow 형식으로 변환
python bin/convert_samplesheet.py samples.csv -o samplesheet.csv -p nextflow-atac
```

---

### Phase 2: 출력 디렉토리 재구성 스크립트 ✅

**파일**: `bin/reorganize_outputs.py`

```python
#!/usr/bin/env python3
"""
Reorganize nf-core/atacseq outputs to standardized structure
"""

import shutil
import json
from pathlib import Path
import pandas as pd
import argparse

def create_standard_structure(base_dir, project_id):
    """표준 디렉토리 구조 생성"""
    base = Path(base_dir) / project_id
    
    dirs = [
        base / 'metadata',
        base / 'project_summary' / 'peaks',
        base / 'project_summary' / 'qc',
        base / 'project_summary' / 'differential_accessibility',
        base / 'logs'
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    return base

def reorganize_sample_outputs(nf_results, standard_base, sample_id, condition, replicate):
    """
    단일 샘플의 nf-core 출력을 표준 구조로 재구성
    
    Parameters:
        nf_results: nf-core/atacseq results 디렉토리
        standard_base: 표준 구조 베이스 디렉토리
        sample_id: 샘플 ID (예: CONTROL_REP1)
        condition: 조건 (예: CONTROL)
        replicate: 반복 번호
    """
    nf_res = Path(nf_results)
    sample_dir = standard_base / sample_id / 'atac-seq'
    
    # Create directories
    final_out = sample_dir / 'final_outputs'
    intermediate = sample_dir / 'intermediate'
    metadata = sample_dir / 'metadata'
    
    for d in [final_out / 'bam', final_out / 'peaks', final_out / 'bigwig', 
              final_out / 'qc', intermediate / 'trimmed', intermediate / 'fastqc',
              intermediate / 'logs', metadata]:
        d.mkdir(parents=True, exist_ok=True)
    
    # Map nf-core outputs to standard structure
    sample_pattern = f"{condition}_REP{replicate}"
    
    # BAM files (final_outputs)
    bam_src = nf_res / 'bwa' / 'mergedLibrary' / f'{sample_pattern}.mLb.clN.sorted.bam'
    if bam_src.exists():
        shutil.copy2(bam_src, final_out / 'bam' / 'aligned.sorted.bam')
        shutil.copy2(f"{bam_src}.bai", final_out / 'bam' / 'aligned.sorted.bam.bai')
        print(f"  ✅ Copied BAM: {sample_id}")
    
    # Peaks (final_outputs)
    peak_src = nf_res / 'bwa' / 'mergedLibrary' / 'macs2' / 'broadPeak' / f'{sample_pattern}_peaks.broadPeak'
    if peak_src.exists():
        shutil.copy2(peak_src, final_out / 'peaks' / 'broad_peaks.bed')
        print(f"  ✅ Copied peaks: {sample_id}")
    
    # BigWig (final_outputs)
    bw_src = nf_res / 'bwa' / 'mergedLibrary' / 'bigwig' / f'{sample_pattern}.bigWig'
    if bw_src.exists():
        shutil.copy2(bw_src, final_out / 'bigwig' / 'coverage.bigWig')
        print(f"  ✅ Copied BigWig: {sample_id}")
    
    # Trimmed FASTQ (intermediate)
    trim_dir = nf_res / 'trimgalore'
    if trim_dir.exists():
        for fq in trim_dir.glob(f'{sample_pattern}*.fq.gz'):
            shutil.copy2(fq, intermediate / 'trimmed' / fq.name)
    
    # FastQC (intermediate)
    fastqc_dir = nf_res / 'fastqc'
    if fastqc_dir.exists():
        for html in fastqc_dir.glob(f'{sample_pattern}*_fastqc.html'):
            shutil.copy2(html, intermediate / 'fastqc' / html.name)
    
    return sample_dir

def generate_manifest(sample_dir, sample_id, project_id):
    """샘플별 manifest.json 생성"""
    final_out = sample_dir / 'final_outputs'
    
    manifest = {
        'sample_id': sample_id,
        'project_id': project_id,
        'pipeline': 'atac-seq',
        'final_outputs': {},
        'analysis_status': 'complete'
    }
    
    # BAM
    bam_file = final_out / 'bam' / 'aligned.sorted.bam'
    if bam_file.exists():
        manifest['final_outputs']['bam'] = {
            'aligned_bam': str(bam_file.relative_to(final_out)),
            'file_size_mb': round(bam_file.stat().st_size / 1024 / 1024, 2)
        }
    
    # Peaks
    peak_file = final_out / 'peaks' / 'broad_peaks.bed'
    if peak_file.exists():
        manifest['final_outputs']['peaks'] = {
            'broad_peaks': str(peak_file.relative_to(final_out))
        }
    
    # Save manifest
    manifest_file = final_out / 'manifest.json'
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"  ✅ Generated manifest: {sample_id}")

def main():
    parser = argparse.ArgumentParser(
        description='Reorganize nf-core/atacseq outputs to standardized structure'
    )
    parser.add_argument('nf_results', help='Path to nf-core/atacseq results directory')
    parser.add_argument('output_base', help='Base directory for standardized outputs')
    parser.add_argument('samples_csv', help='Master samples.csv file')
    parser.add_argument('--project-id', required=True, help='Project ID')
    
    args = parser.parse_args()
    
    # Read samples
    df = pd.read_csv(args.samples_csv)
    df_atac = df[df['library_type'] == 'ATAC-seq']
    
    # Create standard structure
    print(f"📁 Creating standard structure in: {args.output_base}/{args.project_id}")
    standard_base = create_standard_structure(args.output_base, args.project_id)
    
    # Reorganize each sample
    print(f"\n📦 Reorganizing {len(df_atac)} samples...")
    for idx, row in df_atac.iterrows():
        sample_dir = reorganize_sample_outputs(
            args.nf_results,
            standard_base,
            row['sample_id'],
            row['condition'],
            row['replicate']
        )
        generate_manifest(sample_dir, row['sample_id'], args.project_id)
    
    # Copy project-level outputs
    print(f"\n📊 Copying project-level outputs...")
    mqc_src = Path(args.nf_results) / 'multiqc' / 'broadPeak' / 'multiqc_report.html'
    if mqc_src.exists():
        shutil.copy2(mqc_src, standard_base / 'project_summary' / 'qc' / 'multiqc_report.html')
        print("  ✅ Copied MultiQC report")
    
    print(f"\n✅ Reorganization complete!")
    print(f"📂 Standardized outputs: {standard_base}")

if __name__ == '__main__':
    main()
```

**사용법**:
```bash
# nf-core 출력을 표준 구조로 재구성
python bin/reorganize_outputs.py \
    ./results \
    /home/ngs/data/results \
    samples.csv \
    --project-id H2O2_Astrocyte_2025
```

---

### Phase 3: Nextflow 설정 수정 (향후 통합용)

`nextflow.config`에 표준 경로 옵션 추가:

```groovy
params {
    // Standard output structure
    use_standard_structure = false  // Set to true to enable standardized outputs
    standard_base_dir = '/home/ngs/data/results'
    project_id = null  // Must be set when use_standard_structure = true
    
    // Legacy output (default)
    outdir = './results'
}

// Conditional output directory
def output_base = params.use_standard_structure ? 
    "${params.standard_base_dir}/${params.project_id}" : 
    params.outdir
```

---

## 4. 에이전트 통합 워크플로우

### 4.1 표준 분석 파이프라인 (에이전트가 수행)

```
1. 사용자: "H2O2 astrocyte ATAC-seq 분석해줘"
   
2. 에이전트:
   ├── samples.csv 확인/생성
   ├── 프로젝트 디렉토리 생성 (/home/ngs/data/results/H2O2_Astrocyte_2025)
   ├── samplesheet.csv 변환 (convert_samplesheet.py)
   ├── Nextflow 실행
   ├── 표준 구조로 재구성 (reorganize_outputs.py)
   └── manifest.json 기반 QC 리포트 생성

3. 결과:
   └── /home/ngs/data/results/H2O2_Astrocyte_2025/
       ├── CONTROL_REP1/atac-seq/final_outputs/
       ├── CONTROL_REP2/atac-seq/final_outputs/
       └── project_summary/qc/multiqc_report.html
```

### 4.2 에이전트가 읽을 파일 우선순위

1. **QC 평가**: `{sample}/atac-seq/final_outputs/manifest.json`
2. **Peak 분석**: `{sample}/atac-seq/final_outputs/peaks/broad_peaks.bed`
3. **시각화**: `project_summary/qc/multiqc_report.html`
4. **3차 분석 입력**: `{sample}/atac-seq/final_outputs/bam/aligned.sorted.bam`

---

## 5. 체크리스트

### ✅ Phase 1: 샘플 시트 표준화
- [x] `samples.csv` 스키마 정의
- [x] `convert_samplesheet.py` 스크립트 작성
- [x] 검증 로직 추가

### ✅ Phase 2: 출력 구조 표준화
- [x] 표준 디렉토리 구조 설계
- [x] `reorganize_outputs.py` 스크립트 작성
- [x] `manifest.json` 스키마 정의

### 🔲 Phase 3: 파이프라인 통합
- [ ] Nextflow 설정 수정 (use_standard_structure 옵션)
- [ ] 실제 데이터로 테스트
- [ ] WGS 파이프라인에도 동일 표준 적용

### 🔲 Phase 4: 에이전트 통합
- [ ] 에이전트가 manifest.json 파싱
- [ ] 자동 QC 리포트 생성
- [ ] 3차 분석 워크플로우 연결

---

## 6. 다른 파이프라인과의 일관성

| 항목 | RNA-seq | ATAC-seq | WGS |
|------|---------|----------|-----|
| 샘플 시트 | `samples.csv` | `samples.csv` | `samples.csv` |
| 디렉토리 구조 | `{project}/{sample}/rna-seq/` | `{project}/{sample}/atac-seq/` | `{project}/{sample}/wgs/` |
| Final outputs | `final_outputs/` | `final_outputs/` | `final_outputs/` |
| Intermediate | `intermediate/` | `intermediate/` | `intermediate/` |
| Manifest | `manifest.json` | `manifest.json` | `manifest.json` |
| Project summary | `project_summary/` | `project_summary/` | `project_summary/` |

---

## 참고 자료

- [nf-core/atacseq 출력 구조](https://nf-co.re/atacseq/2.1.2/output)
- [ENCODE ATAC-seq 표준](https://www.encodeproject.org/atac-seq/)
- RNA-seq 표준화 문서: `docs/reference/STANDARDIZATION.md`
