#!/bin/bash

# Make scripts executable
chmod +x bin/atac_qc_checker.py
chmod +x bin/generate_qc_html.py

echo "✅ ATAC-seq QC Summary tools installed successfully!"
echo ""
echo "📚 Documentation: docs/ATAC_QC_SUMMARY.md"
echo ""
echo "🧪 Test the tools:"
echo "  atac_qc_checker.py --help"
echo "  generate_qc_html.py --help"
echo ""
echo "🔬 After running the pipeline, check:"
echo "  results/qc_summary/qc_summary.html"
echo "  results/qc_summary/samples_need_review.txt"
