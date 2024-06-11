process FILTER_BLASTN {
    tag "$meta.id"
    label 'process_low'

    conda "conda-forge::sed=4.7"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/ubuntu:20.04' :
        'nf-core/ubuntu:20.04' }"

    input:
    tuple val(meta), path(hits)
    path header
    path filtered_header

    output:
    tuple val(meta), path('*.txt'), emit: txt
    path "versions.yml"           , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def min_contig_length = params.min_contig_length
    def min_perc_cgaligned = params.min_perc_cgaligned

    """
    cat $header $hits > ${prefix}.blastn.txt
    awk 'BEGIN{OFS=\"\\t\";FS=\"\\t\"}{print \$0,\$6/\$16,\$6/\$15}' $hits | awk 'BEGIN{OFS=\"\\t\";FS=\"\\t\"} \$16 > ${min_contig_length} && \$18 > ${min_perc_cgaligned} && \$1 !~ /phage/ {print \$0}' > tmp.out
    cat $filtered_header tmp.out > ${prefix}.filter.blastn.txt

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        sed: \$(echo \$(sed --version 2>&1) | sed 's/^.*GNU sed) //; s/ .*\$//')
    END_VERSIONS
    """
}
