#!/usr/bin/env python3
"""
ATAC-seq Pipeline Comprehensive QC Report Generator
전체 파이프라인 결과를 종합하여 HTML 리포트 생성
"""

import os
import sys
import glob
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def compute_pca(sample_data, samples):
    """
    QC 수치들로 PCA 계산.
    Returns: {
      'pca_points': [{'sample': ..., 'pc1': ..., 'pc2': ..., 'condition': ..., 'outlier': bool}],
      'variance_explained': [pc1_var%, pc2_var%],
      'features': [...],
      'loadings': {'pc1': [...], 'pc2': [...]},
      'error': None or str
    }
    """
    if not HAS_NUMPY:
        return {'error': 'numpy not available'}

    feature_names = [
        'TSS Enrichment', 'FRiP (%)',
        'Total Reads (M)', 'Peak Count (k)', 'Avg Peak Length',
        'Mapped (%)', 'Properly Paired (%)',
    ]

    rows = []
    valid_samples = []
    for s in samples:
        ataqv = sample_data[s].get('ataqv') or {}
        frip_d = sample_data[s].get('frip') or {}
        macs2  = sample_data[s].get('macs2_peaks') or {}
        flagst = sample_data[s].get('bwa_flagstat') or {}

        tss      = ataqv.get('tss_enrichment', None)
        frip     = frip_d.get('frip', None)
        peaks    = macs2.get('num_peaks', None)
        avg_len  = macs2.get('avg_peak_length', None)
        total    = flagst.get('total', None)
        mapped   = flagst.get('mapped_pct', None)
        paired   = flagst.get('properly_paired_pct', None)

        vals = [tss, frip,
                total / 1e6 if total else None,
                peaks / 1e3 if peaks else None,
                avg_len,
                mapped, paired]

        # 하나라도 None이면 제외
        if any(v is None for v in vals):
            continue
        rows.append(vals)
        valid_samples.append(s)

    if len(valid_samples) < 3:
        return {'error': f'Not enough samples with complete data ({len(valid_samples)}/3 minimum)'}

    X = np.array(rows, dtype=float)

    # Z-score 표준화
    mean = X.mean(axis=0)
    std  = X.std(axis=0)
    std[std == 0] = 1.0
    Xz = (X - mean) / std

    # SVD로 PCA
    U, S, Vt = np.linalg.svd(Xz, full_matrices=False)
    var_total = (S ** 2).sum()
    var_exp   = [(float(s**2 / var_total) * 100) for s in S]

    scores = Xz @ Vt.T   # shape (n_samples, n_components)
    pc1 = scores[:, 0].tolist()
    pc2 = scores[:, 1].tolist()

    # 이상치 감지: PC1-PC2 공간에서 Mahalanobis-like distance (z-score of distance from centroid)
    coords = np.column_stack([pc1, pc2])
    centroid = coords.mean(axis=0)
    dists = np.linalg.norm(coords - centroid, axis=1)
    dist_mean = dists.mean()
    dist_std  = dists.std() if dists.std() > 0 else 1.0
    z_dists   = (dists - dist_mean) / dist_std
    outlier_threshold = 2.0  # z > 2 → 이상치

    # condition 추출 (trailing _REP\d+ 제거)
    import re as _re
    points = []
    for i, s in enumerate(valid_samples):
        cond = _re.sub(r'_REP\d+$', '', s)
        points.append({
            'sample':    s,
            'condition': cond,
            'pc1':       round(pc1[i], 4),
            'pc2':       round(pc2[i], 4),
            'outlier':   bool(z_dists[i] > outlier_threshold),
            'z_dist':    round(float(z_dists[i]), 2),
        })

    loadings = {
        'pc1': [round(float(v), 4) for v in Vt[0]],
        'pc2': [round(float(v), 4) for v in Vt[1]],
    }

    return {
        'pca_points':        points,
        'variance_explained': [round(var_exp[0], 1), round(var_exp[1], 1)],
        'features':          feature_names,
        'loadings':          loadings,
        'error':             None,
    }


def get_sample_names(results_dir):
    """결과 디렉터리에서 샘플 이름 추출"""
    samples = set()
    
    # trimgalore 결과에서 샘플 추출
    fastqc_dir = os.path.join(results_dir, 'fastqc')
    if os.path.exists(fastqc_dir):
        for f in glob.glob(os.path.join(fastqc_dir, '*_fastqc.zip')):
            basename = os.path.basename(f)
            # SAMPLE_R1_fastqc.zip or SAMPLE_1_val_1_fastqc.zip
            sample = basename.split('_')[0]
            samples.add(sample)
    
    # BWA 결과에서도 확인
    bwa_dir = os.path.join(results_dir, 'bwa', 'merged_library')
    if os.path.exists(bwa_dir):
        for bam in glob.glob(os.path.join(bwa_dir, '*.mLb.clN.sorted.bam')):
            basename = os.path.basename(bam)
            sample = basename.replace('.mLb.clN.sorted.bam', '')
            samples.add(sample)
    
    return sorted(samples)

def parse_trimgalore_log(results_dir, sample):
    """TrimGalore 로그 파싱 - 샘플의 모든 리드를 합산"""
    # TrimGalore 로그는 trimgalore/logs 폴더에 있음
    log_dir = os.path.join(results_dir, 'trimgalore', 'logs')
    
    if not os.path.exists(log_dir):
        return None
    
    # 샘플에 해당하는 모든 trimming report 파일 찾기
    log_files = glob.glob(os.path.join(log_dir, f'{sample}_*.fastq.gz_trimming_report.txt'))
    
    if not log_files:
        return None
    
    total_reads = 0
    total_with_adapters = 0
    total_passed = 0
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                
                # Total reads processed
                m = re.search(r'Total reads processed:\s+([\d,]+)', content)
                if m:
                    total_reads += int(m.group(1).replace(',', ''))
                
                # Reads with adapters
                m = re.search(r'Reads with adapters:\s+([\d,]+)', content)
                if m:
                    total_with_adapters += int(m.group(1).replace(',', ''))
                
                # Reads written (passing filters)
                m = re.search(r'Reads written \(passing filters\):\s+([\d,]+)', content)
                if m:
                    total_passed += int(m.group(1).replace(',', ''))
        except Exception as e:
            print(f"Error parsing TrimGalore log {log_file}: {e}")
            continue
    
    if total_reads > 0:
        return {
            'total_reads': total_reads,
            'with_adapters': total_with_adapters,
            'passed': total_passed,
            'adapter_rate': round(total_with_adapters / total_reads * 100, 2) if total_reads > 0 else 0
        }
    
    return None

def parse_bwa_flagstat(results_dir, sample):
    """BWA alignment flagstat 파싱"""
    flagstat_file = os.path.join(results_dir, 'bwa', 'merged_library', 'samtools_stats', f'{sample}.mLb.clN.sorted.bam.flagstat')
    
    if not os.path.exists(flagstat_file):
        return None
    
    data = {}
    try:
        with open(flagstat_file, 'r') as f:
            lines = f.readlines()
            
            # Total reads (QC-passed reads + QC-failed reads)
            m = re.search(r'(\d+) \+ \d+ in total', lines[0])
            if m:
                data['total'] = int(m.group(1))
            
            # Duplicates
            for line in lines:
                if 'duplicates' in line:
                    m = re.search(r'(\d+) \+ \d+ duplicates', line)
                    if m:
                        data['duplicates'] = int(m.group(1))
                
                # Mapped
                if 'mapped (' in line and 'primary' not in line:
                    m = re.search(r'(\d+) \+ \d+ mapped \(([\d.]+)%', line)
                    if m:
                        data['mapped'] = int(m.group(1))
                        data['mapped_pct'] = float(m.group(2))
                
                # Properly paired
                if 'properly paired' in line:
                    m = re.search(r'(\d+) \+ \d+ properly paired \(([\d.]+)%', line)
                    if m:
                        data['properly_paired'] = int(m.group(1))
                        data['properly_paired_pct'] = float(m.group(2))
    except:
        pass
    
    return data

def parse_picard_metrics(results_dir, sample):
    """Picard MarkDuplicates metrics 파싱"""
    metrics_file = os.path.join(results_dir, 'bwa', 'merged_library', 'picard_metrics', f'{sample}.mLb.mkD.sorted.MarkDuplicates.metrics.txt')
    
    if not os.path.exists(metrics_file):
        return None
    
    data = {}
    try:
        with open(metrics_file, 'r') as f:
            lines = f.readlines()
            
            # Find metrics section
            for i, line in enumerate(lines):
                if line.startswith('LIBRARY'):
                    # Next line has the data
                    if i + 1 < len(lines):
                        parts = lines[i + 1].strip().split('\t')
                        if len(parts) >= 9:
                            data['unpaired_examined'] = int(parts[1]) if parts[1] else 0
                            data['read_pairs_examined'] = int(parts[2]) if parts[2] else 0
                            data['unmapped'] = int(parts[3]) if parts[3] else 0
                            data['unpaired_duplicates'] = int(parts[4]) if parts[4] else 0
                            data['read_pair_duplicates'] = int(parts[5]) if parts[5] else 0
                            data['read_pair_optical_duplicates'] = int(parts[6]) if parts[6] else 0
                            data['percent_duplication'] = float(parts[7]) if parts[7] else 0
                            data['estimated_library_size'] = int(parts[8]) if parts[8] else 0
                    break
    except:
        pass
    
    return data

def parse_macs2_peaks(results_dir, sample):
    """MACS2 peak calling 결과 파싱"""
    # narrowPeak or broadPeak 파일
    peak_patterns = [
        os.path.join(results_dir, 'bwa', 'merged_library', 'macs2', 'broad_peak', f'{sample}*_peaks.broadPeak'),
        os.path.join(results_dir, 'bwa', 'merged_library', 'macs2', 'narrow_peak', f'{sample}*_peaks.narrowPeak'),
    ]
    
    data = {}
    for pattern in peak_patterns:
        peak_files = glob.glob(pattern)
        if peak_files:
            peak_file = peak_files[0]
            try:
                with open(peak_file, 'r') as f:
                    peaks = f.readlines()
                    data['num_peaks'] = len(peaks)
                    
                    # Peak 길이 통계
                    lengths = []
                    scores = []
                    for line in peaks:
                        parts = line.strip().split('\t')
                        if len(parts) >= 5:
                            start = int(parts[1])
                            end = int(parts[2])
                            lengths.append(end - start)
                            
                            # Score
                            if len(parts) >= 7:
                                try:
                                    scores.append(float(parts[6]))
                                except:
                                    pass
                    
                    if lengths:
                        data['avg_peak_length'] = sum(lengths) / len(lengths)
                        data['median_peak_length'] = sorted(lengths)[len(lengths) // 2]
                        data['min_peak_length'] = min(lengths)
                        data['max_peak_length'] = max(lengths)
                    
                    if scores:
                        data['avg_peak_score'] = sum(scores) / len(scores)
                
                break
            except:
                pass
    
    return data if data else None

def parse_frip_score(results_dir, sample):
    """FRiP score 파싱 (Fraction of Reads in Peaks)"""
    # FRiP score는 MACS2 peak QC 파일에 있음
    frip_file = os.path.join(results_dir, 'bwa', 'merged_library', 'macs2', 'broad_peak', 'qc', f'{sample}.mLb.clN_peaks.FRiP_mqc.tsv')
    
    if not os.path.exists(frip_file):
        return None
    
    try:
        with open(frip_file, 'r') as f:
            lines = f.readlines()
            # 마지막 줄에 "SAMPLE_NAME value" 형식으로 FRiP score가 있음
            for line in reversed(lines):
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) == 2:
                        try:
                            frip = float(parts[1])
                            return {'frip': frip * 100}  # 백분율로 변환
                        except ValueError:
                            pass
    except Exception as e:
        print(f"Error parsing FRiP score for {sample}: {e}")
        pass
    
    return None

def parse_fragment_size(results_dir, sample):
    """Fragment size distribution 파싱"""
    # Picard CollectInsertSizeMetrics 결과
    insert_file = os.path.join(results_dir, 'bwa', 'merged_library', 'picard_metrics', f'{sample}.mLb.clN.CollectMultipleMetrics.insert_size_metrics')
    
    if not os.path.exists(insert_file):
        return None
    
    data = {}
    try:
        with open(insert_file, 'r') as f:
            lines = f.readlines()
            
            for i, line in enumerate(lines):
                if line.startswith('MEDIAN_INSERT_SIZE'):
                    if i + 1 < len(lines):
                        parts = lines[i + 1].strip().split('\t')
                        if len(parts) >= 5:
                            data['median'] = float(parts[0]) if parts[0] else 0
                            data['mode'] = float(parts[1]) if parts[1] else 0
                            data['median_absolute_deviation'] = float(parts[2]) if parts[2] else 0
                            data['min'] = float(parts[3]) if parts[3] else 0
                            data['max'] = float(parts[4]) if parts[4] else 0
                    break
    except:
        pass
    
    return data

def parse_ataqv_metrics(results_dir, sample):
    """ATAQv JSON 파일에서 ATAC-seq 특화 메트릭 파싱"""
    ataqv_file = os.path.join(results_dir, 'bwa', 'merged_library', 'ataqv', 'broad_peak', f'{sample}.ataqv.json')
    
    if not os.path.exists(ataqv_file):
        return None
    
    data = {}
    try:
        with open(ataqv_file, 'r') as f:
            json_data = json.load(f)
        
        # ATAQv JSON is a list with one element
        if isinstance(json_data, list) and len(json_data) > 0:
            json_data = json_data[0]
        
        metrics = json_data.get('metrics', {})
        
        # TSS enrichment
        if 'tss_enrichment' in metrics:
            data['tss_enrichment'] = round(metrics['tss_enrichment'], 2)
        
        # Mitochondrial reads
        if 'mitochondrial_reads' in metrics and 'total_reads' in metrics:
            total = metrics['total_reads']
            if total > 0:
                mt_rate = (metrics['mitochondrial_reads'] / total) * 100
                data['mitochondrial_rate'] = round(mt_rate, 2)
        
        # FRiP score (high-quality autosomal alignments in peaks)
        if 'hqaa_in_peaks' in metrics and 'hqaa' in metrics:
            hqaa_total = metrics['hqaa']
            if hqaa_total > 0:
                frip = (metrics['hqaa_in_peaks'] / hqaa_total) * 100
                data['frip'] = round(frip, 2)
        
        # Fragment length distribution
        if 'fragment_length_counts' in metrics:
            frag_dist = metrics['fragment_length_counts']
            if isinstance(frag_dist, dict):
                # NFR: nucleosome-free region (38-100bp)
                nfr = sum(frag_dist.get(str(i), 0) for i in range(38, 101))
                # Mono-nucleosome: ~180-247bp
                mono = sum(frag_dist.get(str(i), 0) for i in range(180, 248))
                # Di-nucleosome: ~315-472bp
                di = sum(frag_dist.get(str(i), 0) for i in range(315, 473))
                
                total_frags = nfr + mono + di
                if total_frags > 0:
                    data['nfr_percent'] = round((nfr / total_frags) * 100, 2)
                    data['mono_nuc_percent'] = round((mono / total_frags) * 100, 2)
                    data['di_nuc_percent'] = round((di / total_frags) * 100, 2)
        
        # Total reads
        if 'total_reads' in metrics:
            data['total_reads'] = metrics['total_reads']
        
    except Exception as e:
        print(f"Warning: Could not parse ATAQv JSON for {sample}: {e}")
    
    return data if data else None

def get_file_size(filepath):
    """파일 크기를 읽기 쉬운 형식으로 변환"""
    if not os.path.exists(filepath):
        return "N/A"
    size = os.path.getsize(filepath)
    if size > 1e9:
        return f"{size/1e9:.2f} GB"
    elif size > 1e6:
        return f"{size/1e6:.2f} MB"
    else:
        return f"{size/1e3:.2f} KB"

def generate_html_report(results_dir, output_file):
    """HTML 종합 리포트 생성"""
    
    samples = get_sample_names(results_dir)
    
    if not samples:
        print("⚠️  No samples found in results directory")
        return
    
    print(f"Found {len(samples)} samples: {', '.join(samples)}")
    
    # 각 샘플별 데이터 수집
    sample_data = {}
    for sample in samples:
        sample_data[sample] = {
            'trimgalore': parse_trimgalore_log(results_dir, sample),
            'bwa_flagstat': parse_bwa_flagstat(results_dir, sample),
            'picard_metrics': parse_picard_metrics(results_dir, sample),
            'macs2_peaks': parse_macs2_peaks(results_dir, sample),
            'frip': parse_frip_score(results_dir, sample),
            'fragment_size': parse_fragment_size(results_dir, sample),
            'ataqv': parse_ataqv_metrics(results_dir, sample),
        }
    
    # HTML 생성
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATAC-seq Pipeline QC Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .summary-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .summary-card h3 {{
            color: #667eea;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        
        .summary-card .sub-value {{
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        
        tr:hover {{
            background-color: #f8f9ff;
        }}
        
        .metric-good {{
            color: #10b981;
            font-weight: bold;
        }}
        
        .metric-warning {{
            color: #f59e0b;
            font-weight: bold;
        }}
        
        .metric-bad {{
            color: #ef4444;
            font-weight: bold;
        }}
        
        .progress-bar {{
            height: 25px;
            background: #e5e7eb;
            border-radius: 12px;
            overflow: hidden;
            margin: 5px 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.85em;
            font-weight: bold;
            transition: width 0.3s ease;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .badge-success {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .badge-warning {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .badge-info {{
            background: #dbeafe;
            color: #1e40af;
        }}
        
        .footer {{
            background: #f9fafb;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}

        .pca-grid {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }}
        .pca-canvas-wrap {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        .pca-legend {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
            overflow-y: auto;
            max-height: 480px;
        }}
        .pca-legend h4 {{
            margin-bottom: 12px;
            color: #4c1d95;
            font-size: 0.95em;
        }}
        .pca-legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            font-size: 0.85em;
        }}
        .pca-dot {{
            width: 12px; height: 12px;
            border-radius: 50%;
            flex-shrink: 0;
        }}
        .outlier-tag {{
            background: #fee2e2;
            color: #991b1b;
            border-radius: 4px;
            padding: 1px 6px;
            font-size: 0.78em;
            font-weight: bold;
        }}
        .loading-table {{
            width: 100%;
            font-size: 0.83em;
            margin-top: 15px;
            border-collapse: collapse;
        }}
        .loading-table th, .loading-table td {{
            padding: 4px 8px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }}
        .loading-table th {{
            background: #f3f4f6;
            font-weight: 600;
        }}
        .loading-bar {{
            display: inline-block;
            height: 10px;
            border-radius: 3px;
            vertical-align: middle;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧬 ATAC-seq Pipeline QC Report</h1>
            <p>Comprehensive Quality Control & Analysis Summary</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="content">
            <!-- Overall Summary -->
            <div class="section">
                <h2 class="section-title">📊 Overall Summary</h2>
                <div class="summary-grid">
                    <div class="summary-card">
                        <h3>Total Samples</h3>
                        <div class="value">{len(samples)}</div>
                        <div class="sub-value">{', '.join(samples[:3])}{'...' if len(samples) > 3 else ''}</div>
                    </div>
"""
    
    # Calculate overall statistics
    total_peaks = sum(sample_data[s]['macs2_peaks']['num_peaks'] 
                     for s in samples 
                     if sample_data[s]['macs2_peaks'] and 'num_peaks' in sample_data[s]['macs2_peaks'])
    
    avg_frip = 0
    frip_count = 0
    for s in samples:
        if sample_data[s]['frip'] and 'frip' in sample_data[s]['frip']:
            avg_frip += sample_data[s]['frip']['frip']
            frip_count += 1
    avg_frip = (avg_frip / frip_count) if frip_count > 0 else 0  # 이미 백분율임
    
    html += f"""
                    <div class="summary-card">
                        <h3>Total Peaks</h3>
                        <div class="value">{total_peaks:,}</div>
                        <div class="sub-value">All samples combined</div>
                    </div>
                    <div class="summary-card">
                        <h3>Avg FRiP Score</h3>
                        <div class="value">{avg_frip:.1f}%</div>
                        <div class="sub-value">{'Good' if avg_frip > 20 else 'Check samples'}</div>
                    </div>
                </div>
            </div>
            
            <!-- TrimGalore Results -->
            <div class="section">
                <h2 class="section-title">✂️ Adapter Trimming (TrimGalore)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Sample</th>
                            <th>Total Reads</th>
                            <th>With Adapters</th>
                            <th>Passed</th>
                            <th>Pass Rate</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    for sample in samples:
        tg_data = sample_data[sample]['trimgalore']
        if tg_data:
            total = tg_data.get('total_reads', 0)
            adapters = tg_data.get('with_adapters', 0)
            passed = tg_data.get('passed', 0)
            pass_rate = (passed / total * 100) if total > 0 else 0
            color_class = 'metric-good' if pass_rate > 95 else 'metric-warning'
            
            html += f"""
                        <tr>
                            <td><strong>{sample}</strong></td>
                            <td>{total:,}</td>
                            <td>{adapters:,}</td>
                            <td>{passed:,}</td>
                            <td>
                                <span class="{color_class}">{pass_rate:.1f}%</span>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {pass_rate}%">{pass_rate:.1f}%</div>
                                </div>
                            </td>
                        </tr>
"""
        else:
            html += f"""
                        <tr>
                            <td><strong>{sample}</strong></td>
                            <td colspan="4">No data available</td>
                        </tr>
"""
    
    html += """
                    </tbody>
                </table>
            </div>
            
            <!-- BWA Alignment Results -->
            <div class="section">
                <h2 class="section-title">🎯 Alignment (BWA)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Sample</th>
                            <th>Total Reads</th>
                            <th>Mapped</th>
                            <th>Properly Paired</th>
                            <th>Duplicates</th>
                            <th>Quality</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    for sample in samples:
        bwa_data = sample_data[sample]['bwa_flagstat']
        if bwa_data:
            total = bwa_data.get('total', 0)
            mapped = bwa_data.get('mapped', 0)
            mapped_pct = bwa_data.get('mapped_pct', 0)
            paired = bwa_data.get('properly_paired', 0)
            paired_pct = bwa_data.get('properly_paired_pct', 0)
            dups = bwa_data.get('duplicates', 0)
            dup_pct = (dups / total * 100) if total > 0 else 0
            
            # Quality badge
            if mapped_pct > 90:
                badge = '<span class="badge badge-success">Excellent</span>'
            elif mapped_pct > 80:
                badge = '<span class="badge badge-info">Good</span>'
            else:
                badge = '<span class="badge badge-warning">Check</span>'
            
            html += f"""
                        <tr>
                            <td><strong>{sample}</strong></td>
                            <td>{total:,}</td>
                            <td class="metric-good">{mapped:,} ({mapped_pct:.1f}%)</td>
                            <td>{paired:,} ({paired_pct:.1f}%)</td>
                            <td>{dups:,} ({dup_pct:.1f}%)</td>
                            <td>{badge}</td>
                        </tr>
"""
        else:
            html += f"""
                        <tr>
                            <td><strong>{sample}</strong></td>
                            <td colspan="5">No data available</td>
                        </tr>
"""
    
    html += """
                    </tbody>
                </table>
            </div>
            
            <!-- Peak Calling Results -->
            <div class="section">
                <h2 class="section-title">🏔️ Peak Calling (MACS2)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Sample</th>
                            <th>Number of Peaks</th>
                            <th>Avg Peak Length</th>
                            <th>Peak Length Range</th>
                            <th>FRiP Score</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    for sample in samples:
        peak_data = sample_data[sample]['macs2_peaks']
        frip_data = sample_data[sample]['frip']
        
        if peak_data:
            num_peaks = peak_data.get('num_peaks', 0)
            avg_length = peak_data.get('avg_peak_length', 0)
            min_length = peak_data.get('min_peak_length', 0)
            max_length = peak_data.get('max_peak_length', 0)
            
            # FRiP score는 이미 백분율로 변환됨
            frip = frip_data.get('frip', 0) if frip_data else 0
            frip_class = 'metric-good' if frip > 20 else 'metric-warning' if frip > 10 else 'metric-bad'
            
            html += f"""
                        <tr>
                            <td><strong>{sample}</strong></td>
                            <td class="metric-good">{num_peaks:,}</td>
                            <td>{avg_length:.0f} bp</td>
                            <td>{min_length:.0f} - {max_length:.0f} bp</td>
                            <td class="{frip_class}">{frip:.2f}%</td>
                        </tr>
"""
        else:
            html += f"""
                        <tr>
                            <td><strong>{sample}</strong></td>
                            <td colspan="4">No data available</td>
                        </tr>
"""
    
    html += """
                    </tbody>
                </table>
                <div style="margin-top: 15px; padding: 15px; background: #f0f9ff; border-left: 4px solid #667eea; border-radius: 4px;">
                    <strong>FRiP Score Guide:</strong> 
                    <span class="metric-good">Good: >20%</span> | 
                    <span class="metric-warning">Acceptable: 10-20%</span> | 
                    <span class="metric-bad">Poor: <10%</span>
                </div>
            </div>
            
            <!-- Fragment Size Distribution -->
            <div class="section">
                <h2 class="section-title">📏 Fragment Size Distribution</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Sample</th>
                            <th>Median Insert Size</th>
                            <th>Mode Insert Size</th>
                            <th>Range</th>
                            <th>Nucleosome Pattern</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    for sample in samples:
        frag_data = sample_data[sample]['fragment_size']
        
        if frag_data:
            median = frag_data.get('median', 0)
            mode = frag_data.get('mode', 0)
            min_size = frag_data.get('min', 0)
            max_size = frag_data.get('max', 0)
            
            # ATAC-seq에서 nucleosome pattern 평가
            if median < 150:
                pattern = '<span class="badge badge-success">Strong NFR</span>'
            elif median < 250:
                pattern = '<span class="badge badge-info">Mixed</span>'
            else:
                pattern = '<span class="badge badge-warning">Nucleosome-rich</span>'
            
            html += f"""
                        <tr>
                            <td><strong>{sample}</strong></td>
                            <td>{median:.0f} bp</td>
                            <td>{mode:.0f} bp</td>
                            <td>{min_size:.0f} - {max_size:.0f} bp</td>
                            <td>{pattern}</td>
                        </tr>
"""
        else:
            html += f"""
                        <tr>
                            <td><strong>{sample}</strong></td>
                            <td colspan="4">No data available</td>
                        </tr>
"""
    
    html += """
                    </tbody>
                </table>
                <div style="margin-top: 15px; padding: 15px; background: #f0f9ff; border-left: 4px solid #667eea; border-radius: 4px;">
                    <strong>Expected ATAC-seq pattern:</strong> Bimodal distribution with peaks at ~50bp (nucleosome-free) and ~200bp (mono-nucleosome)
                </div>
            </div>
            
            <!-- ATAC-seq Specific Metrics (ATAQv) -->
            <div class="section">
                <h2 class="section-title">🧬 ATAC-seq Specific QC (ATAQv)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Sample</th>
                            <th>TSS Enrichment</th>
                            <th>Mitochondrial %</th>
                            <th>FRiP Score</th>
                            <th>NFR %</th>
                            <th>Mono-Nuc %</th>
                            <th>Di-Nuc %</th>
                            <th>Overall Status</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    # Replicate outlier detection: compute per-condition FRiP averages
    import re as _re
    condition_frip = {}
    for s in samples:
        ad = sample_data[s]['ataqv']
        if not ad:
            continue
        frip_val = ad.get('frip', 0)
        # condition = sample name without trailing _REP\d+
        cond = _re.sub(r'_REP\d+$', '', s)
        condition_frip.setdefault(cond, []).append(frip_val)
    condition_frip_avg = {c: sum(v)/len(v) for c, v in condition_frip.items() if v}

    for sample in samples:
        ataqv_data = sample_data[sample]['ataqv']
        
        if ataqv_data:
            tss = ataqv_data.get('tss_enrichment', 0)
            mt_rate = ataqv_data.get('mitochondrial_rate', 0)
            frip = ataqv_data.get('frip', 0)
            nfr = ataqv_data.get('nfr_percent', 0)
            mono = ataqv_data.get('mono_nuc_percent', 0)
            di = ataqv_data.get('di_nuc_percent', 0)
            
            # Color coding based on ATAC-seq thresholds
            tss_class = 'metric-good' if tss >= 5 else 'metric-warning' if tss >= 3 else 'metric-bad'
            mt_class = 'metric-good' if mt_rate < 20 else 'metric-warning' if mt_rate < 30 else 'metric-bad'
            frip_class = 'metric-good' if frip >= 10 else 'metric-warning' if frip >= 5 else 'metric-bad'
            
            # Overall status: absolute thresholds
            issues = 0
            warnings = 0
            issue_notes = []
            if tss < 3:
                issues += 1
                issue_notes.append(f'TSS {tss:.2f}x < 3x')
            elif tss < 5:
                warnings += 1
                issue_notes.append(f'TSS {tss:.2f}x < 5x')
            if mt_rate > 30:
                issues += 1
                issue_notes.append(f'MT {mt_rate:.1f}% > 30%')
            elif mt_rate > 20:
                warnings += 1
                issue_notes.append(f'MT {mt_rate:.1f}% > 20%')
            if frip < 5:
                issues += 1
                issue_notes.append(f'FRiP {frip:.1f}% < 5%')
            elif frip < 10:
                warnings += 1
                issue_notes.append(f'FRiP {frip:.1f}% < 10%')

            # Replicate outlier check: FRiP < 50% of condition average
            cond = _re.sub(r'_REP\d+$', '', sample)
            cond_avg = condition_frip_avg.get(cond, 0)
            if cond_avg > 0 and frip < cond_avg * 0.5:
                warnings += 1
                issue_notes.append(f'FRiP outlier: {frip:.1f}% vs condition avg {cond_avg:.1f}%')
                frip_class = 'metric-warning'  # 절대값 통과해도 색 변경

            tooltip = '; '.join(issue_notes) if issue_notes else 'All checks passed'
            if issues >= 1:
                status_badge = f'<span class="badge badge-danger" title="{tooltip}">✗ FAIL</span>'
            elif warnings >= 1:
                status_badge = f'<span class="badge badge-warning" title="{tooltip}">⚠ WARN</span>'
            else:
                status_badge = f'<span class="badge badge-success" title="{tooltip}">✓ PASS</span>'
            
            html += f"""
                        <tr>
                            <td><strong>{sample}</strong></td>
                            <td class="{tss_class}">{tss:.2f}x</td>
                            <td class="{mt_class}">{mt_rate:.2f}%</td>
                            <td class="{frip_class}">{frip:.2f}%</td>
                            <td>{nfr:.1f}%</td>
                            <td>{mono:.1f}%</td>
                            <td>{di:.1f}%</td>
                            <td>{status_badge}</td>
                        </tr>
"""
        else:
            html += f"""
                        <tr>
                            <td><strong>{sample}</strong></td>
                            <td colspan="7">ATAQv data not available</td>
                        </tr>
"""
    
    html += """
                    </tbody>
                </table>
                <div style="margin-top: 15px; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                    <strong>⚙️ ATAC-seq QC Thresholds (Optimized):</strong><br>
                    <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
                        <li><strong>TSS Enrichment:</strong> <span class="metric-good">Good: ≥5x</span>, <span class="metric-warning">Acceptable: 3-5x</span>, <span class="metric-bad">Poor: <3x</span></li>
                        <li><strong>Mitochondrial Reads:</strong> <span class="metric-good">Good: <20%</span>, <span class="metric-warning">Acceptable: 20-30%</span>, <span class="metric-bad">High: >30%</span></li>
                        <li><strong>FRiP Score:</strong> <span class="metric-good">Good: ≥10%</span>, <span class="metric-warning">Acceptable: 5-10%</span>, <span class="metric-bad">Poor: <5%</span> — WARN if &lt;10%, FAIL if &lt;5%</li>
                        <li><strong>Replicate Outlier:</strong> WARN if FRiP &lt;50% of condition average (hover Overall Status for details)</li>
                        <li><strong>Note:</strong> High duplication (up to 50%) is normal in ATAC-seq due to open chromatin regions</li>
                    </ul>
                </div>
            </div>

            <!-- PCA Outlier Detection -->
"""

    # ── PCA 계산 ────────────────────────────────────────────
    pca = compute_pca(sample_data, samples)

    if pca.get('error'):
        html += f"""
            <div class="section">
                <h2 class="section-title">🔬 QC PCA &amp; Outlier Detection</h2>
                <p style="color:#888;padding:20px;">PCA를 계산할 수 없습니다: {pca['error']}</p>
            </div>
"""
    else:
        # 조건별 색상 팔레트
        conditions = sorted(set(p['condition'] for p in pca['pca_points']))
        palette = ['#6366f1','#f59e0b','#10b981','#ef4444','#3b82f6',
                   '#8b5cf6','#ec4899','#14b8a6','#f97316','#84cc16']
        cond_color = {c: palette[i % len(palette)] for i, c in enumerate(conditions)}

        # Chart.js 데이터셋 — Python dict로 만들어서 json.dumps로 직렬화
        datasets = []
        for cond in conditions:
            pts = [p for p in pca['pca_points'] if p['condition'] == cond]
            color = cond_color[cond]
            datasets.append({
                'label': cond,
                'data': [
                    {'x': p['pc1'], 'y': p['pc2'],
                     'sample': p['sample'],
                     'outlier': p['outlier'],
                     'z_dist': p['z_dist']}
                    for p in pts
                ],
                'backgroundColor': [
                    'rgba(239,68,68,0.85)' if p['outlier'] else color + 'cc'
                    for p in pts
                ],
                'borderColor': [
                    '#991b1b' if p['outlier'] else color
                    for p in pts
                ],
                'pointRadius': [10 if p['outlier'] else 7 for p in pts],
                'pointStyle': ['triangle' if p['outlier'] else 'circle' for p in pts],
                'borderWidth': 2,
            })

        pca_json      = json.dumps(pca['pca_points'])
        datasets_json = json.dumps(datasets)
        features_json = json.dumps(pca['features'])
        loadings_json = json.dumps(pca['loadings'])
        var1, var2    = pca['variance_explained']

        # Legend HTML
        legend_html = ''
        for p in pca['pca_points']:
            color = cond_color[p['condition']]
            dot_color = '#ef4444' if p['outlier'] else color
            outlier_tag = '<span class="outlier-tag">⚠ OUTLIER</span>' if p['outlier'] else ''
            legend_html += f"""
                    <div class="pca-legend-item">
                        <div class="pca-dot" style="background:{dot_color}"></div>
                        <span>{p['sample']}</span>
                        {outlier_tag}
                        <span style="color:#888;font-size:0.78em;">(z={p['z_dist']})</span>
                    </div>"""

        # Loading bar HTML
        loading_rows = ''
        for i, feat in enumerate(pca['features']):
            l1 = pca['loadings']['pc1'][i]
            l2 = pca['loadings']['pc2'][i]
            bar1_w = int(abs(l1) * 80)
            bar2_w = int(abs(l2) * 80)
            bar1_c = '#6366f1' if l1 >= 0 else '#ef4444'
            bar2_c = '#f59e0b' if l2 >= 0 else '#10b981'
            loading_rows += f"""
                        <tr>
                            <td>{feat}</td>
                            <td><span class="loading-bar" style="width:{bar1_w}px;background:{bar1_c}"></span> {l1:+.3f}</td>
                            <td><span class="loading-bar" style="width:{bar2_w}px;background:{bar2_c}"></span> {l2:+.3f}</td>
                        </tr>"""

        outlier_samples = [p['sample'] for p in pca['pca_points'] if p['outlier']]
        outlier_note = ''
        if outlier_samples:
            outlier_note = f'<div style="margin-top:12px;padding:10px 15px;background:#fee2e2;border-left:4px solid #ef4444;border-radius:4px;color:#991b1b;font-size:0.9em;"><strong>⚠ 이상치 감지:</strong> {", ".join(outlier_samples)} — PC 공간에서 centroid 대비 z-score &gt; 2.0</div>'

        html += f"""
            <div class="section">
                <h2 class="section-title">🔬 QC PCA &amp; Outlier Detection</h2>
                <p style="color:#555;font-size:0.9em;margin-bottom:5px;">
                    11개 QC 지표 (TSS enrichment, FRiP, Mitochondrial %, Total reads, Peak count, Avg peak length, NFR/Mono/Di-nuc %, Mapped %, Properly paired %)를 Z-score 표준화 후 PCA.
                    <strong>▲ 삼각형 = 이상치</strong> (PC 공간 centroid로부터 z-score &gt; 2.0).
                </p>
                {outlier_note}
                <div class="pca-grid">
                    <div class="pca-canvas-wrap">
                        <canvas id="pcaChart" height="400"></canvas>
                        <p style="text-align:center;color:#888;font-size:0.82em;margin-top:8px;">
                            PC1 {var1}% | PC2 {var2}% | 총 {var1+var2}% 분산 설명
                        </p>
                    </div>
                    <div class="pca-legend">
                        <h4>샘플 목록</h4>
                        {legend_html}
                        <h4 style="margin-top:18px;">PC Loadings</h4>
                        <p style="font-size:0.78em;color:#888;margin-bottom:6px;">각 QC 지표가 PC에 기여하는 방향과 크기</p>
                        <table class="loading-table">
                            <thead><tr><th>Feature</th><th>PC1</th><th>PC2</th></tr></thead>
                            <tbody>{loading_rows}</tbody>
                        </table>
                    </div>
                </div>
            </div>
            <script>
            (function() {{
                const pcaData   = {pca_json};
                const datasets  = {datasets_json};
                const ctx = document.getElementById('pcaChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'scatter',
                    data: {{ datasets }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            legend: {{ position: 'top' }},
                            tooltip: {{
                                callbacks: {{
                                    label: function(ctx) {{
                                        const d = ctx.raw;
                                        const flag = d.outlier ? ' ⚠ OUTLIER' : '';
                                        return `${{d.sample}}  PC1=${{d.x.toFixed(2)}} PC2=${{d.y.toFixed(2)}} z=${{d.z_dist}}${{flag}}`;
                                    }}
                                }}
                            }},
                            title: {{
                                display: true,
                                text: 'QC PCA — PC1 vs PC2',
                                font: {{ size: 15 }}
                            }}
                        }},
                        scales: {{
                            x: {{ title: {{ display: true, text: 'PC1 ({var1}% variance)' }} }},
                            y: {{ title: {{ display: true, text: 'PC2 ({var2}% variance)' }} }}
                        }}
                    }}
                }});
            }})();
            </script>
"""

    html += """
            <!-- File Sizes -->
            <div class="section">
                <h2 class="section-title">💾 Output File Sizes</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Sample</th>
                            <th>BAM File</th>
                            <th>Peak File</th>
                            <th>BigWig</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    for sample in samples:
        bam_file = os.path.join(results_dir, 'bwa', 'merged_library', f'{sample}.mLb.clN.sorted.bam')
        peak_file = glob.glob(os.path.join(results_dir, 'bwa', 'merged_library', 'macs2', 'broad_peak', f'{sample}.mLb.clN_peaks.*Peak'))
        bigwig_file = os.path.join(results_dir, 'bwa', 'merged_library', 'bigwig', f'{sample}.mLb.clN.bigWig')
        
        peak_size = get_file_size(peak_file[0]) if peak_file else "N/A"
        
        html += f"""
                        <tr>
                            <td><strong>{sample}</strong></td>
                            <td>{get_file_size(bam_file)}</td>
                            <td>{peak_size}</td>
                            <td>{get_file_size(bigwig_file)}</td>
                        </tr>
"""
    
    html += f"""
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by ATAC-seq Pipeline Comprehensive QC Report Generator</p>
            <p>Pipeline Version: 1.0 | Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Comprehensive report saved: {output_file}")
    return True

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate comprehensive ATAC-seq pipeline QC report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report from results directory
  %(prog)s results pipeline_qc_report.html

  # With custom results directory
  %(prog)s /path/to/results output.html
        """
    )
    
    parser.add_argument('results_dir', help='Results directory (usually "results")')
    parser.add_argument('output_html', help='Output HTML file path')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.results_dir):
        print(f"❌ Error: Results directory not found: {args.results_dir}")
        sys.exit(1)
    
    print("🔬 ATAC-seq Pipeline Comprehensive QC Report Generator")
    print("=" * 70)
    print(f"Results directory: {args.results_dir}")
    print(f"Output file: {args.output_html}")
    print("")
    
    success = generate_html_report(args.results_dir, args.output_html)
    
    if success:
        print("\n🌐 Open the report in your browser:")
        print(f"   file://{os.path.abspath(args.output_html)}")
        sys.exit(0)
    else:
        print("\n❌ Failed to generate report")
        sys.exit(1)

if __name__ == '__main__':
    main()
