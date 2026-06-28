#!/usr/bin/env python3
"""
make_samplesheet.py — ATAC-seq 샘플시트 자동 생성 도구

사용법:
    python3 make_samplesheet.py <metadata.tsv> <raw_data_dir> <output.csv> [options]

메타데이터 TSV 형식 (탭 구분, 헤더 필수):
    sample_id       condition   replicate   folder
    Veh_1           Veh         1           Neuron1
    Veh_2           Veh         2           Neuron2
    ...

    * folder  : raw_data_dir 아래의 샘플 디렉토리명 (생략 시 sample_id와 동일)
    * replicate: 같은 condition 내 생물학적 반복 번호 (1, 2, 3, ...)
                 pipeline 규칙상 sample_id가 다르면 각각 replicate=1 부터 시작

옵션:
    --lib-id   <str>   파일명에 포함된 라이브러리 ID (자동 감지 가능)
    --lanes    <str>   쉼표 구분 레인 목록 (예: L5,L6,L7,L8). 미지정시 자동 탐색
    --validate         생성 후 파이프라인 검증 스크립트(check_samplesheet.py) 실행
    --dry-run          파일 생성 없이 결과만 출력

예시:
    python3 bin/make_samplesheet.py \\
        metadata_pym.tsv \\
        /home/ngs/data/ygkim/2026/raw/X209SC26037376-Z01-F001_01/01.RawData \\
        samplesheet_pym.csv \\
        --validate
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path


# ── 인수 파싱 ─────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(
        description="ATAC-seq 샘플시트 자동 생성",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("metadata",  help="샘플 메타데이터 TSV 파일")
    p.add_argument("raw_dir",   help="Raw FASTQ 루트 디렉토리 (샘플 폴더들의 부모)")
    p.add_argument("output",    help="출력 샘플시트 CSV 경로")
    p.add_argument("--lib-id",  default=None, help="라이브러리 ID 문자열 (자동 감지 가능)")
    p.add_argument("--lanes",   default=None, help="레인 목록, 쉼표 구분 (예: L5,L6,L7,L8)")
    p.add_argument("--validate",action="store_true", help="생성 후 check_samplesheet.py 실행")
    p.add_argument("--dry-run", action="store_true", help="파일 생성 없이 미리보기")
    return p.parse_args()


# ── 메타데이터 읽기 ────────────────────────────────────────────────────────────
def read_metadata(path):
    """TSV 읽기. 필수 컬럼: sample_id, replicate. 선택: condition, folder"""
    required = {"sample_id", "replicate"}
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        missing = required - set(reader.fieldnames or [])
        if missing:
            sys.exit(f"ERROR: metadata에 필수 컬럼 없음: {', '.join(missing)}\n"
                     f"  필요한 헤더: sample_id  replicate  [condition]  [folder]")
        for i, row in enumerate(reader, 1):
            row["replicate"] = row["replicate"].strip()
            if not row["replicate"].isdigit():
                sys.exit(f"ERROR: row {i} replicate='{row['replicate']}' 가 정수가 아님")
            row["replicate"] = int(row["replicate"])
            if "folder" not in row or not row["folder"].strip():
                row["folder"] = row["sample_id"]
            rows.append(row)
    return rows


# ── FASTQ 파일 탐색 ────────────────────────────────────────────────────────────
def find_fastq_pairs(folder_path, lib_id=None, lanes=None):
    """
    folder_path 안의 FASTQ 파일들을 찾아 (lane, fq1, fq2) 목록 반환.
    lanes 미지정시 폴더에서 자동 탐색.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        sys.exit(f"ERROR: 디렉토리 없음: {folder_path}")

    # 모든 R1/R2 파일 탐색
    all_files = sorted(folder.glob("*.fq.gz")) + sorted(folder.glob("*.fastq.gz"))
    if not all_files:
        sys.exit(f"ERROR: FASTQ 파일 없음: {folder_path}")

    # 라이브러리 ID 자동 감지
    if lib_id is None:
        # 파일명 패턴: SampleName_LIBID_Lane_R.fq.gz
        sample_name = folder.name
        candidates = set()
        for f in all_files:
            stem = f.name
            # sample명 제거 후 lib_id 추출 (SampleName_ 이후 ~ _L숫자_ 이전)
            m = re.search(rf"{re.escape(sample_name)}_(.+?)_(L\d+)_[12]", stem)
            if m:
                candidates.add(m.group(1))
        if len(candidates) == 1:
            lib_id = candidates.pop()
        elif len(candidates) > 1:
            sys.exit(f"ERROR: 여러 라이브러리 ID 감지됨: {candidates}\n"
                     f"  --lib-id 옵션으로 명시해주세요")
        else:
            lib_id = ""  # lib_id 없는 파일명 구조

    # 레인 자동 탐색
    if lanes is None:
        lane_set = set()
        for f in all_files:
            m = re.search(r'_(L\d+)_[12]\.f', f.name)
            if m:
                lane_set.add(m.group(1))
        lanes = sorted(lane_set)
        if not lanes:
            # 레인 구분 없는 경우 단일 파일로 처리
            lanes = [None]

    # (lane, fq1, fq2) 조합
    pairs = []
    sample_name = folder.name
    for lane in lanes:
        if lane:
            if lib_id:
                fq1 = folder / f"{sample_name}_{lib_id}_{lane}_1.fq.gz"
                fq2 = folder / f"{sample_name}_{lib_id}_{lane}_2.fq.gz"
                if not fq1.exists():
                    fq1 = folder / f"{sample_name}_{lib_id}_{lane}_1.fastq.gz"
                    fq2 = folder / f"{sample_name}_{lib_id}_{lane}_2.fastq.gz"
            else:
                fq1 = folder / f"{sample_name}_{lane}_1.fq.gz"
                fq2 = folder / f"{sample_name}_{lane}_2.fq.gz"
        else:
            # 레인 없는 단일 파일
            r1 = [f for f in all_files if re.search(r'_1\.f(q|astq)\.gz$', f.name)]
            r2 = [f for f in all_files if re.search(r'_2\.f(q|astq)\.gz$', f.name)]
            if r1 and r2:
                fq1, fq2 = r1[0], r2[0]
            else:
                sys.exit(f"ERROR: R1/R2 파일을 찾을 수 없음: {folder_path}")

        if not Path(fq1).exists():
            sys.exit(f"ERROR: 파일 없음: {fq1}")
        if not Path(fq2).exists():
            sys.exit(f"ERROR: 파일 없음: {fq2}")
        pairs.append((lane, str(fq1), str(fq2)))

    return pairs


# ── replicate 검증 ─────────────────────────────────────────────────────────────
def validate_replicates(metadata):
    """
    pipeline check_samplesheet.py 규칙 사전 검증:
    각 sample_id의 replicate는 1..N 연속 정수여야 함.
    """
    from collections import defaultdict
    rep_map = defaultdict(set)
    for row in metadata:
        rep_map[row["sample_id"]].add(row["replicate"])

    errors = []
    for sample, reps in rep_map.items():
        reps_sorted = sorted(reps)
        expected = list(range(1, len(reps_sorted) + 1))
        if reps_sorted != expected:
            errors.append(
                f"  '{sample}': replicate={reps_sorted} → 1..{len(reps_sorted)} 이어야 함"
            )
    if errors:
        sys.exit("ERROR: replicate 검증 실패 (pipeline 규칙 위반)\n" + "\n".join(errors) +
                 "\n\n  각 sample_id의 replicate는 1부터 시작하는 연속 정수여야 합니다.\n"
                 "  같은 sample에 생물학적 반복이 없으면 replicate=1 로 설정하세요.")


# ── 메인 ──────────────────────────────────────────────────────────────────────
def main():
    args = parse_args()

    # 메타데이터 읽기
    metadata = read_metadata(args.metadata)

    # replicate 검증 (생성 전에 미리)
    validate_replicates(metadata)

    # 레인 목록
    lanes = args.lanes.split(",") if args.lanes else None

    # 각 샘플의 FASTQ 쌍 탐색
    rows = []  # [sample_id, fq1, fq2, replicate]
    print(f"\n{'─'*60}")
    print(f"  {'Sample':<20} {'Folder':<16} {'Rep':>3}  {'Lanes'}")
    print(f"{'─'*60}")

    for meta in metadata:
        sample_id  = meta["sample_id"]
        replicate  = meta["replicate"]
        folder_name = meta["folder"].strip()
        folder_path = os.path.join(args.raw_dir, folder_name)

        pairs = find_fastq_pairs(folder_path, lib_id=args.lib_id, lanes=lanes)
        lane_names = [p[0] or "single" for p in pairs]
        print(f"  {sample_id:<20} {folder_name:<16} {replicate:>3}  {', '.join(lane_names)}")

        for _, fq1, fq2 in pairs:
            rows.append([sample_id, fq1, fq2, replicate])

    print(f"{'─'*60}")
    print(f"  총 {len(metadata)}개 샘플, {len(rows)}개 행\n")

    # 출력
    if args.dry_run:
        print("[DRY-RUN] 아래 내용이 저장될 예정입니다:\n")
        print("sample,fastq_1,fastq_2,replicate")
        for r in rows:
            print(",".join(str(x) for x in r))
        return

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample", "fastq_1", "fastq_2", "replicate"])
        writer.writerows(rows)
    print(f"✅ 샘플시트 저장: {args.output}")

    # pipeline 공식 검증 실행
    if args.validate:
        import subprocess, tempfile
        checker = Path(__file__).parent / "check_samplesheet.py"
        # check_samplesheet.py는 출력 경로의 디렉토리를 생성하려 하므로
        # 실제 출력 파일과 같은 디렉토리에 임시 파일 생성
        out_dir = os.path.dirname(os.path.abspath(args.output))
        tmp_fd, tmp_out = tempfile.mkstemp(dir=out_dir, suffix=".validated.csv")
        os.close(tmp_fd)
        try:
            result = subprocess.run(
                [sys.executable, str(checker), args.output, tmp_out],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("✅ Pipeline 검증 통과 (check_samplesheet.py)")
            else:
                msg = (result.stderr or result.stdout).strip()
                print(f"❌ Pipeline 검증 실패:\n{msg}")
                sys.exit(1)
        finally:
            if os.path.exists(tmp_out):
                os.remove(tmp_out)


if __name__ == "__main__":
    main()
