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
    # Create empty placeholder files
    echo '{"total_samples": 0, "passed": 0, "failed": 0, "requires_review": []}' > qc_summary.json
    echo '<html><body><h1>QC Summary - Generate manually if needed</h1></body></html>' > qc_summary.html
    touch samples_need_review.txt

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version 2>&1 | sed 's/Python //g')
    END_VERSIONS
    """
}
