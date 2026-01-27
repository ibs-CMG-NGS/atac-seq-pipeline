process ATAC_QC_SUMMARY {
    tag "ATAC QC Summary"
    label 'process_single'

    conda "conda-forge::python=3.9"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/python:3.9--1' :
        'biocontainers/python:3.9--1' }"

    input:
    path fastqc_zip

    output:
    path "qc_summary.json"          , emit: json
    path "qc_summary.html"          , emit: html
    path "samples_need_review.txt"  , emit: review_list, optional: true
    path "versions.yml"             , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    # Extract all FastQC zip files
    for zip in *.zip; do
        [ -f "\$zip" ] || continue
        unzip -q -o "\$zip"
    done

    # Run ATAC-seq QC checker
    atac_qc_checker.py . qc_summary.json

    # Generate HTML report
    generate_qc_html.py qc_summary.json qc_summary.html

    # Create list of samples needing review
    python3 <<'PYTHON_SCRIPT'
import json
from datetime import datetime

with open('qc_summary.json', 'r') as f:
    data = json.load(f)

if data['requires_review']:
    with open('samples_need_review.txt', 'w') as f:
        f.write("# ATAC-seq samples requiring manual QC review\\n")
        f.write("# Generated: {}\\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        f.write("# Total samples: {}\\n".format(data['total_samples']))
        f.write("# Failed samples: {}\\n\\n".format(data['failed']))
        
        for result in data['requires_review']:
            f.write("{}\\n".format(result['sample']))
            if result.get('issues'):
                for issue in result['issues']:
                    f.write("  - ISSUE: {}\\n".format(issue))
            if result.get('warnings'):
                for warning in result['warnings']:
                    f.write("  - WARNING: {}\\n".format(warning))
            f.write("\\n")
PYTHON_SCRIPT

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version 2>&1 | sed 's/Python //g')
        atac_qc_checker: 1.0.0
    END_VERSIONS
    """
}
