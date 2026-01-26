# ATAC-seq Automatic QC Summary

This pipeline automatically analyzes FastQC results for ATAC-seq specific quality metrics and generates a comprehensive summary report.

## Features

- **ATAC-seq Specific Criteria**: Understands normal ATAC-seq characteristics (Tn5 bias, high duplication)
- **Automatic Flagging**: Identifies samples that require manual review
- **Visual Reports**: Generates HTML summary with color-coded results
- **Review List**: Creates a text file listing only samples needing attention

## What Gets Checked

### ✅ Critical Quality Metrics

1. **Per Base Sequence Quality**
   - Threshold: Mean quality > Q28 for 80% of bases
   - Flags: Samples with consistently low quality

2. **Adapter Content**
   - Threshold: < 10% adapter contamination
   - Flags: High adapter content (trimming failure)

3. **Read Length**
   - Threshold: Minimum 50bp after trimming
   - Flags: Very short reads that may affect alignment

4. **GC Content**
   - Expected range: 30-65%
   - Flags: Unusual GC content (possible contamination)

5. **Read Count**
   - Warning threshold: < 1M reads
   - Recommended: > 5M reads for ATAC-seq

### ⚠️ ATAC-seq Normal Characteristics (Not Flagged)

The following are **EXPECTED** in ATAC-seq and will NOT be flagged as issues:

- **Per Base Sequence Content** - Tn5 transposase bias at read starts
- **Sequence Duplication Levels** - High duplication (50-70%) is normal
- **Kmer Content** - Tn5 sequence preference patterns

## Output Files

### 1. `qc_summary.json`
Structured JSON with all QC results:
```json
{
  "total_samples": 24,
  "passed": 22,
  "failed": 2,
  "requires_review": [...]
}
```

### 2. `qc_summary.html`
Interactive HTML report with:
- Summary statistics dashboard
- Color-coded sample table
- Detailed issue descriptions
- Sortable and filterable view

### 3. `samples_need_review.txt`
Simple text list of samples requiring attention:
```
# Samples requiring manual QC review

SAMPLE1_REP1_T1
  - ISSUE: Low quality bases: 45/150 positions below Q28
  - WARNING: Low read count: 850,000 reads

SAMPLE2_REP2_T1
  - ISSUE: High adapter content: 12.5%
```

## Usage

### Standalone Usage

```bash
# Analyze all FastQC results in a directory
atac_qc_checker.py /path/to/fastqc_results qc_summary.json

# Generate HTML report
generate_qc_html.py qc_summary.json qc_summary.html
```

### Integrated in Pipeline

The QC summary is automatically generated after FastQC/TrimGalore steps:

```bash
nextflow run . -profile singularity -params-file params.yaml
```

Results will be in:
```
results/
  qc_summary/
    qc_summary.json
    qc_summary.html
    samples_need_review.txt  # Only if issues found
```

## Interpretation Guide

### ✅ PASS Status
- All quality metrics within acceptable ranges
- No manual review required
- Safe to proceed with downstream analysis

### ❌ FAIL Status
- One or more critical quality issues detected
- **Action Required**: Review the specific issues listed
- Consider:
  - Re-sequencing low-quality samples
  - Re-trimming if adapter contamination
  - Excluding from downstream analysis if quality too poor

### ⚠️ Warnings
- Minor issues that don't fail QC
- May still be usable for analysis
- Review to ensure acceptable for your specific needs

## Example Workflow

1. **Run pipeline** - Generates FastQC reports
2. **Auto QC** - System analyzes all samples
3. **Check summary** - Open `qc_summary.html` in browser
4. **Review flagged samples** - Only check samples in `samples_need_review.txt`
5. **Make decisions** - Keep, re-trim, or exclude problematic samples

## Customization

To adjust QC thresholds, edit `bin/atac_qc_checker.py`:

```python
THRESHOLDS = {
    'min_mean_quality': 28,           # Minimum base quality
    'max_adapter_content': 10,        # Maximum adapter %
    'max_duplication_pct': 85,        # Maximum duplication %
    'min_sequence_length': 50,        # Minimum read length
    'min_gc_content': 30,             # Minimum GC %
    'max_gc_content': 65,             # Maximum GC %
}
```

## Troubleshooting

**Q: All samples show "Per base sequence content" FAIL**  
A: This is normal for ATAC-seq! The tool automatically ignores this for ATAC-seq data.

**Q: High duplication is flagged**  
A: Only duplication >85% is flagged. 50-70% is normal and not flagged.

**Q: Can I run this on existing FastQC results?**  
A: Yes! Use the standalone mode:
```bash
atac_qc_checker.py /path/to/old/fastqc qc_summary.json
```

## Citation

If you use this QC tool, please cite the nf-core/atacseq pipeline:

> Ewels PA, Peltzer A, Fillinger S, Patel H, Alneberg J, Wilm A, Garcia MU, Di Tommaso P, Nahnsen S. The nf-core framework for community-curated bioinformatics pipelines. Nat Biotechnol. 2020 Mar;38(3):276-278. doi: 10.1038/s41587-020-0439-x. PubMed PMID: 32055031.
