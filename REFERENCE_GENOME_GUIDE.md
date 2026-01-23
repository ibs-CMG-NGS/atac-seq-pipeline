# ATAC-seq Pipeline 참조 유전체 준비 가이드

이 문서는 nf-core/atacseq 파이프라인에서 사용할 참조 유전체를 준비하는 방법을 설명합니다.

## 목차
1. [iGenomes 사용하기 (권장)](#1-igenomes-사용하기-권장)
2. [커스텀 참조 유전체 준비하기](#2-커스텀-참조-유전체-준비하기)
3. [필수 파일 목록](#3-필수-파일-목록)
4. [참조 유전체 다운로드 예시](#4-참조-유전체-다운로드-예시)

---

## 1. iGenomes 사용하기 (권장)

### 개요
nf-core는 주요 모델 생물의 참조 유전체를 사전 구축하여 제공합니다 (AWS S3 호스팅).

### 지원되는 유전체
```yaml
# 인간 (Human)
genome: 'GRCh37'  # hg19
genome: 'GRCh38'  # hg38

# 마우스 (Mouse)
genome: 'GRCm38'  # mm10
genome: 'GRCm39'  # mm39

# 기타
genome: 'BDGP6'      # Drosophila melanogaster
genome: 'CanFam3.1'  # Dog
genome: 'CHIMP2.1.4' # Chimpanzee
genome: 'EquCab2'    # Horse
genome: 'Galgal4'    # Chicken
genome: 'Mmul_1'     # Macaque
genome: 'NCBIM37'    # Mouse (old)
genome: 'Rnor_6.0'   # Rat
genome: 'Sscrofa10.2' # Pig
genome: 'susScr3'    # Pig (old)
genome: 'Zv9'        # Zebrafish
genome: 'WBcel235'   # C. elegans
```

### 사용 방법
```bash
nextflow run nf-core/atacseq \
  --input samplesheet.csv \
  --outdir results \
  --genome GRCh38 \
  --read_length 150 \
  -profile docker
```

**또는 params.yaml:**
```yaml
genome: 'GRCh38'
read_length: 150
```

### 로컬 iGenomes 캐시 사용 (선택사항)
대역폭을 절약하고 싶다면 iGenomes를 로컬에 다운로드:

```bash
# iGenomes 다운로드 (예: GRCh38)
aws s3 --no-sign-request sync \
  s3://ngi-igenomes/igenomes/Homo_sapiens/NCBI/GRCh38/ \
  /data/igenomes/Homo_sapiens/NCBI/GRCh38/
```

**params.yaml 설정:**
```yaml
genome: 'GRCh38'
igenomes_base: '/data/igenomes'
igenomes_ignore: false
```

---

## 2. 커스텀 참조 유전체 준비하기

iGenomes에 없는 유전체를 사용하거나 커스텀 어노테이션이 필요한 경우:

### 2.1 기본 설정 (최소 요구사항)

**필수 파일:**
- FASTA 파일 (`.fa`, `.fasta`, 압축 가능 `.gz`)
- GTF 파일 (`.gtf`, 압축 가능 `.gz`)

**params.yaml:**
```yaml
genome: null  # iGenomes를 사용하지 않음
fasta: '/path/to/genome/genome.fa'
gtf: '/path/to/genome/genes.gtf'
read_length: 150
```

파이프라인이 자동으로 생성하는 것들:
- Aligner 인덱스 (BWA, Bowtie2, STAR 등)
- Gene BED 파일 (GTF에서 변환)
- TSS BED 파일
- Chromosome sizes 파일

### 2.2 완전한 설정 (사전 빌드된 인덱스 포함)

인덱스를 미리 만들어두면 시간과 연산 자원을 절약할 수 있습니다.

**디렉토리 구조 예시:**
```
/data/genomes/hg38_custom/
├── genome.fa
├── genome.fa.fai          # samtools faidx로 생성
├── genes.gtf
├── genes.bed              # 선택사항
├── blacklist.bed          # 선택사항 (ENCODE blacklist)
├── bwa_index/             # BWA 인덱스
│   ├── genome.fa.amb
│   ├── genome.fa.ann
│   ├── genome.fa.bwt
│   ├── genome.fa.pac
│   └── genome.fa.sa
├── bowtie2_index/         # Bowtie2 인덱스
│   ├── genome.1.bt2
│   ├── genome.2.bt2
│   ├── genome.3.bt2
│   ├── genome.4.bt2
│   ├── genome.rev.1.bt2
│   └── genome.rev.2.bt2
└── star_index/            # STAR 인덱스
    ├── Genome
    ├── SA
    ├── SAindex
    └── ...
```

**params.yaml:**
```yaml
genome: null
fasta: '/data/genomes/hg38_custom/genome.fa'
gtf: '/data/genomes/hg38_custom/genes.gtf'
gene_bed: '/data/genomes/hg38_custom/genes.bed'
blacklist: '/data/genomes/hg38_custom/blacklist.bed'

# Aligner 인덱스 (사용하는 aligner에 맞게 선택)
aligner: 'bwa'
bwa_index: '/data/genomes/hg38_custom/bwa_index/'
# bowtie2_index: '/data/genomes/hg38_custom/bowtie2_index/'
# star_index: '/data/genomes/hg38_custom/star_index/'

# ATAC-seq 특화 설정
mito_name: 'chrM'  # 미토콘드리아 염색체 이름 (MT, chrM, M 등)
macs_gsize: '2.7e9'  # Effective genome size (human: 2.7e9, mouse: 1.87e9)

read_length: 150
save_reference: true  # 생성된 인덱스 저장
```

---

## 3. 필수 파일 목록

### 3.1 FASTA 파일 (필수)
- **형식:** `.fa`, `.fasta`, `.fa.gz`, `.fasta.gz`
- **내용:** 참조 유전체 시퀀스
- **예시:** `Homo_sapiens.GRCh38.dna.primary_assembly.fa`

### 3.2 GTF 파일 (필수)
- **형식:** `.gtf`, `.gtf.gz`
- **내용:** 유전자 어노테이션
- **예시:** `Homo_sapiens.GRCh38.109.gtf`

**대체 가능:** GFF 파일 (`.gff`, `.gff3`)
```yaml
gff: '/path/to/genes.gff3'  # GTF 대신 사용 가능
```

### 3.3 Blacklist BED 파일 (강력 권장)
- **형식:** `.bed`
- **내용:** 제외할 genomic regions (반복 서열, 인공물 등)
- **다운로드:** [ENCODE Blacklist](https://github.com/Boyle-Lab/Blacklist)

**주요 유전체별 blacklist:**
- **hg19:** `hg19-blacklist.v2.bed`
- **hg38:** `hg38-blacklist.v2.bed`
- **mm10:** `mm10-blacklist.v2.bed`

### 3.4 미토콘드리아 염색체 이름 (중요)
FASTA 파일의 미토콘드리아 염색체 이름을 확인하고 설정:

```bash
# FASTA 파일에서 염색체 이름 확인
grep "^>" genome.fa | head -20

# 미토콘드리아 염색체 찾기
grep -i "mito\|^>M\|^>MT\|^>chrM" genome.fa
```

**흔한 이름:**
- Ensembl: `MT`
- UCSC: `chrM`
- NCBI: `M`

**params.yaml 설정:**
```yaml
mito_name: 'chrM'  # 또는 'MT', 'M'
```

### 3.5 MACS2 Genome Size
Peak calling에 필요한 effective genome size:

| 유전체 | Genome Size | Read Length 50 | Read Length 100 | Read Length 150 |
|--------|-------------|----------------|-----------------|-----------------|
| Human (hg38) | 2.7e9 | 2.7e9 | 2.7e9 | 2.7e9 |
| Human (hg19) | 2.7e9 | 2.7e9 | 2.7e9 | 2.7e9 |
| Mouse (mm10) | 1.87e9 | 1.87e9 | 1.87e9 | 1.87e9 |
| Mouse (mm39) | 1.87e9 | 1.87e9 | 1.87e9 | 1.87e9 |

**params.yaml:**
```yaml
macs_gsize: '2.7e9'  # 또는 'hs', 'mm' (MACS2 내장 값)
```

---

## 4. 참조 유전체 다운로드 예시

### 4.1 Human (GRCh38/hg38) - Ensembl

```bash
# 디렉토리 생성
mkdir -p /data/genomes/GRCh38_ensembl
cd /data/genomes/GRCh38_ensembl

# FASTA 다운로드
wget http://ftp.ensembl.org/pub/release-109/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
gunzip Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz

# GTF 다운로드
wget http://ftp.ensembl.org/pub/release-109/gtf/homo_sapiens/Homo_sapiens.GRCh38.109.gtf.gz
gunzip Homo_sapiens.GRCh38.109.gtf.gz

# Blacklist 다운로드
wget https://github.com/Boyle-Lab/Blacklist/raw/master/lists/hg38-blacklist.v2.bed.gz
gunzip hg38-blacklist.v2.bed.gz

# FASTA 인덱스 생성
samtools faidx Homo_sapiens.GRCh38.dna.primary_assembly.fa
```

**params.yaml:**
```yaml
genome: null
fasta: '/data/genomes/GRCh38_ensembl/Homo_sapiens.GRCh38.dna.primary_assembly.fa'
gtf: '/data/genomes/GRCh38_ensembl/Homo_sapiens.GRCh38.109.gtf'
blacklist: '/data/genomes/GRCh38_ensembl/hg38-blacklist.v2.bed'
mito_name: 'MT'
macs_gsize: '2.7e9'
read_length: 150
save_reference: true
```

### 4.2 Human (GRCh38/hg38) - UCSC

```bash
mkdir -p /data/genomes/hg38_ucsc
cd /data/genomes/hg38_ucsc

# FASTA 다운로드
wget https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz
gunzip hg38.fa.gz

# GTF 다운로드 (GENCODE)
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.annotation.gtf.gz
gunzip gencode.v43.annotation.gtf.gz

# Blacklist
wget https://github.com/Boyle-Lab/Blacklist/raw/master/lists/hg38-blacklist.v2.bed.gz
gunzip hg38-blacklist.v2.bed.gz

# 인덱스
samtools faidx hg38.fa
```

**params.yaml:**
```yaml
fasta: '/data/genomes/hg38_ucsc/hg38.fa'
gtf: '/data/genomes/hg38_ucsc/gencode.v43.annotation.gtf'
blacklist: '/data/genomes/hg38_ucsc/hg38-blacklist.v2.bed'
mito_name: 'chrM'
macs_gsize: '2.7e9'
```

### 4.3 Mouse (GRCm39/mm39) - Ensembl

```bash
mkdir -p /data/genomes/GRCm39_ensembl
cd /data/genomes/GRCm39_ensembl

# FASTA
wget http://ftp.ensembl.org/pub/release-109/fasta/mus_musculus/dna/Mus_musculus.GRCm39.dna.primary_assembly.fa.gz
gunzip Mus_musculus.GRCm39.dna.primary_assembly.fa.gz

# GTF
wget http://ftp.ensembl.org/pub/release-109/gtf/mus_musculus/Mus_musculus.GRCm39.109.gtf.gz
gunzip Mus_musculus.GRCm39.109.gtf.gz

# Blacklist
wget https://github.com/Boyle-Lab/Blacklist/raw/master/lists/mm10-blacklist.v2.bed.gz
gunzip mm10-blacklist.v2.bed.gz

# 인덱스
samtools faidx Mus_musculus.GRCm39.dna.primary_assembly.fa
```

**params.yaml:**
```yaml
fasta: '/data/genomes/GRCm39_ensembl/Mus_musculus.GRCm39.dna.primary_assembly.fa'
gtf: '/data/genomes/GRCm39_ensembl/Mus_musculus.GRCm39.109.gtf'
blacklist: '/data/genomes/GRCm39_ensembl/mm10-blacklist.v2.bed'
mito_name: 'MT'
macs_gsize: '1.87e9'
```

### 4.4 사전 빌드된 인덱스 생성

#### BWA 인덱스
```bash
mkdir -p /data/genomes/GRCh38_ensembl/bwa_index
cd /data/genomes/GRCh38_ensembl/bwa_index

# 인덱스 생성 (30분~2시간 소요)
bwa index -p genome ../Homo_sapiens.GRCh38.dna.primary_assembly.fa
```

#### Bowtie2 인덱스
```bash
mkdir -p /data/genomes/GRCh38_ensembl/bowtie2_index
cd /data/genomes/GRCh38_ensembl/bowtie2_index

# 인덱스 생성
bowtie2-build ../Homo_sapiens.GRCh38.dna.primary_assembly.fa genome
```

#### STAR 인덱스
```bash
mkdir -p /data/genomes/GRCh38_ensembl/star_index

# 인덱스 생성 (많은 메모리 필요: ~32GB)
STAR --runMode genomeGenerate \
  --genomeDir /data/genomes/GRCh38_ensembl/star_index \
  --genomeFastaFiles /data/genomes/GRCh38_ensembl/Homo_sapiens.GRCh38.dna.primary_assembly.fa \
  --sjdbGTFfile /data/genomes/GRCh38_ensembl/Homo_sapiens.GRCh38.109.gtf \
  --sjdbOverhang 100 \
  --runThreadN 16
```

---

## 5. 검증 및 테스트

### 5.1 파일 무결성 확인

```bash
# FASTA 파일 확인
head -20 genome.fa
samtools faidx genome.fa

# GTF 파일 확인
head -20 genes.gtf
zcat genes.gtf.gz | head -20  # 압축된 경우

# Chromosome 목록 확인
cut -f1 genome.fa.fai | head -30
```

### 5.2 파이프라인 테스트

```bash
# 작은 테스트 데이터로 검증
nextflow run nf-core/atacseq \
  -profile test,docker \
  --genome null \
  --fasta /data/genomes/GRCh38_ensembl/Homo_sapiens.GRCh38.dna.primary_assembly.fa \
  --gtf /data/genomes/GRCh38_ensembl/Homo_sapiens.GRCh38.109.gtf \
  --outdir test_custom_genome \
  --save_reference
```

---

## 6. 트러블슈팅

### 문제: "Chromosome XXX not found"
- FASTA와 GTF/BED 파일의 염색체 명명 규칙이 일치하는지 확인
- Ensembl: `1, 2, 3, ..., X, Y, MT`
- UCSC: `chr1, chr2, chr3, ..., chrX, chrY, chrM`

**해결책:** 동일한 소스(Ensembl 또는 UCSC)에서 모든 파일 다운로드

### 문제: "Mitochondrial reads not filtered"
- `mito_name` 파라미터가 FASTA 파일의 실제 염색체 이름과 일치하는지 확인

```bash
# 확인
grep "^>" genome.fa | grep -i mito
```

### 문제: 인덱스 생성 실패
- 메모리 부족: STAR 인덱스는 32GB+ 필요
- 디스크 공간 부족 확인
- 파이프라인이 자동으로 생성하도록 하거나 수동으로 생성

---

## 7. 권장사항

### 개발/테스트 환경 (WSL Ubuntu)
```yaml
# iGenomes 사용 (빠른 테스트)
genome: 'GRCh38'
save_reference: false
```

### 프로덕션 환경 (서버)
```yaml
# 로컬 참조 유전체 + 사전 빌드 인덱스
genome: null
fasta: '/shared/genomes/GRCh38/genome.fa'
gtf: '/shared/genomes/GRCh38/genes.gtf'
bwa_index: '/shared/genomes/GRCh38/bwa_index/'
blacklist: '/shared/genomes/GRCh38/blacklist.bed'
save_reference: false  # 이미 빌드됨
```

---

## 참고 자료

- [nf-core/atacseq documentation](https://nf-co.re/atacseq)
- [Ensembl FTP](http://ftp.ensembl.org/)
- [UCSC Genome Browser](https://genome.ucsc.edu/)
- [GENCODE](https://www.gencodegenes.org/)
- [ENCODE Blacklist](https://github.com/Boyle-Lab/Blacklist)
- [iGenomes](https://emea.support.illumina.com/sequencing/sequencing_software/igenome.html)
