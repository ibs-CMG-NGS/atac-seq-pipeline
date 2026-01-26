#!/usr/bin/env python3
"""
ATAC-seq specific FastQC report analyzer
Automatically flags samples with quality issues based on ATAC-seq specific criteria
"""

import sys
import re
from pathlib import Path
import json
import argparse


class ATACseqQCChecker:
    """ATAC-seq specific QC criteria checker"""
    
    # ATAC-seq에서 FAIL/WARNING이 허용되는 모듈
    ATAC_EXPECTED_WARNINGS = {
        'Per base sequence content',  # Tn5 bias at read start
        'Sequence Duplication Levels',  # High duplication normal for open chromatin
        'Kmer Content',  # Tn5 sequence preference
        'Per tile sequence quality',  # Sometimes shows patterns
    }
    
    # 임계값 설정
    THRESHOLDS = {
        'min_mean_quality': 28,
        'min_passing_quality_pct': 0.8,  # 80% of bases > Q28
        'max_adapter_content': 10,  # %
        'max_duplication_pct': 85,  # %
        'min_sequence_length': 50,
        'min_gc_content': 30,
        'max_gc_content': 65,
        'max_n_content': 5,  # % N bases
    }
    
    def __init__(self, fastqc_data_path):
        self.path = Path(fastqc_data_path)
        self.sample_name = self.path.parent.name.replace('_fastqc', '')
        self.data = self._parse_fastqc_data()
        self.issues = []
        self.warnings = []
        
    def _parse_fastqc_data(self):
        """Parse fastqc_data.txt file"""
        data = {
            'basic_statistics': {},
            'per_base_quality': [],
            'per_sequence_quality': {},
            'adapter_content': {},
            'module_status': {},
            'sequence_length_distribution': {},
            'overrepresented_sequences': []
        }
        
        with open(self.path, 'r') as f:
            current_module = None
            for line in f:
                line = line.strip()
                
                # Module headers
                if line.startswith('>>'):
                    if line.startswith('>>END_MODULE'):
                        current_module = None
                    else:
                        module_name = line[2:].split('\t')[0]
                        status = line.split('\t')[1] if '\t' in line else 'unknown'
                        data['module_status'][module_name] = status
                        current_module = module_name
                
                # Skip comment lines
                elif line.startswith('#'):
                    continue
                    
                # Parse specific modules
                elif current_module == 'Basic Statistics' and '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        key, value = parts[0], parts[1]
                        data['basic_statistics'][key] = value
                    
                elif current_module == 'Per base sequence quality' and '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        try:
                            data['per_base_quality'].append({
                                'base': parts[0],
                                'mean': float(parts[1])
                            })
                        except ValueError:
                            pass
                            
                elif current_module == 'Adapter Content' and '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        try:
                            # Check if any adapter has high content
                            for val in parts[1:]:
                                if val and float(val) > data['adapter_content'].get('max', 0):
                                    data['adapter_content']['max'] = float(val)
                        except ValueError:
                            pass
        
        return data
    
    def check_quality(self):
        """Run all QC checks"""
        self._check_basic_stats()
        self._check_per_base_quality()
        self._check_module_failures()
        self._check_adapter_content()
        
        return {
            'sample': self.sample_name,
            'status': 'PASS' if len(self.issues) == 0 else 'FAIL',
            'issues': self.issues,
            'warnings': self.warnings,
            'requires_review': len(self.issues) > 0,
            'basic_stats': self.data['basic_statistics']
        }
    
    def _check_basic_stats(self):
        """Check basic statistics"""
        stats = self.data['basic_statistics']
        
        # Total sequences
        if 'Total Sequences' in stats:
            total_seq = int(stats['Total Sequences'])
            if total_seq < 1000000:  # Less than 1M reads
                self.warnings.append(
                    f"Low read count: {total_seq:,} reads (recommended: >5M for ATAC-seq)"
                )
        
        # Sequence length
        if 'Sequence length' in stats:
            seq_len = stats['Sequence length']
            # Parse "35-151" or "151"
            if '-' in seq_len:
                min_len = int(seq_len.split('-')[0])
                max_len = int(seq_len.split('-')[1])
            else:
                min_len = max_len = int(seq_len)
            
            if min_len < self.THRESHOLDS['min_sequence_length']:
                self.issues.append(
                    f"Short reads: minimum {min_len}bp (recommended: >{self.THRESHOLDS['min_sequence_length']}bp)"
                )
        
        # GC content
        if '%GC' in stats:
            gc = int(stats['%GC'])
            if gc < self.THRESHOLDS['min_gc_content']:
                self.issues.append(
                    f"Low GC content: {gc}% (expected: >{self.THRESHOLDS['min_gc_content']}%)"
                )
            elif gc > self.THRESHOLDS['max_gc_content']:
                self.issues.append(
                    f"High GC content: {gc}% (expected: <{self.THRESHOLDS['max_gc_content']}%)"
                )
        
        # Sequences flagged as poor quality
        if 'Sequences flagged as poor quality' in stats:
            poor_qual = int(stats['Sequences flagged as poor quality'])
            if poor_qual > 0:
                total = int(stats.get('Total Sequences', 1))
                pct = (poor_qual / total) * 100
                if pct > 5:
                    self.issues.append(
                        f"High poor quality sequences: {poor_qual:,} ({pct:.1f}%)"
                    )
    
    def _check_per_base_quality(self):
        """Check per base sequence quality"""
        if not self.data['per_base_quality']:
            return
        
        low_quality_positions = 0
        total_positions = len(self.data['per_base_quality'])
        
        for pos_data in self.data['per_base_quality']:
            if pos_data['mean'] < self.THRESHOLDS['min_mean_quality']:
                low_quality_positions += 1
        
        if total_positions > 0:
            pct_low = low_quality_positions / total_positions
            if pct_low > (1 - self.THRESHOLDS['min_passing_quality_pct']):
                self.issues.append(
                    f"Low quality bases: {low_quality_positions}/{total_positions} positions "
                    f"below Q{self.THRESHOLDS['min_mean_quality']} "
                    f"({pct_low*100:.1f}% of read)"
                )
            elif pct_low > 0.1:  # More than 10% low quality
                self.warnings.append(
                    f"Some low quality bases: {low_quality_positions}/{total_positions} positions "
                    f"below Q{self.THRESHOLDS['min_mean_quality']}"
                )
    
    def _check_module_failures(self):
        """Check for unexpected module failures"""
        for module, status in self.data['module_status'].items():
            if status == 'fail':
                # Check if this failure is expected for ATAC-seq
                if module not in self.ATAC_EXPECTED_WARNINGS:
                    self.issues.append(f"Unexpected FAIL: {module}")
                # For expected warnings, just note them
                # (don't add to issues, these are normal for ATAC-seq)
                    
            elif status == 'warn':
                if module not in self.ATAC_EXPECTED_WARNINGS:
                    self.warnings.append(f"Warning: {module}")
    
    def _check_adapter_content(self):
        """Check adapter contamination"""
        # Check module status
        if self.data['module_status'].get('Adapter Content') == 'fail':
            max_adapter = self.data['adapter_content'].get('max', 0)
            if max_adapter > self.THRESHOLDS['max_adapter_content']:
                self.issues.append(
                    f"High adapter content: {max_adapter:.1f}% (threshold: {self.THRESHOLDS['max_adapter_content']}%)"
                )


def analyze_all_samples(fastqc_dir, output_json, verbose=False):
    """Analyze all FastQC reports in directory"""
    fastqc_path = Path(fastqc_dir)
    results = []
    
    # Find all fastqc_data.txt files
    data_files = list(fastqc_path.rglob('fastqc_data.txt'))
    
    if not data_files:
        print(f"Warning: No fastqc_data.txt files found in {fastqc_dir}", file=sys.stderr)
        return None
    
    print(f"Found {len(data_files)} FastQC reports to analyze...")
    
    for data_file in data_files:
        try:
            checker = ATACseqQCChecker(data_file)
            result = checker.check_quality()
            results.append(result)
            
            if verbose:
                status_icon = "✅" if result['status'] == 'PASS' else "❌"
                print(f"{status_icon} {result['sample']}: {result['status']}")
                
        except Exception as e:
            print(f"Error processing {data_file}: {e}", file=sys.stderr)
    
    # Generate summary
    summary = {
        'total_samples': len(results),
        'passed': sum(1 for r in results if r['status'] == 'PASS'),
        'failed': sum(1 for r in results if r['status'] == 'FAIL'),
        'requires_review': [r for r in results if r['requires_review']],
        'all_results': results
    }
    
    # Save to JSON
    with open(output_json, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary to console
    print(f"\n{'='*70}")
    print(f"ATAC-seq QC Summary")
    print(f"{'='*70}")
    print(f"Total samples analyzed: {summary['total_samples']}")
    print(f"✅ Passed: {summary['passed']} ({summary['passed']/summary['total_samples']*100:.1f}%)")
    print(f"❌ Failed: {summary['failed']} ({summary['failed']/summary['total_samples']*100:.1f}%)")
    
    if summary['requires_review']:
        print(f"\n{'='*70}")
        print(f"⚠️  {len(summary['requires_review'])} samples require review:")
        print(f"{'='*70}")
        
        for result in summary['requires_review']:
            print(f"\n📋 Sample: {result['sample']}")
            print(f"   Status: {result['status']}")
            
            if result['issues']:
                print(f"   🔴 Critical issues:")
                for issue in result['issues']:
                    print(f"      • {issue}")
            
            if result['warnings']:
                print(f"   ⚠️  Warnings:")
                for warning in result['warnings']:
                    print(f"      • {warning}")
    else:
        print(f"\n✅ All samples passed QC! No review needed.")
    
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_json}")
    print(f"{'='*70}\n")
    
    return summary


def main():
    parser = argparse.ArgumentParser(
        description='Analyze FastQC reports for ATAC-seq specific quality metrics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all FastQC reports in a directory
  %(prog)s /path/to/fastqc_results qc_summary.json

  # With verbose output
  %(prog)s -v /path/to/fastqc_results qc_summary.json
        """
    )
    
    parser.add_argument('fastqc_dir', help='Directory containing FastQC results')
    parser.add_argument('output_json', help='Output JSON file for summary')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not Path(args.fastqc_dir).exists():
        print(f"Error: Directory not found: {args.fastqc_dir}", file=sys.stderr)
        sys.exit(1)
    
    summary = analyze_all_samples(args.fastqc_dir, args.output_json, args.verbose)
    
    # Exit with non-zero code if any samples failed
    if summary and summary['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
