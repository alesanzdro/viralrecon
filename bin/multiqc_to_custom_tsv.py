#!/usr/bin/env python

import os
import sys
import errno
import argparse
import yaml
from collections import OrderedDict


def parse_args(args=None):
    Description = 'Create custom spreadsheet for pertinent MultiQC metrics generated by the nf-core/viralrecon pipeline.'
    Epilog = "Example usage: python multiqc_to_custom_tsv.py"
    parser = argparse.ArgumentParser(description=Description, epilog=Epilog)
    parser.add_argument('-md', '--multiqc_data_dir', type=str, dest="MULTIQC_DATA_DIR", default='./multiqc_data/', help="Full path to directory containing YAML files for each module, as generated by MultiQC. (default: './multiqc_data/').")
    parser.add_argument('-of', '--out_file', type=str, dest="OUT_FILE", default='./viralrecon_summary_stats.tsv', help="Full path to output file (default: './viralrecon_summary_stats.tsv').")
    return parser.parse_args(args)


def make_dir(path):
    if not len(path) == 0:
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise


# Find key in dictionary created from YAML file recursively
# From https://stackoverflow.com/a/37626981
def find_tag(d, tag):
    if tag in d:
        yield d[tag]
    for k,v in d.items():
        if isinstance(v, dict):
            for i in find_tag(v, tag):
                yield i


# Load YAML as an ordered dict
# From https://stackoverflow.com/a/21912744
def yaml_ordered_load(stream):
    class OrderedLoader(yaml.SafeLoader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return OrderedDict(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def yaml_fields_to_dict(YAMLFile,AppendDict={},FieldMappingDict={}):
    with open(YAMLFile) as f:
        yaml_dict = yaml_ordered_load(f)
        for k in yaml_dict.keys():
            key = k
            if YAMLFile.find('multiqc_picard_insertSize') != -1:
                key = k[:-3]
            if key not in AppendDict:
                AppendDict[key] = OrderedDict()
            if FieldMappingDict != {}:
                for i,j in FieldMappingDict.items():
                    val = list(find_tag(yaml_dict[k], j[0]))
                    if len(val) != 0:
                        val = val[0]
                        if len(j) == 2:
                            val = list(find_tag(val, j[1]))[0]
                        if j[0] in ['number_of_SNPs', 'number_of_indels', 'MISSENSE']:
                            val = int(val)
                        if i not in AppendDict[key]:
                            AppendDict[key][i] = val
                        else:
                            print('WARNING: {} key already exists in dictionary so will be overwritten. YAML file {}.'.format(i,YAMLFile))
            else:
                AppendDict[key] = yaml_dict[k]
    return AppendDict


def main(args=None):
    args = parse_args(args)

    ## File names for MultiQC YAML along with fields to fetch from each file
    VariantFileFieldList = [
        ('multiqc_fastp.yaml',                                     OrderedDict([('Total input reads', ['before_filtering','total_reads']),
                                                                                ('Total reads after fastp trimming', ['after_filtering','total_reads'])])),
        ('multiqc_samtools_flagstat_samtools_bowtie2.yaml',        OrderedDict([('% reads mapped to virus', ['mapped_passed_pct'])])),
        ('multiqc_ivar_summary.yaml',                              OrderedDict([('Total reads trimmed by iVar', ['trimmed_reads'])])),
        ('multiqc_samtools_flagstat_samtools_ivar.yaml',           OrderedDict([('Total reads after iVar trimming', ['flagstat_total'])])),
        ('multiqc_samtools_flagstat_samtools_markduplicates.yaml', OrderedDict([('Total reads after MarkDuplicates', ['flagstat_total']),
                                                                                ('Duplicate reads', ['duplicates_passed'])])),
        ('multiqc_picard_insertSize.yaml',                         OrderedDict([('Insert size mean', ['MEAN_INSERT_SIZE']),
                                                                                ('Insert size std dev', ['STANDARD_DEVIATION'])])),
        ('multiqc_picard_wgsmetrics.yaml',                         OrderedDict([('Coverage mean', ['MEAN_COVERAGE']),
                                                                                ('Coverage std dev', ['SD_COVERAGE']),
                                                                                ('% Coverage > 10x', ['PCT_10X'])])),
        ('multiqc_bcftools_stats_bcftools_varscan2.yaml',          OrderedDict([('High conf SNPs (VarScan 2)', ['number_of_SNPs']),
                                                                                ('High conf INDELs (VarScan 2)', ['number_of_indels'])])),
        ('multiqc_snpeff_snpeff_varscan2.yaml',                    OrderedDict([('Missense variants (VarScan 2)', ['MISSENSE'])])),
        ('multiqc_quast_quast_varscan2.yaml',                      OrderedDict([('QUAST Consensus #N per 100kb (VarScan 2)', ["# N's per 100 kbp"])])),
        ('multiqc_bcftools_stats_bcftools_ivar.yaml',              OrderedDict([('High conf SNPs (iVar)', ['number_of_SNPs']),
                                                                                ('High conf INDELs (iVar)', ['number_of_indels'])])),
        ('multiqc_snpeff_snpeff_ivar.yaml',                        OrderedDict([('Nissense variants (iVar)', ['MISSENSE'])])),
        ('multiqc_quast_quast_ivar.yaml',                          OrderedDict([('QUAST Consensus #N per 100kb (iVar)', ["# N's per 100 kbp"])])),
        ('multiqc_bcftools_stats_bcftools_bcftools.yaml',          OrderedDict([('High conf SNPs (BCFTools)', ['number_of_SNPs']),
                                                                                ('High conf INDELs (BCFTools)', ['number_of_indels'])])),
        ('multiqc_snpeff_snpeff_bcftools.yaml',                    OrderedDict([('Missense variants (BCFTools)', ['MISSENSE'])])),
        ('multiqc_quast_quast_bcftools.yaml',                      OrderedDict([('QUAST Consensus #N per 100kb (BCFTools)', ["# N's per 100 kbp"])])),
    ]

    AssemblyFileFieldList = [
        ('multiqc_fastp.yaml',                                     OrderedDict([('Total input reads', ['before_filtering','total_reads'])])),
        #('multiqc_fastqc_fastqc_cutadapt.yaml',                    OrderedDict([('Total reads after cutadapt trimming', ['Total Sequences'])])), ## HAVE TO MULTIPLY BY 2 FOR PE READS?
        ('multiqc_bcftools_stats_bcftools_spades.yaml',            OrderedDict([('High conf SNPs (SPAdes)', ['number_of_SNPs']),
                                                                                ('High conf INDELs (SPAdes)', ['number_of_indels'])])),
        ('multiqc_snpeff_snpeff_spades.yaml',                      OrderedDict([('Missense variants (SPAdes)', ['MISSENSE'])])),
        ('multiqc_quast_quast_spades.yaml',                        OrderedDict([('Total contigs (SPAdes)', ['# contigs']),
                                                                                ('# contigs > 5kb (SPAdes)', ['# contigs (>= 5000 bp)']),
                                                                                ('Genome fraction (%) (SPAdes)', ['Genome fraction (%)']),
                                                                                ('Largest contig (SPAdes)', ['Largest contig']),
                                                                                ('N50 (SPAdes)', ['N50'])])),
        ('multiqc_bcftools_stats_bcftools_metaspades.yaml',        OrderedDict([('High conf SNPs (metaSPAdes)', ['number_of_SNPs']),
                                                                                ('High conf INDELs (metaSPAdes)', ['number_of_indels'])])),
        ('multiqc_snpeff_snpeff_metaspades.yaml',                  OrderedDict([('Missense variants (metaSPAdes)', ['MISSENSE'])])),
        ('multiqc_quast_quast_metaspades.yaml',                    OrderedDict([('Total contigs (metaSPAdes)', ['# contigs']),
                                                                                ('# contigs > 5kb (metaSPAdes)', ['# contigs (>= 5000 bp)']),
                                                                                ('Genome fraction (%) (metaSPAdes)', ['Genome fraction (%)']),
                                                                                ('Largest contig (metaSPAdes)', ['Largest contig']),
                                                                                ('N50 (metaSPAdes)', ['N50'])])),
        ('multiqc_bcftools_stats_bcftools_unicycler.yaml',         OrderedDict([('High conf SNPs (Unicycler)', ['number_of_SNPs']),
                                                                                ('High conf INDELs (Unicycler)', ['number_of_indels'])])),
        ('multiqc_snpeff_snpeff_unicycler.yaml',                   OrderedDict([('Missense variants (Unicycler)', ['MISSENSE'])])),
        ('multiqc_quast_quast_unicycler.yaml',                     OrderedDict([('Total contigs (Unicycler)', ['# contigs']),
                                                                                ('# contigs > 5kb (Unicycler)', ['# contigs (>= 5000 bp)']),
                                                                                ('Genome fraction (%) (Unicycler)', ['Genome fraction (%)']),
                                                                                ('Largest contig (Unicycler)', ['Largest contig']),
                                                                                ('N50 (Unicycler)', ['N50'])])),
        ('multiqc_bcftools_stats_bcftools_minia.yaml',             OrderedDict([('High conf SNPs (minia)', ['number_of_SNPs']),
                                                                                ('High conf INDELs (minia)', ['number_of_indels'])])),
        ('multiqc_snpeff_snpeff_minia.yaml',                       OrderedDict([('Missense variants (minia)', ['MISSENSE'])])),
        ('multiqc_quast_quast_minia.yaml',                         OrderedDict([('Total contigs (minia)', ['# contigs']),
                                                                                ('# contigs > 5kb (minia)', ['# contigs (>= 5000 bp)']),
                                                                                ('Genome fraction (%) (minia)', ['Genome fraction (%)']),
                                                                                ('Largest contig (minia)', ['Largest contig']),
                                                                                ('N50 (minia)', ['N50'])]))
    ]

    ## Get variant calling metrics
    VariantMetricsDict = {}
    VariantFieldList = []
    for yamlFile,mappingDict in VariantFileFieldList:
        yamlFile = os.path.join(args.MULTIQC_DATA_DIR,yamlFile)
        if os.path.exists(yamlFile):
            VariantMetricsDict = yaml_fields_to_dict(YAMLFile=yamlFile,AppendDict=VariantMetricsDict,FieldMappingDict=mappingDict)
            VariantFieldList += mappingDict.keys()

    ## Get assembly metrics
    AssemblyMetricsDict = {}
    AssemblyFieldList = []
    for yamlFile,mappingDict in AssemblyFileFieldList:
        yamlFile = os.path.join(args.MULTIQC_DATA_DIR,yamlFile)
        if os.path.exists(yamlFile):
            AssemblyMetricsDict = yaml_fields_to_dict(YAMLFile=yamlFile,AppendDict=AssemblyMetricsDict,FieldMappingDict=mappingDict)
            AssemblyFieldList += mappingDict.keys()

    ## Write to file
    if VariantMetricsDict != {}:
        make_dir(os.path.dirname(args.OUT_FILE))
        fout = open(args.OUT_FILE,'w')
        header = ['Sample'] + VariantFieldList
        fout.write('## Variant-calling metrics\n')
        fout.write('{}\n'.format('\t'.join(header)))
        for k in sorted(VariantMetricsDict.keys()):
            rowList = [k]
            for field in VariantFieldList:
                if field in VariantMetricsDict[k]:
                    rowList.append(VariantMetricsDict[k][field])
                else:
                    rowList.append('NA')
            fout.write('{}\n'.format('\t'.join(map(str,rowList))))
        fout.close()

    if AssemblyMetricsDict != {}:
        spacing = '\n\n'
        if VariantMetricsDict == {}:
            spacing = ''
        fout = open(args.OUT_FILE,'a')
        header = ['Sample'] + AssemblyFieldList
        fout.write('{}## De novo assembly metrics\n'.format(spacing))
        fout.write('{}\n'.format('\t'.join(header)))
        for k in sorted(AssemblyMetricsDict.keys()):
            rowList = [k]
            for field in AssemblyFieldList:
                if field in AssemblyMetricsDict[k]:
                    rowList.append(AssemblyMetricsDict[k][field])
                else:
                    rowList.append('NA')
            fout.write('{}\n'.format('\t'.join(map(str,rowList))))
        fout.close()

if __name__ == '__main__':
    sys.exit(main())
