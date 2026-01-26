#!/usr/bin/env python3
"""
Generate HTML report from ATAC-seq QC summary JSON
"""

import sys
import json
from pathlib import Path
from datetime import datetime


def generate_html_report(json_file, html_output):
    """Generate HTML report from QC summary JSON"""
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Calculate statistics
    total = data['total_samples']
    passed = data['passed']
    failed = data['failed']
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    # Start HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATAC-seq QC Summary Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        h2 {{
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .stat-card.pass {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        
        .stat-card.fail {{
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        }}
        
        .stat-card h3 {{
            font-size: 14px;
            font-weight: 300;
            margin-bottom: 10px;
            opacity: 0.9;
        }}
        
        .stat-card .number {{
            font-size: 36px;
            font-weight: bold;
        }}
        
        .stat-card .percentage {{
            font-size: 14px;
            opacity: 0.8;
            margin-top: 5px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background-color: white;
        }}
        
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 12px;
        }}
        
        .status-pass {{
            background-color: #d4edda;
            color: #155724;
        }}
        
        .status-fail {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        
        .issue {{
            color: #dc3545;
            margin: 5px 0;
        }}
        
        .warning {{
            color: #fd7e14;
            margin: 5px 0;
        }}
        
        .issue-list {{
            list-style: none;
            padding-left: 0;
        }}
        
        .issue-list li {{
            padding: 4px 0;
        }}
        
        .issue-list li:before {{
            content: "• ";
            font-weight: bold;
        }}
        
        .no-issues {{
            background-color: #d4edda;
            color: #155724;
            padding: 30px;
            text-align: center;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 18px;
        }}
        
        .timestamp {{
            color: #6c757d;
            font-size: 14px;
            margin-top: 30px;
            text-align: right;
        }}
        
        .section-icon {{
            margin-right: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧬 ATAC-seq Quality Control Summary Report</h1>
        
        <div class="summary-stats">
            <div class="stat-card">
                <h3>Total Samples</h3>
                <div class="number">{total}</div>
            </div>
            <div class="stat-card pass">
                <h3>Passed QC</h3>
                <div class="number">{passed}</div>
                <div class="percentage">{pass_rate:.1f}%</div>
            </div>
            <div class="stat-card fail">
                <h3>Failed QC</h3>
                <div class="number">{failed}</div>
                <div class="percentage">{100-pass_rate:.1f}%</div>
            </div>
        </div>
"""
    
    # Add samples requiring review
    if data['requires_review']:
        html += f"""
        <h2><span class="section-icon">⚠️</span>Samples Requiring Review ({len(data['requires_review'])})</h2>
        <table>
            <thead>
                <tr>
                    <th>Sample Name</th>
                    <th>Status</th>
                    <th>Total Reads</th>
                    <th>Issues</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for result in data['requires_review']:
            status_class = 'status-pass' if result['status'] == 'PASS' else 'status-fail'
            total_reads = result.get('basic_stats', {}).get('Total Sequences', 'N/A')
            
            issues_html = '<ul class="issue-list">'
            
            if result.get('issues'):
                for issue in result['issues']:
                    issues_html += f'<li class="issue">🔴 {issue}</li>'
            
            if result.get('warnings'):
                for warning in result['warnings']:
                    issues_html += f'<li class="warning">⚠️ {warning}</li>'
            
            issues_html += '</ul>'
            
            html += f"""
                <tr>
                    <td><strong>{result['sample']}</strong></td>
                    <td><span class="status-badge {status_class}">{result['status']}</span></td>
                    <td>{total_reads}</td>
                    <td>{issues_html}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
"""
    else:
        html += """
        <div class="no-issues">
            <strong>✅ Excellent!</strong> All samples passed quality control.<br>
            No manual review required.
        </div>
"""
    
    # Add all samples summary table
    html += f"""
        <h2><span class="section-icon">📊</span>All Samples Overview</h2>
        <table>
            <thead>
                <tr>
                    <th>Sample Name</th>
                    <th>Status</th>
                    <th>Total Reads</th>
                    <th>GC%</th>
                    <th>Issues Count</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for result in sorted(data['all_results'], key=lambda x: (x['status'] != 'PASS', x['sample'])):
        status_class = 'status-pass' if result['status'] == 'PASS' else 'status-fail'
        total_reads = result.get('basic_stats', {}).get('Total Sequences', 'N/A')
        gc_content = result.get('basic_stats', {}).get('%GC', 'N/A')
        issue_count = len(result.get('issues', []))
        warning_count = len(result.get('warnings', []))
        
        issues_text = f"{issue_count} issues" if issue_count > 0 else ""
        if warning_count > 0:
            issues_text += f", {warning_count} warnings" if issues_text else f"{warning_count} warnings"
        if not issues_text:
            issues_text = "None"
        
        html += f"""
                <tr>
                    <td>{result['sample']}</td>
                    <td><span class="status-badge {status_class}">{result['status']}</span></td>
                    <td>{total_reads}</td>
                    <td>{gc_content}</td>
                    <td>{issues_text}</td>
                </tr>
"""
    
    html += f"""
            </tbody>
        </table>
        
        <div class="timestamp">
            Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    with open(html_output, 'w') as f:
        f.write(html)
    
    print(f"HTML report generated: {html_output}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: generate_qc_html.py <input.json> <output.html>")
        sys.exit(1)
    
    generate_html_report(sys.argv[1], sys.argv[2])
