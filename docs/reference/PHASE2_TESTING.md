# Phase 2 Testing Guide

## 🧪 테스트 준비

### 1. 서버에서 스크립트 권한 설정
```bash
cd /home/ygkim/ngs_pipeline/rna-seq-pipeline
chmod +x scripts/generate_qc_summary.py
chmod +x scripts/generate_manifest.py
```

---

## 📊 QC Summary 생성 테스트

### 테스트 1: 단일 샘플 QC summary 생성

```bash
cd /home/ygkim/ngs_pipeline/rna-seq-pipeline

# h_RNA_200_1 샘플 (PASS 예상)
python3 scripts/generate_qc_summary.py \
    --sample-id h_RNA_200_1 \
    --star-log /home/ngs/data/h-rna-seq-pipeline-results/aligned/h_RNA_200_1/Log.final.out \
    --featurecounts /home/ngs/data/h-rna-seq-pipeline-results/counts/counts_matrix.txt.summary \
    -o /tmp/qc_summary_h_RNA_200_1.json

# 결과 확인
cat /tmp/qc_summary_h_RNA_200_1.json | jq '.'
```

**예상 출력:**
```
Generating QC Summary
  Sample: h_RNA_200_1
  ...
Status: PASS
  Uniquely mapped: 93.57%
  Assignment rate: 78.34%

✅ No issues found
```

### 테스트 2: 문제 샘플 QC summary (FAIL 예상)

```bash
# h_RNA_D1_2 샘플 (FAIL 예상)
python3 scripts/generate_qc_summary.py \
    --sample-id h_RNA_D1_2 \
    --star-log /home/ngs/data/h-rna-seq-pipeline-results/aligned/h_RNA_D1_2/Log.final.out \
    --featurecounts /home/ngs/data/h-rna-seq-pipeline-results/counts/counts_matrix.txt.summary \
    -o /tmp/qc_summary_h_RNA_D1_2.json

# 결과 확인
cat /tmp/qc_summary_h_RNA_D1_2.json | jq '.overall_status, .issues'
```

**예상 출력:**
```
Status: FAIL
  Uniquely mapped: 36.18%
  Assignment rate: 6.74%

Issues found: 2
  CRITICAL: Low uniquely mapped rate: 36.2%
  CRITICAL: Low assignment rate: 6.7%
```

### 테스트 3: 모든 샘플 QC summary 생성

```bash
# 모든 샘플에 대해 QC summary 생성
for sample in h_RNA_Cont_1 h_RNA_Cont_2 h_RNA_100_1 h_RNA_200_1 h_RNA_D1_1 h_RNA_D3_1; do
    echo "Processing $sample..."
    python3 scripts/generate_qc_summary.py \
        --sample-id $sample \
        --star-log /home/ngs/data/h-rna-seq-pipeline-results/aligned/$sample/Log.final.out \
        --featurecounts /home/ngs/data/h-rna-seq-pipeline-results/counts/counts_matrix.txt.summary \
        -o /tmp/qc_summary_$sample.json
done

# 상태 요약
echo -e "\n=== QC Status Summary ==="
for json in /tmp/qc_summary_*.json; do
    sample=$(basename $json .json | sed 's/qc_summary_//')
    status=$(jq -r '.overall_status' $json)
    unique_map=$(jq -r '.alignment.uniquely_mapped_pct' $json)
    assign_rate=$(jq -r '.quantification.assignment_rate' $json)
    echo "$sample: $status (Unique: ${unique_map}%, Assign: ${assign_rate}%)"
done
```

---

## 📁 Manifest 생성 테스트 (모의 구조)

표준 디렉토리 구조를 만들고 manifest를 생성해봅니다.

### 테스트 4: 표준 구조 생성 및 Manifest

```bash
# 1. 표준 디렉토리 구조 생성 (h_RNA_200_1 샘플)
SAMPLE="h_RNA_200_1"
PROJECT="H2O2_human_2025"
SAMPLE_DIR="/tmp/test_standard_structure/${PROJECT}/${SAMPLE}/rna-seq"

mkdir -p ${SAMPLE_DIR}/final_outputs/{bam,counts,qc}
mkdir -p ${SAMPLE_DIR}/intermediate/{trimmed,fastqc,logs}
mkdir -p ${SAMPLE_DIR}/metadata

# 2. 기존 결과물을 final_outputs로 복사 (시뮬레이션)
# BAM
cp /home/ngs/data/h-rna-seq-pipeline-results/aligned/${SAMPLE}/Aligned.sortedByCoord.out.bam \
   ${SAMPLE_DIR}/final_outputs/bam/aligned.sorted.bam
cp /home/ngs/data/h-rna-seq-pipeline-results/aligned/${SAMPLE}/Aligned.sortedByCoord.out.bam.bai \
   ${SAMPLE_DIR}/final_outputs/bam/aligned.sorted.bam.bai 2>/dev/null || true

# Counts (샘플별로 추출 필요 - 여기서는 생략)
echo "gene_id,${SAMPLE}" > ${SAMPLE_DIR}/final_outputs/counts/gene_counts.csv
echo "ENSG00000000003,1000" >> ${SAMPLE_DIR}/final_outputs/counts/gene_counts.csv

# QC summary
cp /tmp/qc_summary_${SAMPLE}.json ${SAMPLE_DIR}/final_outputs/qc/qc_summary.json

# 3. Manifest 생성
python3 scripts/generate_manifest.py \
    --sample-dir ${SAMPLE_DIR} \
    --sample-id ${SAMPLE} \
    --project-id ${PROJECT} \
    --pipeline-type rna-seq

# 4. 결과 확인
cat ${SAMPLE_DIR}/final_outputs/manifest.json | jq '.'
```

**예상 출력:**
```
Generating Manifest
  Sample: h_RNA_200_1
  Project: H2O2_human_2025
  ...

✅ Manifest generated: .../final_outputs/manifest.json

Summary:
  Status: completed
  Final outputs: 3
  QC status: PASS
  Next steps: differential_expression, pathway_analysis, gene_set_enrichment
```

### 테스트 5: Manifest 검증

```bash
# Manifest 파일 검증 (MD5 체크섬)
python3 scripts/generate_manifest.py \
    --validate ${SAMPLE_DIR}/final_outputs/manifest.json
```

**예상 출력:**
```
Validating Manifest: .../manifest.json
======================================================================

✅ OK: aligned_bam
✅ OK: bam_index
✅ OK: gene_counts
✅ OK: qc_summary

======================================================================
✅ Manifest validation PASSED
======================================================================
```

---

## 🔍 표준 구조 검증

### 테스트 6: 디렉토리 구조 확인

```bash
# 생성된 표준 구조 확인
tree -L 4 /tmp/test_standard_structure/

# 예상 출력:
# /tmp/test_standard_structure/
# └── H2O2_human_2025/
#     └── h_RNA_200_1/
#         └── rna-seq/
#             ├── final_outputs/
#             │   ├── bam/
#             │   ├── counts/
#             │   ├── qc/
#             │   └── manifest.json
#             ├── intermediate/
#             └── metadata/
```

### 테스트 7: Manifest 내용 상세 확인

```bash
# Final outputs 목록
jq '.final_outputs | keys' ${SAMPLE_DIR}/final_outputs/manifest.json

# QC 메트릭
jq '.qc_metrics' ${SAMPLE_DIR}/final_outputs/manifest.json

# 다음 단계
jq '.next_steps' ${SAMPLE_DIR}/final_outputs/manifest.json

# 파일 크기 및 MD5
jq '.final_outputs.aligned_bam | {path, size_bytes, md5}' ${SAMPLE_DIR}/final_outputs/manifest.json
```

---

## 📈 전체 프로젝트 테스트

### 테스트 8: 여러 샘플에 대해 표준 구조 생성

```bash
# 좋은 샘플 3개 + 나쁜 샘플 1개로 테스트
SAMPLES=("h_RNA_200_1" "h_RNA_200_2" "h_RNA_D1_1" "h_RNA_D1_2")

for SAMPLE in "${SAMPLES[@]}"; do
    echo "=== Processing $SAMPLE ==="
    
    # 1. QC summary 생성
    python3 scripts/generate_qc_summary.py \
        --sample-id $SAMPLE \
        --star-log /home/ngs/data/h-rna-seq-pipeline-results/aligned/$SAMPLE/Log.final.out \
        --featurecounts /home/ngs/data/h-rna-seq-pipeline-results/counts/counts_matrix.txt.summary \
        -o /tmp/qc_summary_$SAMPLE.json
    
    # 2. 표준 구조 생성
    SAMPLE_DIR="/tmp/test_standard_structure/H2O2_human_2025/${SAMPLE}/rna-seq"
    mkdir -p ${SAMPLE_DIR}/final_outputs/{bam,counts,qc}
    
    # 파일 복사
    cp /home/ngs/data/h-rna-seq-pipeline-results/aligned/${SAMPLE}/Aligned.sortedByCoord.out.bam \
       ${SAMPLE_DIR}/final_outputs/bam/aligned.sorted.bam
    cp /tmp/qc_summary_$SAMPLE.json ${SAMPLE_DIR}/final_outputs/qc/qc_summary.json
    
    # 3. Manifest 생성
    python3 scripts/generate_manifest.py \
        --sample-dir ${SAMPLE_DIR} \
        --sample-id ${SAMPLE} \
        --project-id H2O2_human_2025
    
    echo ""
done
```

### 테스트 9: 프로젝트 전체 요약

```bash
# 모든 샘플의 QC 상태 수집
echo "=== Project QC Summary ==="
for SAMPLE in "${SAMPLES[@]}"; do
    MANIFEST="/tmp/test_standard_structure/H2O2_human_2025/${SAMPLE}/rna-seq/final_outputs/manifest.json"
    
    if [ -f "$MANIFEST" ]; then
        STATUS=$(jq -r '.qc_metrics.overall_status' $MANIFEST)
        UNIQUE=$(jq -r '.qc_metrics.alignment.uniquely_mapped_pct // 0' $MANIFEST)
        ASSIGN=$(jq -r '.qc_metrics.quantification.assignment_rate // 0' $MANIFEST)
        
        printf "%-15s: %-6s (Unique: %5.1f%%, Assign: %5.1f%%)\n" \
            "$SAMPLE" "$STATUS" "$UNIQUE" "$ASSIGN"
    fi
done
```

---

## ✅ 검증 체크리스트

Phase 2 구현 완료 확인:

- [ ] QC summary 생성 스크립트 작동
  - [ ] PASS 샘플 정상 판정
  - [ ] FAIL 샘플 정상 판정
  - [ ] WARN 샘플 정상 판정

- [ ] Manifest 생성 스크립트 작동
  - [ ] final_outputs 목록 생성
  - [ ] MD5 체크섬 계산
  - [ ] QC 메트릭 포함
  - [ ] 다음 단계 제안

- [ ] Manifest 검증 기능
  - [ ] 파일 존재 확인
  - [ ] MD5 체크섬 검증

- [ ] 표준 디렉토리 구조
  - [ ] final_outputs/ 생성
  - [ ] intermediate/ 생성
  - [ ] metadata/ 생성

---

## 🚀 다음 단계 (Phase 3)

테스트 완료 후:
1. 실제 파이프라인에 통합 (Snakefile 규칙 추가)
2. Migration 스크립트 작성 (기존 결과 → 표준 구조)
3. WGS, ATAC-seq 파이프라인 확장

---

## 💡 트러블슈팅

### jq가 없는 경우
```bash
sudo apt-get install jq
```

### Permission denied
```bash
chmod +x scripts/*.py
```

### MD5 계산 느림
대용량 BAM 파일의 경우 MD5 계산에 시간이 걸릴 수 있습니다.
테스트시 작은 파일로 먼저 확인하세요.
