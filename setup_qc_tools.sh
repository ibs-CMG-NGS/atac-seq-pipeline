#!/bin/bash

# Make scripts executable
chmod +x bin/atac_qc_checker.py
chmod +x bin/generate_qc_html.py
chmod +x bin/atac_pipeline_report.py

echo "✅ ATAC-seq QC Tools installed successfully!"
echo ""
echo "📚 Documentation: docs/ATAC_QC_SUMMARY.md"
echo ""
echo "🧪 Test the tools:"
echo "  atac_qc_checker.py --help"
echo "  generate_qc_html.py --help"
echo "  atac_pipeline_report.py --help"
echo ""
echo "🔬 After running the pipeline, check:"
echo "  results/qc_summary/qc_summary.html          # FastQC-based QC"
echo "  results/pipeline_qc/pipeline_qc_report.html # Full pipeline QC"
echo "  results/qc_summary/samples_need_review.txt  # Samples needing review"
