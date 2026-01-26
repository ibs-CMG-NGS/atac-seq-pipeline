process ATAC_PIPELINE_REPORT {
    tag "Pipeline QC Report"
    label 'process_single'

    conda "conda-forge::python=3.9"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/python:3.9--1' :
        'biocontainers/python:3.9--1' }"

    input:
    path results_dir

    output:
    path "pipeline_qc_report.html", emit: html
    path "versions.yml"           , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    # Generate comprehensive pipeline QC report
    atac_pipeline_report.py ${results_dir} pipeline_qc_report.html

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version 2>&1 | sed 's/Python //g')
        atac_pipeline_report: 1.0.0
    END_VERSIONS
    """
}
