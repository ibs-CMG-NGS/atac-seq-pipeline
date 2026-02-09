#!/usr/bin/env python3
"""
Convert master samples.csv to pipeline-specific format

This script converts a standardized master sample sheet (samples.csv) to
pipeline-specific formats for different workflow managers.

Supported formats:
- nextflow-atac: nf-core/atacseq samplesheet.csv format
- snakemake-rna: Snakemake RNA-seq samples.tsv format (future)
- wdl-wgs: WDL WGS inputs.json format (future)

Usage:
    python bin/convert_samplesheet.py samples.csv -o samplesheet.csv -p nextflow-atac

Author: IBS CMG NGS Team
Date: 2026-02-10
"""

import pandas as pd
import argparse
import sys
from pathlib import Path


def validate_master_sheet(df):
    """
    Validate master samples.csv for required columns and data integrity
    
    Args:
        df: pandas DataFrame of master sample sheet
        
    Raises:
        ValueError: If validation fails
    """
    required_cols = [
        'project_id', 'sample_id', 'condition', 'replicate',
        'library_type', 'read_type', 'fastq_1', 'species', 'genome_build'
    ]
    
    # Check for required columns
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    
    # Check for empty values in required columns
    for col in required_cols:
        if df[col].isna().any():
            empty_rows = df[df[col].isna()].index.tolist()
            raise ValueError(f"Column '{col}' has empty values in rows: {empty_rows}")
    
    # Validate read_type
    valid_read_types = ['single-end', 'paired-end']
    invalid_read_types = df[~df['read_type'].isin(valid_read_types)]['read_type'].unique()
    if len(invalid_read_types) > 0:
        raise ValueError(f"Invalid read_type values: {invalid_read_types}. Must be one of {valid_read_types}")
    
    # Check FASTQ file existence
    missing_files = []
    for idx, row in df.iterrows():
        fastq1 = Path(row['fastq_1'])
        if not fastq1.exists():
            missing_files.append(f"Row {idx}: {row['fastq_1']} (sample: {row['sample_id']})")
        
        if row['read_type'] == 'paired-end':
            if 'fastq_2' not in row or pd.isna(row['fastq_2']):
                raise ValueError(f"Row {idx}: paired-end sample {row['sample_id']} missing fastq_2")
            
            fastq2 = Path(row['fastq_2'])
            if not fastq2.exists():
                missing_files.append(f"Row {idx}: {row['fastq_2']} (sample: {row['sample_id']})")
    
    if missing_files:
        print("⚠️  Warning: The following FASTQ files were not found:")
        for f in missing_files:
            print(f"    {f}")
        
        response = input("\nContinue anyway? [y/N]: ")
        if response.lower() != 'y':
            sys.exit(1)


def convert_to_nextflow_atac(df, output_file):
    """
    Convert master samples.csv to nf-core/atacseq samplesheet.csv
    
    Format:
        sample,fastq_1,fastq_2,replicate
        
    Args:
        df: pandas DataFrame of master sample sheet
        output_file: path to output samplesheet.csv
    """
    # Filter ATAC-seq samples only
    df_atac = df[df['library_type'] == 'ATAC-seq'].copy()
    
    if len(df_atac) == 0:
        raise ValueError("No ATAC-seq samples found in master sheet")
    
    # Create Nextflow format
    # Use 'condition' as sample name (nf-core groups by this)
    nf_df = pd.DataFrame({
        'sample': df_atac['condition'],
        'fastq_1': df_atac['fastq_1'],
        'fastq_2': df_atac['fastq_2'] if 'fastq_2' in df_atac.columns else '',
        'replicate': df_atac['replicate']
    })
    
    # Handle single-end data (no fastq_2)
    if 'fastq_2' not in df_atac.columns:
        nf_df['fastq_2'] = ''
    
    # Save to file
    nf_df.to_csv(output_file, index=False)
    print(f"✅ Converted {len(nf_df)} samples to Nextflow format: {output_file}")
    
    # Print summary
    print(f"\n📊 Sample Summary:")
    print(f"   Total samples: {len(nf_df)}")
    print(f"   Unique conditions: {nf_df['sample'].nunique()}")
    print(f"   Genome build: {df_atac['genome_build'].unique()[0]}")
    print(f"   Species: {df_atac['species'].unique()[0]}")
    
    print(f"\n📋 Condition breakdown:")
    for cond, count in nf_df['sample'].value_counts().sort_index().items():
        print(f"      - {cond}: {count} replicates")
    
    # Check for single-end vs paired-end
    read_types = df_atac['read_type'].unique()
    if len(read_types) > 1:
        print(f"\n⚠️  Warning: Mixed read types detected: {read_types}")
    else:
        print(f"\n   Read type: {read_types[0]}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert master samples.csv to pipeline-specific format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert for ATAC-seq Nextflow pipeline
  python bin/convert_samplesheet.py samples.csv -o samplesheet.csv -p nextflow-atac
  
  # Specify project ID for filtering
  python bin/convert_samplesheet.py samples.csv -o samplesheet.csv -p nextflow-atac --project-id H2O2_Astrocyte_2025
  
  # Skip validation
  python bin/convert_samplesheet.py samples.csv -o samplesheet.csv -p nextflow-atac --no-validate
        """
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
    parser.add_argument(
        '--project-id',
        help='Filter samples by project ID'
    )
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip validation of master sheet'
    )
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.master_csv).exists():
        print(f"❌ Error: Input file not found: {args.master_csv}")
        sys.exit(1)
    
    # Read master sheet
    try:
        df = pd.read_csv(args.master_csv)
        print(f"📖 Read {len(df)} samples from {args.master_csv}")
    except Exception as e:
        print(f"❌ Error reading master sheet: {e}")
        sys.exit(1)
    
    # Filter by project ID if specified
    if args.project_id:
        df = df[df['project_id'] == args.project_id]
        if len(df) == 0:
            print(f"❌ Error: No samples found for project ID: {args.project_id}")
            sys.exit(1)
        print(f"   Filtered to project '{args.project_id}': {len(df)} samples")
    
    # Validate
    if not args.no_validate:
        try:
            validate_master_sheet(df)
            print("✅ Master sheet validation passed")
        except ValueError as e:
            print(f"❌ Validation failed: {e}")
            sys.exit(1)
    
    # Convert
    try:
        if args.pipeline == 'nextflow-atac':
            convert_to_nextflow_atac(df, args.output)
        else:
            print(f"❌ Pipeline format '{args.pipeline}' not yet implemented")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        sys.exit(1)
    
    print(f"\n✅ Success! Output written to: {args.output}")


if __name__ == '__main__':
    main()
