# 🖥️ 서버 환경 설정 가이드

이 문서는 Linux 서버에서 ATAC-seq 파이프라인을 실행하기 위한 환경 설정 방법을 설명합니다.

## 📋 목차

1. [필수 요구사항](#1-필수-요구사항)
2. [Apptainer 설치](#2-apptainer-설치)
3. [Conda 환경 설정](#3-conda-환경-설정)
4. [파이프라인 설정](#4-파이프라인-설정)
5. [실행 확인](#5-실행-확인)
6. [트러블슈팅](#6-트러블슈팅)

---

## 1. 필수 요구사항

### 1.1 시스템 요구사항

- **운영체제**: Ubuntu 20.04+ / CentOS 7+ / RHEL 7+
- **권한**: sudo (관리자) 권한 (Apptainer 설치용)
- **디스크**: 최소 100GB 여유 공간 (데이터 + 결과물 + 캐시)
- **메모리**: 최소 16GB RAM (권장 32GB+)
- **CPU**: 최소 8 cores (권장 16+ cores)

### 1.2 필수 소프트웨어

✅ **반드시 필요**:
- Apptainer/Singularity (컨테이너 시스템) ⭐
- Conda/Mamba (환경 관리)
- Java 11+ (Nextflow용)
- Git

⚠️ **없으면 파이프라인 실행 불가**:
- Apptainer가 없으면 `-profile singularity` 사용 불가
- Docker가 없고 Apptainer도 없으면 `-profile conda` 사용 (매우 느림)

---

## 2. Apptainer 설치

### 2.1 설치 확인

```bash
# Apptainer 설치 여부 확인
apptainer --version

# Singularity 확인 (구버전)
singularity --version

# Docker 확인 (대안)
docker --version
```

### 2.2 Apptainer 설치 (Ubuntu/Debian)

**관리자 권한 필요:**

```bash
# 시스템 업데이트
sudo apt update
sudo apt install -y software-properties-common

# Apptainer PPA 추가
sudo add-apt-repository -y ppa:apptainer/ppa
sudo apt update

# Apptainer 설치
sudo apt install -y apptainer

# 설치 확인
apptainer --version
# 예상 출력: apptainer version 1.4.5
```

### 2.3 Apptainer 설치 (CentOS/RHEL)

```bash
# EPEL 저장소 활성화
sudo yum install -y epel-release

# Apptainer 설치
sudo yum install -y apptainer

# 설치 확인
apptainer --version
```

### 2.4 수동 설치 (최신 버전)

```bash
# 의존성 설치
sudo apt install -y \
    build-essential \
    libseccomp-dev \
    pkg-config \
    squashfs-tools \
    cryptsetup \
    wget \
    git

# Go 설치 (Apptainer 빌드용)
export VERSION=1.21.0 OS=linux ARCH=amd64
wget https://dl.google.com/go/go$VERSION.$OS-$ARCH.tar.gz
sudo tar -C /usr/local -xzvf go$VERSION.$OS-$ARCH.tar.gz
rm go$VERSION.$OS-$ARCH.tar.gz

echo 'export PATH=/usr/local/go/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# Apptainer 다운로드 및 빌드
export VERSION=1.4.5
wget https://github.com/apptainer/apptainer/releases/download/v${VERSION}/apptainer-${VERSION}.tar.gz
tar -xzf apptainer-${VERSION}.tar.gz
cd apptainer-${VERSION}

./mconfig
make -C builddir
sudo make -C builddir install

# 설치 확인
apptainer --version
```

### 2.5 캐시 디렉토리 설정

```bash
# Apptainer 캐시 디렉토리 생성
mkdir -p ~/.apptainer/cache
mkdir -p ~/.singularity/cache

# 환경 변수 설정
echo 'export APPTAINER_CACHEDIR="$HOME/.apptainer/cache"' >> ~/.bashrc
echo 'export NXF_SINGULARITY_CACHEDIR="$HOME/.singularity/cache"' >> ~/.bashrc
source ~/.bashrc

# 확인
echo $APPTAINER_CACHEDIR
echo $NXF_SINGULARITY_CACHEDIR
```

---

## 3. Conda 환경 설정

### 3.1 Conda 설치 확인

```bash
conda --version
# 없으면 Miniconda 설치
```

### 3.2 파이프라인 환경 생성

```bash
# 환경 생성
conda create -n atac-seq-pipeline python=3.10 -y

# 환경 활성화
conda activate atac-seq-pipeline

# Nextflow 설치
conda install -c bioconda nextflow -y

# 버전 확인
nextflow -version
```

---

## 4. 파이프라인 설정

### 4.1 GitHub에서 Clone

```bash
# 작업 디렉토리로 이동
cd ~/ngs-pipeline

# Repository clone
git clone https://github.com/ibs-cmg-ngs/atac-seq-pipeline.git
cd atac-seq-pipeline

# 환경 활성화
conda activate atac-seq-pipeline
```

### 4.2 스크립트 실행 권한 부여 ⚠️ 필수

```bash
# bin 디렉토리의 모든 스크립트에 실행 권한 부여
chmod +x bin/*

# 확인
ls -l bin/ | head
```

### 4.3 설정 파일 준비

```bash
# 템플릿 복사
cp samplesheet_template.csv samplesheet.csv
cp params_template.yaml params.yaml

# 편집
nano samplesheet.csv
nano params.yaml
```

### 4.4 환경 변수 설정

```bash
# ~/.bashrc에 추가
cat >> ~/.bashrc << 'EOF'

# ATAC-seq Pipeline 환경 변수
export NXF_OPTS='-Xms1g -Xmx4g'
export NXF_SINGULARITY_CACHEDIR="$HOME/.singularity/cache"
export APPTAINER_CACHEDIR="$HOME/.apptainer/cache"

# Conda 환경 자동 활성화 (선택사항)
# conda activate atac-seq-pipeline

EOF

# 적용
source ~/.bashrc
```

---

## 5. 실행 확인

### 5.1 컨테이너 테스트

```bash
# Apptainer로 간단한 컨테이너 실행
apptainer exec docker://python:3.8.3 python --version

# 성공하면 다음 출력:
# Python 3.8.3
```

### 5.2 파이프라인 테스트

```bash
# 작은 테스트 데이터로 검증
nextflow run nf-core/atacseq \
  -profile test,singularity \
  --outdir test_results

# 성공 시 다음 메시지:
# Pipeline completed successfully
```

### 5.3 실제 데이터 실행

```bash
# 프로덕션 실행
nextflow run . \
  -profile singularity \
  -params-file params.yaml \
  -resume

# 백그라운드 실행 (권장)
nohup nextflow run . \
  -profile singularity \
  -params-file params.yaml \
  -resume > pipeline.log 2>&1 &

# 로그 확인
tail -f pipeline.log
```

---

## 6. 트러블슈팅

### 6.1 "singularity: command not found" 에러

**증상:**
```
bash: line 1: singularity: command not found
ERROR ~ Error executing process > 'NFCORE_ATACSEQ:ATACSEQ:INPUT_CHECK:SAMPLESHEET_CHECK'
```

**원인**: Apptainer/Singularity가 설치되지 않음

**해결 방법:**
```bash
# 1. Apptainer 설치 확인
apptainer --version

# 2. 없으면 설치 (관리자 권한 필요)
sudo apt install -y apptainer

# 3. 또는 Conda 프로파일 사용 (느림)
nextflow run . -profile conda -params-file params.yaml
```

### 6.2 "Permission denied" 에러

**증상:**
```
Permission denied: /tmp/apptainer-xxxxx
```

**해결 방법:**
```bash
# 임시 디렉토리 권한 확인
chmod 1777 /tmp

# 또는 사용자 디렉토리 사용
export APPTAINER_TMPDIR="$HOME/tmp"
mkdir -p $APPTAINER_TMPDIR
```

### 6.3 캐시 디렉토리 문제

**증상:**
```
WARNING: NXF_SINGULARITY_CACHEDIR is not defined
WARN: Singularity cache directory has not been defined -- Remote image will be stored in the path: /home/ngs/ngs-pipeline/atac-seq-pipeline/work/singularity
```

**해결 방법:**
```bash
# 캐시 디렉토리 설정
export NXF_SINGULARITY_CACHEDIR="$HOME/.singularity/cache"
mkdir -p $NXF_SINGULARITY_CACHEDIR

# ~/.bashrc에 영구 저장 (권장)
echo 'export NXF_SINGULARITY_CACHEDIR="$HOME/.singularity/cache"' >> ~/.bashrc
source ~/.bashrc
```

### 6.4 "Permission denied" - 스크립트 실행 권한 문제

**증상:**
```
.command.sh: line 3: /home/ngs/ngs-pipeline/atac-seq-pipeline/bin/gtf2bed: Permission denied
ERROR ~ Error executing process > 'NFCORE_ATACSEQ:ATACSEQ:PREPARE_GENOME:GTF2BED'
```

**원인**: `bin/` 디렉토리의 스크립트 파일에 실행 권한이 없음

**해결 방법:**
```bash
# bin 디렉토리의 모든 스크립트에 실행 권한 부여
chmod +x bin/gtf2bed
chmod +x bin/*.py
chmod +x bin/*.r
chmod +x bin/*.sh

# 또는 한번에
chmod +x bin/*

# 파이프라인 재개
nextflow run . -profile singularity -params-file params.yaml -resume
```

### 6.5 관리자 권한이 없는 경우

**문제**: Apptainer/Docker를 설치할 수 없음

**해결 방법:**
```bash
# 1. 시스템 관리자에게 Apptainer 설치 요청 (권장)

# 2. Conda 프로파일 사용 (느리지만 작동함)
nextflow run . -profile conda -params-file params.yaml

# 3. 로컬 컴퓨터(WSL)에서 Docker 사용
# WSL Ubuntu에서:
nextflow run . -profile docker -params-file params.yaml
```

### 6.6 디스크 공간 부족

**증상:**
```
No space left on device
```

**해결 방법:**
```bash
# 디스크 사용량 확인
df -h

# Apptainer 캐시 정리
rm -rf ~/.apptainer/cache/*
rm -rf ~/.singularity/cache/*

# Nextflow work 디렉토리 정리
rm -rf work/

# 이전 결과물 백업 후 삭제
tar -czf old_results.tar.gz results/
rm -rf results/
```

### 6.7 메모리 부족

**증상 1: Java heap space**
```
OutOfMemoryError: Java heap space
```

**해결 방법:**
```bash
# Java 메모리 증가
export NXF_OPTS='-Xms2g -Xmx8g'
```

**증상 2: Process 메모리 요구량 초과**
```
ERROR ~ Error executing process > 'NFCORE_ATACSEQ:ATACSEQ:FASTQ_FASTQC_UMITOOLS_TRIMGALORE:TRIMGALORE'
Caused by:
  Process requirement exceeds available memory -- req: 72 GB; avail: 62.8 GB
```

**원인**: 파이프라인이 요구하는 메모리가 서버 사용 가능 메모리보다 큼

**해결 방법 1: 명령줄에서 최대 메모리 설정 (권장)**
```bash
# 서버의 사용 가능한 메모리로 제한
nextflow run . \
  -profile singularity \
  -params-file params.yaml \
  --max_memory '60.GB' \
  -resume
```

**해결 방법 2: params 파일에 추가**
```bash
# params.yaml 파일 편집
nano params.yaml

# 다음 줄 추가:
# max_memory: '60.GB'
# max_cpus: 16
```

**해결 방법 3: 커스텀 config 파일 생성**
```bash
# custom.config 생성
cat > custom.config << 'EOF'
params {
    max_memory = 60.GB
    max_cpus = 16
}

process {
    // 특정 프로세스 메모리 제한
    withName: 'TRIMGALORE' {
        memory = { check_max( 48.GB * task.attempt, 'memory' ) }
    }
}
EOF

# 커스텀 config로 실행
nextflow run . \
  -profile singularity \
  -params-file params.yaml \
  -c custom.config \
  -resume
```

### 6.8 세션 락(Lock) 문제

**증상:**
```
ERROR ~ Unable to acquire lock on session with ID xxxxx
```

**원인**: 이전 실행이 비정상 종료되어 락 파일이 남아있음

**해결 방법:**
```bash
# 방법 1: 전체 Nextflow 캐시 삭제 (권장)
rm -rf .nextflow/
rm -rf .nextflow.log*

# 방법 2: 특정 세션만 삭제
# rm -rf .nextflow/cache/<SESSION_ID>

# 방법 3: 락 파일만 삭제
# rm -f .nextflow/cache/<SESSION_ID>/db/LOCK

# 다시 실행
nextflow run . -profile singularity -params-file params.yaml
```

### 6.9 Singularity 이미지 다운로드 타임아웃

**증상:**
```
ERROR ~ Error executing process > 'NFCORE_ATACSEQ:ATACSEQ:FASTQ_FASTQC_UMITOOLS_TRIMGALORE:TRIMGALORE'
Caused by:
  Failed to pull singularity image
    status : 143
    hint   : Try and increase singularity.pullTimeout in the config (current is "20m")
```

**원인**: 네트워크 속도가 느려 20분 내에 이미지 다운로드 실패

**해결 방법 1: Timeout 증가 (권장)**
```bash
# nextflow.config 파일 편집
nano nextflow.config

# 파일 끝에 추가:
# singularity {
#     pullTimeout = '60m'
# }

# 또는 환경 변수로 설정
export NXF_SINGULARITY_PULL_TIMEOUT='60m'

# 파이프라인 재실행
nextflow run . -profile singularity -params-file params.yaml -resume
```

**해결 방법 2: 이미지 미리 다운로드**
```bash
# 캐시 디렉토리로 이동
cd ~/.singularity/cache

# 필요한 이미지 수동 다운로드
apptainer pull docker://quay.io/biocontainers/trim-galore:0.6.7--hdfd78af_0

# 다운로드 완료 후 파이프라인 재실행
cd ~/ngs-pipeline/atac-seq-pipeline
nextflow run . -profile singularity -params-file params.yaml -resume
```

**해결 방법 3: 명령줄에서 직접 설정**
```bash
nextflow run . \
  -profile singularity \
  -params-file params.yaml \
  -resume \
  -c <(echo "singularity.pullTimeout = '60m'")
```

---

## 📚 추가 참고자료

- [Apptainer 공식 문서](https://apptainer.org/docs/)
- [Nextflow 설치 가이드](https://www.nextflow.io/docs/latest/getstarted.html)
- [nf-core/atacseq 문서](https://nf-co.re/atacseq)
- [CONDA_SETUP_GUIDE.md](./CONDA_SETUP_GUIDE.md)
- [QUICK_START_KR.md](./QUICK_START_KR.md)

---

## ✅ 설정 완료 체크리스트

서버에서 다음 명령어들이 모두 성공하면 설정 완료:

```bash
# ✅ Apptainer 설치 확인
apptainer --version

# ✅ Conda 환경 확인
conda activate atac-seq-pipeline

# ✅ Nextflow 설치 확인
nextflow -version

# ✅ Git repository 확인
cd ~/ngs-pipeline/atac-seq-pipeline
git status

# ✅ 설정 파일 확인
ls -l samplesheet.csv params.yaml

# ✅ 환경 변수 확인
echo $NXF_SINGULARITY_CACHEDIR
echo $APPTAINER_CACHEDIR

# ✅ 테스트 실행
nextflow run nf-core/atacseq -profile test,singularity --outdir test_results
```

모든 항목이 성공하면 프로덕션 분석을 시작할 수 있습니다! 🎉
