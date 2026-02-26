#!/usr/bin/env python3
"""
Generate manifest.json for ATAC-seq sample final outputs

This script creates a manifest.json file that contains metadata about
final outputs for each sample, including QC metrics and file locations.

Usage:
    python bin/generate_manifest.py \
        --sample-id CONTROL_REP1 \
        --project-id H2O2_Astrocyte_2025 \
        --final-outputs-dir /path/to/sample/atac-seq/final_outputs \
        --multiqc-data /path/to/multiqc/data

Author: IBS CMG NGS Team
Date: 2026-02-10
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd


def extract_qc_metrics(multiqc_data_dir, sample_id, condition):
    """
    Extract QC metrics from MultiQC data files
    
    Args:
        multiqc_data_dir: Path to multiqc_data directory
        sample_id: Sample ID (e.g., H2O2_100uM_REP1)
        condition: nf-core sample name for MultiQC lookup (e.g., 100uM_REP1)
        
    Returns:
        dict: QC metrics
    """
    metrics = {}
    multiqc_dir = Path(multiqc_data_dir)
    
    if not multiqc_dir.exists():
        print(f"⚠️  Warning: MultiQC data directory not found: {multiqc_dir}")
        return metrics
    
    # Use condition if provided, otherwise fall back to sample_id
    lookup_name = condition if condition else sample_id
    
    try:
        # FRiP score - use lookup_name (e.g., 100uM_REP1)
        frip_file = multiqc_dir / 'multiqc_mlib_frip_score-plot.txt'
        if frip_file.exists():
            df_frip = pd.read_csv(frip_file, sep='\t', index_col=0)
            if lookup_name in df_frip.index and lookup_name in df_frip.columns:
                metrics['frip_score'] = float(df_frip.loc[lookup_name, lookup_name])
        
        # Peak count - use lookup_name
        peak_file = multiqc_dir / 'multiqc_mlib_peak_count-plot.txt'
        if peak_file.exists():
            df_peak = pd.read_csv(peak_file, sep='\t', index_col=0)
            # Peak count file has sample name in index
            if lookup_name in df_peak.index:
                # Get the peak count value (first non-NaN value in the row)
                peak_values = df_peak.loc[lookup_name]
                peak_count = peak_values.dropna().values[0] if len(peak_values.dropna()) > 0 else 0
                metrics['peak_count'] = int(peak_count)
        
        # Alignment metrics from Picard - use lookup_name
        picard_file = multiqc_dir / 'multiqc_picard_AlignmentSummaryMetrics.txt'
        if picard_file.exists():
            df_picard = pd.read_csv(picard_file, sep='\t')
            # Find row matching lookup_name
            sample_rows = df_picard[df_picard['Sample'] == lookup_name]
            if not sample_rows.empty:
                row = sample_rows.iloc[0]
                metrics['total_reads'] = int(row['TOTAL_READS']) if 'TOTAL_READS' in row else 0
                metrics['aligned_reads'] = int(row['PF_READS_ALIGNED']) if 'PF_READS_ALIGNED' in row else 0
                metrics['alignment_rate'] = float(row['PCT_PF_READS_ALIGNED']) if 'PCT_PF_READS_ALIGNED' in row else 0.0
                metrics['duplicate_rate'] = float(row.get('PERCENT_DUPLICATION', 0.0))
        
        # Duplication metrics - use lookup_name
        dup_file = multiqc_dir / 'multiqc_picard_dups.txt'
        if dup_file.exists():
            df_dup = pd.read_csv(dup_file, sep='\t')
            sample_rows = df_dup[df_dup['Sample'] == lookup_name]
            if not sample_rows.empty:
                row = sample_rows.iloc[0]
                metrics['duplicate_rate'] = float(row['PERCENT_DUPLICATION']) if 'PERCENT_DUPLICATION' in row else 0.0
        
    except Exception as e:
        print(f"⚠️  Warning: Error extracting QC metrics: {e}")
    
    return metrics


def get_file_info(file_path):
    """
    Get file metadata (size, modification time)
    
    Args:
        file_path: Path to file
        
    Returns:
        dict: File metadata
    """
    path = Path(file_path)
    if not path.exists():
        return None
    
    stat = path.stat()
    return {
        'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
    }


def scan_final_outputs(final_outputs_dir):
    """
    Scan final_outputs directory and catalog all files
    
    Args:
        final_outputs_dir: Path to final_outputs directory
        
    Returns:
        dict: Categorized file paths
    """
    base_dir = Path(final_outputs_dir)
    outputs = {}
    
    # BAM files
    bam_dir = base_dir / 'bam'
    if bam_dir.exists():
        bam_files = list(bam_dir.glob('*.bam'))
        bai_files = list(bam_dir.glob('*.bai'))
        
        if bam_files:
            bam_file = bam_files[0]
            outputs['bam'] = {
                'aligned_bam': str(bam_file.relative_to(base_dir)),
                'bam_index': str(bai_files[0].relative_to(base_dir)) if bai_files else None
            }
            
            # Add file metadata
            bam_info = get_file_info(bam_file)
            if bam_info:
                outputs['bam'].update(bam_info)
    
    # Peak files
    peaks_dir = base_dir / 'peaks'
    if peaks_dir.exists():
        broad_peaks = list(peaks_dir.glob('*broad*.bed'))
        narrow_peaks = list(peaks_dir.glob('*narrow*.bed'))
        
        outputs['peaks'] = {}
        if broad_peaks:
            outputs['peaks']['broad_peaks'] = str(broad_peaks[0].relative_to(base_dir))
        if narrow_peaks:
            outputs['peaks']['narrow_peaks'] = str(narrow_peaks[0].relative_to(base_dir))
    
    # BigWig files
    bigwig_dir = base_dir / 'bigwig'
    if bigwig_dir.exists():
        bigwig_files = list(bigwig_dir.glob('*.bigWig')) + list(bigwig_dir.glob('*.bw'))
        
        if bigwig_files:
            outputs['bigwig'] = {}
            for bw in bigwig_files:
                if 'normalized' in bw.name.lower() or 'norm' in bw.name.lower():
                    outputs['bigwig']['normalized'] = str(bw.relative_to(base_dir))
                else:
                    outputs['bigwig']['coverage'] = str(bw.relative_to(base_dir))
    
    # QC files
    qc_dir = base_dir / 'qc'
    if qc_dir.exists():
        outputs['qc'] = {}
        
        for qc_file in qc_dir.iterdir():
            if qc_file.is_file():
                rel_path = str(qc_file.relative_to(base_dir))
                if qc_file.suffix == '.json':
                    outputs['qc']['summary'] = rel_path
                elif qc_file.suffix == '.html':
                    outputs['qc']['report'] = rel_path
                elif 'frip' in qc_file.name.lower():
                    outputs['qc']['frip_score_file'] = rel_path
    
    return outputs


def generate_manifest(args):
    """
    Generate manifest.json for a sample
    
    Args:
        args: Command line arguments
        
    Returns:
        dict: Manifest data
    """
    manifest = {
        'sample_id': args.sample_id,
        'project_id': args.project_id,
        'pipeline_type': 'atac-seq',
        'pipeline_version': args.pipeline_version,
        'execution_date': datetime.now().isoformat(),
        'genome_build': args.genome_build,
        'aligner': args.aligner,
        'peak_caller': args.peak_caller
    }
    
    # Scan final outputs
    final_outputs = scan_final_outputs(args.final_outputs_dir)
    manifest['final_outputs'] = final_outputs
    
    # Extract QC metrics
    if args.multiqc_data:
        qc_metrics = extract_qc_metrics(args.multiqc_data, args.sample_id, args.condition)
        manifest['qc_metrics'] = qc_metrics
        
        # Add FRiP and peak count to peaks section if available
        if 'peaks' in final_outputs and qc_metrics:
            if 'frip_score' in qc_metrics:
                final_outputs['peaks']['frip_score'] = qc_metrics['frip_score']
            if 'peak_count' in qc_metrics:
                final_outputs['peaks']['peak_count'] = qc_metrics['peak_count']
    else:
        manifest['qc_metrics'] = {}
    
    # Determine status
    manifest['status'] = 'completed'
    manifest['warnings'] = []
    manifest['errors'] = []

    # Basic QC checks
    if 'qc_metrics' in manifest:
        qc = manifest['qc_metrics']

        if qc.get('frip_score', 0) < 0.3:
            manifest['warnings'].append(f"Low FRiP score: {qc.get('frip_score', 0):.3f} < 0.3")

        if qc.get('peak_count', 0) < 1000:
            manifest['warnings'].append(f"Low peak count: {qc.get('peak_count', 0)} < 1000")

        if qc.get('alignment_rate', 0) < 0.7:
            manifest['warnings'].append(f"Low alignment rate: {qc.get('alignment_rate', 0):.1%} < 70%")

        # Set QC status field for agent readability
        manifest['qc_metrics']['status'] = 'WARN' if manifest['warnings'] else 'PASS'

    manifest['next_steps'] = []

    return manifest


def main():
    parser = argparse.ArgumentParser(
        description='Generate manifest.json for ATAC-seq sample final outputs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate manifest with MultiQC data
  python bin/generate_manifest.py \\
      --sample-id CONTROL_REP1 \\
      --project-id H2O2_Astrocyte_2025 \\
      --condition CONTROL \\
      --final-outputs-dir /path/to/CONTROL_REP1/atac-seq/final_outputs \\
      --multiqc-data /path/to/multiqc_data \\
      --output manifest.json
  
  # Generate manifest without QC metrics
  python bin/generate_manifest.py \\
      --sample-id CONTROL_REP1 \\
      --project-id H2O2_Astrocyte_2025 \\
      --final-outputs-dir /path/to/CONTROL_REP1/atac-seq/final_outputs \\
      --output manifest.json
        """
    )
    
    parser.add_argument(
        '--sample-id',
        required=True,
        help='Sample ID (e.g., CONTROL_REP1)'
    )
    parser.add_argument(
        '--project-id',
        required=True,
        help='Project ID (e.g., H2O2_Astrocyte_2025)'
    )
    parser.add_argument(
        '--condition',
        help='Condition name (e.g., CONTROL) - used for MultiQC data lookup'
    )
    parser.add_argument(
        '--final-outputs-dir',
        required=True,
        help='Path to final_outputs directory'
    )
    parser.add_argument(
        '--multiqc-data',
        help='Path to multiqc_data directory (optional)'
    )
    parser.add_argument(
        '--output',
        help='Output manifest.json file (default: auto-detect from final-outputs-dir)'
    )
    parser.add_argument(
        '--pipeline-version',
        default='nf-core/atacseq v2.1.2',
        help='Pipeline version (default: nf-core/atacseq v2.1.2)'
    )
    parser.add_argument(
        '--genome-build',
        default='GRCm39',
        help='Genome build (default: GRCm39)'
    )
    parser.add_argument(
        '--aligner',
        default='bwa',
        help='Aligner used (default: bwa)'
    )
    parser.add_argument(
        '--peak-caller',
        default='macs2',
        help='Peak caller used (default: macs2)'
    )
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty print JSON output'
    )
    
    args = parser.parse_args()
    
    # Check if final_outputs_dir exists
    if not Path(args.final_outputs_dir).exists():
        print(f"❌ Error: final_outputs directory not found: {args.final_outputs_dir}")
        sys.exit(1)
    
    # Auto-detect output path if not specified
    if args.output is None:
        # Assume structure: .../sample_id/atac-seq/final_outputs
        # Place manifest in: .../sample_id/atac-seq/metadata/manifest.json
        final_outputs_path = Path(args.final_outputs_dir).resolve()
        # Go up two levels: final_outputs -> atac-seq -> sample_dir
        metadata_dir = final_outputs_path.parent / 'metadata'
        metadata_dir.mkdir(parents=True, exist_ok=True)
        args.output = str(metadata_dir / 'manifest.json')
    
    # Generate manifest
    try:
        manifest = generate_manifest(args)
        
        # Save to file
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            if args.pretty:
                json.dump(manifest, f, indent=2)
            else:
                json.dump(manifest, f, indent=2)  # Always pretty for readability
        
        print(f"✅ Manifest generated: {output_path}")
        
        # Print summary
        print(f"\n📊 Manifest Summary:")
        print(f"   Sample ID: {manifest['sample_id']}")
        print(f"   Project ID: {manifest['project_id']}")
        print(f"   Status: {manifest['status']}")
        
        if 'qc_metrics' in manifest and manifest['qc_metrics']:
            print(f"\n   QC Metrics:")
            qc = manifest['qc_metrics']
            if 'frip_score' in qc:
                print(f"      - FRiP score: {qc['frip_score']:.3f}")
            if 'peak_count' in qc:
                print(f"      - Peak count: {qc['peak_count']:,}")
            if 'alignment_rate' in qc:
                print(f"      - Alignment rate: {qc['alignment_rate']:.1%}")
        
        if manifest.get('warnings'):
            print(f"\n⚠️  Warnings:")
            for warning in manifest['warnings']:
                print(f"      - {warning}")
        
        if manifest.get('errors'):
            print(f"\n❌ Errors:")
            for error in manifest['errors']:
                print(f"      - {error}")
        
    except Exception as e:
        print(f"❌ Error generating manifest: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
