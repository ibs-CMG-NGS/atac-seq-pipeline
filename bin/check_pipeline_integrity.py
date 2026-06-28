#!/usr/bin/env python3
"""
ATAC-seq Pipeline Integrity Checker
====================================
파이프라인 완료 후 샘플 ID 불일치 및 누락 결과를 진단합니다.

주요 검사 항목:
  1. BAM 파일명과 expected 샘플명 불일치 감지
  2. FRIP_SCORE / ATAQv 누락 샘플 식별
  3. Nextflow work dir에서 실제 task input/output 교차 검증

사용법:
  python3 check_pipeline_integrity.py <results_dir> [nextflow_work_dir]

예시:
  python3 check_pipeline_integrity.py \\
      /home/ngs/data/ygkim/2026/2026-ben-mouse-atac/results \\
      /home/ngs/data/nextflow_work/atac-seq-pipeline
"""

import os
import sys
import glob
import re
import json
from pathlib import Path
from collections import defaultdict

# ──────────────────────────────────────────────
# ANSI colors
# ──────────────────────────────────────────────
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}✓{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}⚠{RESET}  {msg}")
def fail(msg): print(f"  {RED}✗{RESET} {msg}")
def info(msg): print(f"  {CYAN}ℹ{RESET}  {msg}")

# ──────────────────────────────────────────────
# 1. 결과 디렉토리에서 샘플 목록 수집
# ──────────────────────────────────────────────
def get_expected_samples(results_dir):
    bam_dir = os.path.join(results_dir, 'bwa', 'merged_library')
    samples = set()
    for bam in glob.glob(os.path.join(bam_dir, '*.mLb.mkD.sorted.bam')):
        sample = os.path.basename(bam).replace('.mLb.mkD.sorted.bam', '')
        samples.add(sample)
    return sorted(samples)

# ──────────────────────────────────────────────
# 2. 결과 파일 존재 여부 검사
# ──────────────────────────────────────────────
def check_output_files(results_dir, samples):
    bam_dir  = os.path.join(results_dir, 'bwa', 'merged_library')
    peak_dir = os.path.join(bam_dir, 'macs2', 'broad_peak')
    qc_dir   = os.path.join(peak_dir, 'qc')
    ataqv_dir= os.path.join(bam_dir, 'ataqv', 'broad_peak')

    issues = defaultdict(list)

    for sample in samples:
        # BAM files
        for tag, pattern in [
            ('mkD BAM', f'{sample}.mLb.mkD.sorted.bam'),
            ('clN BAM', f'{sample}.mLb.clN.sorted.bam'),
        ]:
            path = os.path.join(bam_dir, pattern)
            if not os.path.exists(path):
                issues[sample].append(f"Missing {tag}: {pattern}")

        # Peak files
        peak_file = os.path.join(peak_dir, f'{sample}.mLb.clN_peaks.broadPeak')
        if not os.path.exists(peak_file):
            issues[sample].append(f"Missing broadPeak file")

        # FRiP score
        frip_file = os.path.join(qc_dir, f'{sample}.mLb.clN_peaks.FRiP_mqc.tsv')
        if not os.path.exists(frip_file):
            issues[sample].append(f"Missing FRiP score file → ATAQv도 skip되었을 가능성")

        # ATAQv
        ataqv_file = os.path.join(ataqv_dir, f'{sample}.ataqv.json')
        if not os.path.exists(ataqv_file):
            issues[sample].append(f"Missing ATAQv output")

    return issues

# ──────────────────────────────────────────────
# 3. Execution trace 파싱
# ──────────────────────────────────────────────
def parse_execution_trace(results_dir):
    """가장 최신 execution_trace 파일 파싱"""
    trace_files = sorted(glob.glob(
        os.path.join(results_dir, 'pipeline_info', 'execution_trace_*.txt')
    ))
    if not trace_files:
        return None, {}

    trace_file = trace_files[-1]
    tasks = defaultdict(list)  # process_name -> [sample, status, hash]

    with open(trace_file) as f:
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 6:
                continue
            task_hash = parts[1].strip()
            task_name = parts[3].strip()
            status    = parts[4].strip()
            m = re.search(r'\((.+)\)', task_name)
            sample = m.group(1) if m else ''
            # full process path를 key로 사용 (마지막 컴포넌트가 아닌 전체)
            process_key = re.sub(r' \(.*\)', '', task_name)  # sample 이름 제거
            tasks[process_key].append({
                'sample': sample,
                'status': status,
                'hash': task_hash,
                'full_name': task_name,
            })

    return trace_file, tasks

# ──────────────────────────────────────────────
# 4. Task 카운트 불일치 감지
# ──────────────────────────────────────────────
def check_task_counts(tasks, expected_n):
    """각 프로세스의 task 수가 expected_n(샘플 수)와 다른 경우 보고"""
    # partial match로 key 찾기
    def find_tasks(keyword):
        result = []
        for key, task_list in tasks.items():
            if keyword in key:
                result.extend(task_list)
        return result

    key_processes = {
        'MACS2_CALLPEAK':        ('MERGED_LIBRARY_CALL_ANNOTATE_PEAKS:MACS2_CALLPEAK', expected_n),
        'FRIP_SCORE':            ('MERGED_LIBRARY_CALL_ANNOTATE_PEAKS:FRIP_SCORE',      expected_n),
        'ATAQV_ATAQV':           ('MERGED_LIBRARY_ATAQV_ATAQV',                         expected_n),
        'PICARD_MARKDUPLICATES': ('MERGED_LIBRARY_MARKDUPLICATES_PICARD:PICARD_MARKDUPLICATES', expected_n),
        'BAMTOOLS_FILTER':       ('MERGED_LIBRARY_FILTER_BAM:BAMTOOLS_FILTER',           expected_n),
    }
    issues = {}
    for label, (keyword, expected) in key_processes.items():
        found = [t for t in find_tasks(keyword) if t['status'] == 'COMPLETED']
        if len(found) != expected:
            issues[label] = {
                'expected': expected,
                'actual': len(found),
                'samples': [t['sample'] for t in found],
            }
    return issues

# ──────────────────────────────────────────────
# 5. Work dir에서 BAM 파일명 vs meta.id 불일치 감지
# ──────────────────────────────────────────────
def check_bam_id_mismatch(tasks, work_dir, expected_samples):
    """
    FILTER_BAM:BAM_SORT_STATS_SAMTOOLS:SAMTOOLS_SORT 작업 디렉토리에서
    실제 BAM 파일명과 trace의 sample ID(meta.id)가 일치하는지 확인.

    이것이 이번 파이프라인에서 발생한 핵심 버그:
    SAMTOOLS_SORT (1D_REP1) work dir → 1D_REP3.mLb.clN.sorted.bam 생성
    """
    if not work_dir or not os.path.exists(work_dir):
        return []

    mismatches = []

    for key, task_list in tasks.items():
        # FILTER_BAM 안의 BAM_SORT_STATS_SAMTOOLS:SAMTOOLS_SORT만 검사
        if 'FILTER_BAM' not in key or 'BAM_SORT_STATS_SAMTOOLS' not in key or 'SAMTOOLS_SORT' not in key:
            continue

        for task in task_list:
            sample = task['sample']
            h = task['hash']
            if not h or '/' not in h:
                continue

            p1, p2 = h.split('/')
            dirs = glob.glob(os.path.join(work_dir, p1, f'{p2}*'))
            if not dirs:
                continue

            d = dirs[0]
            try:
                all_files = os.listdir(d)
            except PermissionError:
                continue

            cln_bams = [f for f in all_files
                        if f.endswith('.mLb.clN.sorted.bam') or f.endswith('.mLb.clN.bam')]

            for bam in cln_bams:
                bam_sample = bam.replace('.mLb.clN.sorted.bam', '').replace('.mLb.clN.bam', '')
                if bam_sample != sample:
                    mismatches.append({
                        'expected_sample': sample,
                        'actual_bam': bam,
                        'actual_sample': bam_sample,
                        'work_dir': d,
                        'hash': h,
                    })

    return mismatches

# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    results_dir = sys.argv[1]
    work_dir    = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD} ATAC-seq Pipeline Integrity Check{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"  Results : {results_dir}")
    if work_dir:
        print(f"  Work dir: {work_dir}")
    print()

    # 1. 샘플 목록
    samples = get_expected_samples(results_dir)
    if not samples:
        fail("No samples found in results directory")
        sys.exit(1)
    info(f"Found {len(samples)} samples: {', '.join(samples)}")
    print()

    # 2. 결과 파일 존재 여부
    print(f"{BOLD}[1] Output File Check{RESET}")
    file_issues = check_output_files(results_dir, samples)
    if not file_issues:
        ok("All expected output files present")
    else:
        for sample, problems in sorted(file_issues.items()):
            for p in problems:
                fail(f"{sample}: {p}")
    print()

    # 3. Execution trace 분석
    print(f"{BOLD}[2] Execution Trace Analysis{RESET}")
    trace_file, tasks = parse_execution_trace(results_dir)
    if not trace_file:
        warn("No execution trace found — skipping trace analysis")
    else:
        info(f"Trace: {os.path.basename(trace_file)}")

        # Task 카운트 불일치
        count_issues = check_task_counts(tasks, len(samples))
        if not count_issues:
            ok(f"All key processes ran for all {len(samples)} samples")
        else:
            for process, info_data in count_issues.items():
                expected = info_data['expected']
                actual   = info_data['actual']
                found    = set(info_data['samples'])
                missing  = sorted(set(samples) - found)
                fail(f"{process}: {actual}/{expected} samples completed")
                if missing:
                    warn(f"  → Missing samples: {', '.join(missing)}")
    print()

    # 4. BAM ID 불일치 검사 (work dir 필요)
    print(f"{BOLD}[3] BAM Filename vs Sample ID Mismatch Check{RESET}")
    if not work_dir:
        warn("Work directory not provided — skipping BAM ID mismatch check")
        info("Tip: pass nextflow work dir as 2nd argument to enable this check")
    elif not tasks:
        warn("No trace data — skipping")
    else:
        mismatches = check_bam_id_mismatch(tasks, work_dir, samples)
        if not mismatches:
            ok("No BAM filename / sample ID mismatches detected")
        else:
            for m in mismatches:
                fail(f"MISMATCH: meta.id='{m['expected_sample']}' but BAM='{m['actual_bam']}'")
                warn(f"  work dir: {m['work_dir']}")
                warn(f"  → This causes downstream FRIP/ATAQv to be silently skipped!")
    print()

    # 5. Summary
    print(f"{BOLD}{'='*60}{RESET}")
    total_issues = sum(len(v) for v in file_issues.values())
    mismatch_count = 0
    if work_dir and tasks:
        mismatch_count = len(check_bam_id_mismatch(tasks, work_dir, samples))

    if total_issues == 0 and mismatch_count == 0:
        print(f"{GREEN}{BOLD}✓ Pipeline integrity OK{RESET}")
    else:
        print(f"{RED}{BOLD}✗ Issues found: {total_issues} missing files, {mismatch_count} ID mismatches{RESET}")
        if mismatch_count > 0:
            print(f"\n{YELLOW}  Recommended action:{RESET}")
            print(f"  The affected samples are missing FRiP score and ATAQv data.")
            print(f"  Run ATAQv manually for these samples:")
            print(f"  → bash run_ataqv_missing.sh")
    print()


if __name__ == '__main__':
    main()
