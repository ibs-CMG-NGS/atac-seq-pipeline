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
    bwa_dir = os.path.join(results_dir, 'bwa', 'mergedLibrary')
    if os.path.exists(bwa_dir):
        for bam in glob.glob(os.path.join(bwa_dir, '*.mLb.clN.sorted.bam')):
            basename = os.path.basename(bam)
            sample = basename.replace('.mLb.clN.sorted.bam', '')
            samples.add(sample)
    
    return sorted(samples)

def parse_trimgalore_log(results_dir, sample):
    """TrimGalore 로그 파싱"""
    # TrimGalore 로그는 trimgalore 폴더에 있을 수 있음
    log_patterns = [
        os.path.join(results_dir, 'trimgalore', f'{sample}*.txt'),
        os.path.join(results_dir, 'trimgalore', 'logs', f'{sample}*.log'),
    ]
    
    data = {}
    for pattern in log_patterns:
        log_files = glob.glob(pattern)
        if log_files:
            log_file = log_files[0]
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    
                    # Total reads processed
                    m = re.search(r'Total reads processed:\s+([\d,]+)', content)
                    if m:
                        data['total_reads'] = int(m.group(1).replace(',', ''))
                    
                    # Reads with adapters
                    m = re.search(r'Reads with adapters:\s+([\d,]+)', content)
                    if m:
                        data['with_adapters'] = int(m.group(1).replace(',', ''))
                    
                    # Reads written (passing filters)
                    m = re.search(r'Reads written \(passing filters\):\s+([\d,]+)', content)
                    if m:
                        data['passed'] = int(m.group(1).replace(',', ''))
                    
                    break
            except:
                pass
    
    return data if data else None

def parse_bwa_flagstat(results_dir, sample):
    """BWA alignment flagstat 파싱"""
    flagstat_file = os.path.join(results_dir, 'bwa', 'mergedLibrary', f'{sample}.mLb.clN.sorted.bam.flagstat')
    
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
    metrics_file = os.path.join(results_dir, 'bwa', 'mergedLibrary', 'picard_metrics', f'{sample}.mLb.clN.sorted.MarkDuplicates.metrics.txt')
    
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
        os.path.join(results_dir, 'bwa', 'mergedLibrary', 'macs2', f'{sample}*_peaks.narrowPeak'),
        os.path.join(results_dir, 'bwa', 'mergedLibrary', 'macs2', f'{sample}*_peaks.broadPeak'),
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
    # FRiP score는 peak QC 파일에 있을 수 있음
    frip_file = os.path.join(results_dir, 'bwa', 'mergedLibrary', 'macs2', 'qc', f'{sample}_FRiP.txt')
    
    if os.path.exists(frip_file):
        try:
            with open(frip_file, 'r') as f:
                content = f.read()
                m = re.search(r'FRiP.*?([\d.]+)', content)
                if m:
                    return {'frip': float(m.group(1))}
        except:
            pass
    
    return None

def parse_fragment_size(results_dir, sample):
    """Fragment size distribution 파싱"""
    # Picard CollectInsertSizeMetrics 결과
    insert_file = os.path.join(results_dir, 'bwa', 'mergedLibrary', 'picard_metrics', f'{sample}.mLb.clN.sorted.CollectInsertSizeMetrics.txt')
    
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
    </style>
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
    avg_frip = (avg_frip / frip_count * 100) if frip_count > 0 else 0
    
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
            
            frip = frip_data.get('frip', 0) * 100 if frip_data else 0
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
        bam_file = os.path.join(results_dir, 'bwa', 'mergedLibrary', f'{sample}.mLb.clN.sorted.bam')
        peak_file = glob.glob(os.path.join(results_dir, 'bwa', 'mergedLibrary', 'macs2', f'{sample}*_peaks.*Peak'))
        bigwig_file = os.path.join(results_dir, 'bwa', 'mergedLibrary', 'bigwig', f'{sample}.bigWig')
        
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
