#!/usr/bin/env python3
"""
Reorganize nf-core/atacseq outputs to standardized structure

This script transforms nf-core/atacseq pipeline outputs into the standardized
directory structure for agent-based management.

Standard structure:
    {base_dir}/{project_id}/
    ├── metadata/
    ├── {sample_id}/
    │   └── atac-seq/
    │       ├── final_outputs/
    │       ├── intermediate/
    │       └── metadata/
    └── project_summary/

Usage:
    python bin/reorganize_outputs.py \\
        /path/to/nf-core/results \\
        /path/to/standard/base \\
        samples.csv \\
        --project-id H2O2_Astrocyte_2025

Author: IBS CMG NGS Team
Date: 2026-02-10
"""

import shutil
import json
import argparse
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime


def create_standard_structure(base_dir, project_id):
    """
    Create standardized directory structure
    
    Args:
        base_dir: Base directory for results
        project_id: Project identifier
        
    Returns:
        Path: Project base directory
    """
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
        print(f"  📁 Created: {d.relative_to(base_dir)}")
    
    return base


def create_sample_structure(standard_base, sample_id):
    """
    Create sample-specific directory structure
    
    Args:
        standard_base: Standard structure base directory
        sample_id: Sample identifier
        
    Returns:
        Path: Sample base directory
    """
    sample_dir = standard_base / sample_id / 'atac-seq'
    
    dirs = [
        sample_dir / 'final_outputs' / 'bam',
        sample_dir / 'final_outputs' / 'peaks',
        sample_dir / 'final_outputs' / 'bigwig',
        sample_dir / 'final_outputs' / 'qc',
        sample_dir / 'intermediate' / 'trimmed',
        sample_dir / 'intermediate' / 'fastqc',
        sample_dir / 'intermediate' / 'logs',
        sample_dir / 'metadata'
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    return sample_dir


def copy_or_link(src, dst, use_symlink=False):
    """
    Copy or symlink a file
    
    Args:
        src: Source file path
        dst: Destination file path
        use_symlink: Use symbolic link instead of copy
    """
    src = Path(src)
    dst = Path(dst)
    
    if not src.exists():
        return False
    
    # Create parent directory if needed
    dst.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing file/link
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    
    if use_symlink:
        dst.symlink_to(src.resolve())
    else:
        shutil.copy2(src, dst)
    
    return True


def reorganize_sample_outputs(nf_results, standard_base, sample_id, condition, 
                               replicate, use_symlink=False, peak_type='broadPeak'):
    """
    Reorganize single sample's nf-core outputs to standard structure
    
    Args:
        nf_results: nf-core/atacseq results directory
        standard_base: Standard structure base directory
        sample_id: Sample ID (e.g., CONTROL_REP1)
        condition: Condition (e.g., CONTROL)
        replicate: Replicate number
        use_symlink: Use symbolic links instead of copying
        peak_type: Peak type (broadPeak or narrowPeak)
        
    Returns:
        Path: Sample directory
    """
    nf_res = Path(nf_results)
    sample_dir = create_sample_structure(standard_base, sample_id)
    
    final_out = sample_dir / 'final_outputs'
    intermediate = sample_dir / 'intermediate'
    
    # Determine nf-core sample pattern
    # nf-core uses format: {condition}_REP{replicate} or just {condition}
    nf_sample = f"{condition}"
    
    print(f"\n  📦 Processing: {sample_id}")
    files_copied = 0
    files_failed = 0
    
    # === FINAL OUTPUTS ===
    
    # BAM files (merged library)
    bam_patterns = [
        nf_res / 'bwa' / 'mergedLibrary' / f'{nf_sample}.mLb.clN.sorted.bam',
        nf_res / 'bwa' / 'mergedLibrary' / f'{nf_sample}.sorted.bam'
    ]
    
    for bam_src in bam_patterns:
        if bam_src.exists():
            bam_dst = final_out / 'bam' / 'aligned.sorted.bam'
            if copy_or_link(bam_src, bam_dst, use_symlink):
                files_copied += 1
                print(f"     ✅ BAM: {bam_src.name}")
                
                # Copy BAM index
                bai_src = Path(str(bam_src) + '.bai')
                if bai_src.exists():
                    bai_dst = final_out / 'bam' / 'aligned.sorted.bam.bai'
                    copy_or_link(bai_src, bai_dst, use_symlink)
                    files_copied += 1
            break
    
    # Peak files
    peak_dir = nf_res / 'bwa' / 'mergedLibrary' / 'macs2' / peak_type
    if peak_dir.exists():
        # Broad peaks
        if peak_type == 'broadPeak':
            peak_src = peak_dir / f'{nf_sample}_peaks.broadPeak'
            if peak_src.exists():
                peak_dst = final_out / 'peaks' / 'broad_peaks.bed'
                if copy_or_link(peak_src, peak_dst, use_symlink):
                    files_copied += 1
                    print(f"     ✅ Peaks: {peak_src.name}")
        
        # Narrow peaks
        elif peak_type == 'narrowPeak':
            peak_src = peak_dir / f'{nf_sample}_peaks.narrowPeak'
            if peak_src.exists():
                peak_dst = final_out / 'peaks' / 'narrow_peaks.bed'
                if copy_or_link(peak_src, peak_dst, use_symlink):
                    files_copied += 1
                    print(f"     ✅ Peaks: {peak_src.name}")
    
    # BigWig files
    bw_dir = nf_res / 'bwa' / 'mergedLibrary' / 'bigwig'
    if bw_dir.exists():
        bw_patterns = [
            bw_dir / f'{nf_sample}.bigWig',
            bw_dir / f'{nf_sample}.bw'
        ]
        
        for bw_src in bw_patterns:
            if bw_src.exists():
                bw_dst = final_out / 'bigwig' / 'coverage.bigWig'
                if copy_or_link(bw_src, bw_dst, use_symlink):
                    files_copied += 1
                    print(f"     ✅ BigWig: {bw_src.name}")
                break
    
    # === INTERMEDIATE FILES ===
    
    # Trimmed FASTQ
    trim_dir = nf_res / 'trimgalore'
    if trim_dir.exists():
        for fq in trim_dir.glob(f'{nf_sample}*.fq.gz'):
            fq_dst = intermediate / 'trimmed' / fq.name
            if copy_or_link(fq, fq_dst, use_symlink):
                files_copied += 1
    
    # FastQC reports
    fastqc_dir = nf_res / 'fastqc'
    if fastqc_dir.exists():
        for html in fastqc_dir.glob(f'{nf_sample}*_fastqc.html'):
            html_dst = intermediate / 'fastqc' / html.name
            if copy_or_link(html, html_dst, use_symlink):
                files_copied += 1
        
        for zip_file in fastqc_dir.glob(f'{nf_sample}*_fastqc.zip'):
            zip_dst = intermediate / 'fastqc' / zip_file.name
            copy_or_link(zip_file, zip_dst, use_symlink)
    
    print(f"     📊 Copied/linked {files_copied} files")
    
    return sample_dir


def copy_project_summary(nf_results, standard_base, peak_type='broadPeak', use_symlink=False):
    """
    Copy project-level summary files
    
    Args:
        nf_results: nf-core results directory
        standard_base: Standard structure base directory
        peak_type: Peak type (broadPeak or narrowPeak)
        use_symlink: Use symbolic links
    """
    nf_res = Path(nf_results)
    project_summary = standard_base / 'project_summary'
    
    print(f"\n  📊 Copying project-level outputs...")
    files_copied = 0
    
    # MultiQC report
    mqc_src = nf_res / 'multiqc' / peak_type / 'multiqc_report.html'
    if mqc_src.exists():
        mqc_dst = project_summary / 'qc' / 'multiqc_report.html'
        if copy_or_link(mqc_src, mqc_dst, use_symlink):
            files_copied += 1
            print(f"     ✅ MultiQC report")
    
    # MultiQC data directory
    mqc_data_src = nf_res / 'multiqc' / peak_type / 'multiqc_data'
    if mqc_data_src.exists():
        mqc_data_dst = project_summary / 'qc' / 'multiqc_data'
        if mqc_data_dst.exists():
            shutil.rmtree(mqc_data_dst)
        shutil.copytree(mqc_data_src, mqc_data_dst)
        files_copied += 1
        print(f"     ✅ MultiQC data")
    
    # Consensus peaks
    consensus_dir = nf_res / 'bwa' / 'mergedLibrary' / 'macs2' / peak_type / 'consensus'
    if consensus_dir.exists():
        consensus_dst = project_summary / 'peaks'
        for consensus_file in consensus_dir.glob('*.bed'):
            dst = consensus_dst / consensus_file.name
            if copy_or_link(consensus_file, dst, use_symlink):
                files_copied += 1
        print(f"     ✅ Consensus peaks")
    
    # IGV session
    igv_src = nf_res / 'igv' / 'igv_session.xml'
    if igv_src.exists():
        igv_dst = project_summary / 'igv_session.xml'
        copy_or_link(igv_src, igv_dst, use_symlink)
        files_copied += 1
        print(f"     ✅ IGV session")
    
    print(f"     📊 Copied {files_copied} project files")


def save_metadata(standard_base, project_id, samples_csv, args):
    """
    Save project metadata
    
    Args:
        standard_base: Standard structure base directory
        project_id: Project ID
        samples_csv: Path to master samples.csv
        args: Command line arguments
    """
    metadata_dir = standard_base / 'metadata'
    
    # Copy master samples.csv
    samples_src = Path(samples_csv)
    if samples_src.exists():
        samples_dst = metadata_dir / 'samples_master.csv'
        shutil.copy2(samples_src, samples_dst)
        print(f"     ✅ Master samples.csv")
    
    # Save reorganization metadata
    reorg_meta = {
        'project_id': project_id,
        'reorganization_date': datetime.now().isoformat(),
        'source_results': str(args.nf_results),
        'peak_type': args.peak_type,
        'use_symlink': args.symlink,
        'pipeline_version': 'nf-core/atacseq v2.1.2'
    }
    
    meta_file = metadata_dir / 'reorganization_info.json'
    with open(meta_file, 'w') as f:
        json.dump(reorg_meta, f, indent=2)
    
    print(f"     ✅ Reorganization metadata")


def main():
    parser = argparse.ArgumentParser(
        description='Reorganize nf-core/atacseq outputs to standardized structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Reorganize with file copying
  python bin/reorganize_outputs.py \\
      ./results \\
      /home/ngs/data/results \\
      samples_H2O2_astrocyte.csv \\
      --project-id H2O2_Astrocyte_2025
  
  # Reorganize with symbolic links (saves space)
  python bin/reorganize_outputs.py \\
      ./results \\
      /home/ngs/data/results \\
      samples_H2O2_astrocyte.csv \\
      --project-id H2O2_Astrocyte_2025 \\
      --symlink
  
  # Use narrow peaks instead of broad peaks
  python bin/reorganize_outputs.py \\
      ./results \\
      /home/ngs/data/results \\
      samples.csv \\
      --project-id MyProject \\
      --peak-type narrowPeak
        """
    )
    
    parser.add_argument(
        'nf_results',
        help='Path to nf-core/atacseq results directory'
    )
    parser.add_argument(
        'output_base',
        help='Base directory for standardized outputs'
    )
    parser.add_argument(
        'samples_csv',
        help='Master samples.csv file'
    )
    parser.add_argument(
        '--project-id',
        required=True,
        help='Project ID'
    )
    parser.add_argument(
        '--peak-type',
        default='broadPeak',
        choices=['broadPeak', 'narrowPeak'],
        help='Peak type to use (default: broadPeak)'
    )
    parser.add_argument(
        '--symlink',
        action='store_true',
        help='Use symbolic links instead of copying files (saves space)'
    )
    parser.add_argument(
        '--multiqc-data',
        help='Path to MultiQC data directory (if different from nf_results/multiqc/*/multiqc_data)'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.nf_results).exists():
        print(f"❌ Error: nf-core results directory not found: {args.nf_results}")
        sys.exit(1)
    
    if not Path(args.samples_csv).exists():
        print(f"❌ Error: Samples CSV not found: {args.samples_csv}")
        sys.exit(1)
    
    # Read samples
    try:
        df = pd.read_csv(args.samples_csv)
        df_atac = df[df['library_type'] == 'ATAC-seq']
        
        if args.project_id:
            df_atac = df_atac[df_atac['project_id'] == args.project_id]
        
        if len(df_atac) == 0:
            print(f"❌ Error: No ATAC-seq samples found for project {args.project_id}")
            sys.exit(1)
        
        print(f"📖 Found {len(df_atac)} ATAC-seq samples for project {args.project_id}")
    except Exception as e:
        print(f"❌ Error reading samples CSV: {e}")
        sys.exit(1)
    
    # Create standard structure
    print(f"\n📁 Creating standard structure in: {args.output_base}/{args.project_id}")
    standard_base = create_standard_structure(args.output_base, args.project_id)
    
    # Reorganize each sample
    print(f"\n📦 Reorganizing {len(df_atac)} samples...")
    for idx, row in df_atac.iterrows():
        try:
            reorganize_sample_outputs(
                args.nf_results,
                standard_base,
                row['sample_id'],
                row['condition'],
                row['replicate'],
                use_symlink=args.symlink,
                peak_type=args.peak_type
            )
        except Exception as e:
            print(f"     ⚠️  Error processing {row['sample_id']}: {e}")
    
    # Copy project-level outputs
    copy_project_summary(args.nf_results, standard_base, args.peak_type, args.symlink)
    
    # Save metadata
    print(f"\n  💾 Saving metadata...")
    save_metadata(standard_base, args.project_id, args.samples_csv, args)
    
    print(f"\n✅ Reorganization complete!")
    print(f"📂 Standardized outputs: {standard_base}")
    print(f"\n📋 Next steps:")
    print(f"   1. Generate manifest files:")
    print(f"      for sample in {standard_base}/*/atac-seq/final_outputs; do")
    print(f"          python bin/generate_manifest.py --sample-id ... --final-outputs-dir $sample")
    print(f"      done")
    print(f"   2. Review MultiQC report: {standard_base}/project_summary/qc/multiqc_report.html")


if __name__ == '__main__':
    main()
