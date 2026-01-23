# Conda 환경 설정 가이드

이 문서는 Conda를 사용하여 ATAC-seq 파이프라인 실행 환경을 구축하는 전체 과정을 설명합니다.

## 목차
1. [Conda 설치 확인](#1-conda-설치-확인)
2. [컨테이너 시스템 설치 (필수)](#2-컨테이너-시스템-설치-필수)
3. [Conda 환경 생성](#3-conda-환경-생성)
4. [Nextflow 설치](#4-nextflow-설치)
5. [의존성 패키지 설치](#5-의존성-패키지-설치)
6. [파이프라인 Repository 설정](#6-파이프라인-repository-설정)
7. [환경 활성화 및 검증](#7-환경-활성화-및-검증)
8. [환경 관리](#8-환경-관리)

---

## 1. Conda 설치 확인

### 1.1 Conda 설치 여부 확인

```bash
# Conda 설치 확인
conda --version

# 또는 mamba (더 빠른 conda 대안)
mamba --version
```

### 1.2 Conda가 설치되어 있지 않은 경우

**Miniconda 설치 (권장):**

```bash
# 최신 Miniconda 다운로드 (Linux x86_64)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# 설치 스크립트 실행
bash Miniconda3-latest-Linux-x86_64.sh

# 설치 중:
# - 라이선스 동의: yes
# - 설치 경로: 기본값 또는 원하는 경로
# - conda init 실행: yes (권장)

# 설치 후 터미널 재시작 또는:
source ~/.bashrc
# 또는 (zsh 사용 시)
source ~/.zshrc

# 설치 확인
conda --version
```

**Mamba 설치 (선택사항, 더 빠른 패키지 해결):**

```bash
conda install -n base -c conda-forge mamba
```

---

## 2. 컨테이너 시스템 설치 (필수)

### ⚠️ 중요: Apptainer/Singularity 또는 Docker 필수

Nextflow 파이프라인은 **컨테이너 시스템**을 사용하여 각 도구를 독립적인 환경에서 실행합니다.
서버에서 파이프라인을 실행하려면 반드시 다음 중 하나가 설치되어 있어야 합니다.

### 2.1 설치 확인

```bash
# Apptainer 확인 (권장)
apptainer --version

# Singularity 확인 (구버전)
singularity --version

# Docker 확인
docker --version

# Podman 확인
podman --version
```

### 2.2 Apptainer 설치 (권장)

**Ubuntu/Debian 시스템:**

```bash
# 관리자 권한 필요
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:apptainer/ppa
sudo apt update
sudo apt install -y apptainer

# 설치 확인
apptainer --version
```

**CentOS/RHEL 시스템:**

```bash
# EPEL 저장소 활성화
sudo yum install -y epel-release

# Apptainer 설치
sudo yum install -y apptainer

# 설치 확인
apptainer --version
```

### 2.3 대안: Conda 프로파일 사용

컨테이너 시스템 설치가 불가능한 경우 (관리자 권한이 없는 경우):

```bash
# -profile conda 사용 (속도 느림, 재현성 낮음)
nextflow run nf-core/atacseq \
  -profile conda \
  -params-file params.yaml
```

**⚠️ 주의:**
- Conda 프로파일은 컨테이너보다 느리고 환경 구축에 30분~1시간 소요
- 재현성이 낮아 권장하지 않음
- 가능하면 시스템 관리자에게 Apptainer 설치 요청

---

## 3. Conda 환경 생성

### 3.1 기본 환경 생성

```bash
# atac-seq-pipeline 환경 생성 (Python 3.10)
conda create -n atac-seq-pipeline python=3.10 -y

# 또는 mamba 사용 (더 빠름)
mamba create -n atac-seq-pipeline python=3.10 -y
```

### 3.2 환경 활성화

```bash
conda activate atac-seq-pipeline

# 프롬프트가 변경됨:
# (atac-seq-pipeline) user@host:~$
```

### 3.3 Conda 채널 설정

```bash
# Bioconda 및 필수 채널 추가
conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels conda-forge

# 채널 우선순위 설정
conda config --set channel_priority strict
```

---

## 4. Nextflow 설치

### 4.1 Nextflow 설치

**방법 A: Conda로 설치 (권장)**

```bash
# 환경이 활성화된 상태에서
conda install -c bioconda nextflow -y

# 또는 mamba 사용
mamba install -c bioconda nextflow -y
```

**방법 B: 직접 설치**

```bash
# Nextflow 다운로드 및 설치
curl -s https://get.nextflow.io | bash

# Conda 환경의 bin 디렉토리로 이동
mv nextflow $CONDA_PREFIX/bin/

# 실행 권한 부여
chmod +x $CONDA_PREFIX/bin/nextflow
```

### 3.2 Nextflow 설정

```bash
# Nextflow 버전 확인
nextflow -version

# 출력 예시:
#      N E X T F L O W
#      version 23.10.1 build 5891
#      created 10-01-2024 10:00 UTC
#      cite doi:10.1038/nbt.3820
#      http://nextflow.io

# Nextflow 설정 (선택사항)
export NXF_OPTS='-Xms1g -Xmx4g'  # Java 메모리 설정

# ~/.bashrc에 추가하여 영구 적용
echo 'export NXF_OPTS="-Xms1g -Xmx4g"' >> ~/.bashrc
```

---

## 4. 의존성 패키지 설치

### 4.1 필수 도구 설치

```bash
# 환경이 활성화된 상태에서 필수 도구 설치
conda install -c conda-forge -c bioconda \
    git \
    wget \
    curl \
    -y
```

### 4.2 파이프라인 실행 도구 설치

#### Singularity/Apptainer (권장)

```bash
# Apptainer (Singularity의 후속 버전)
# 대부분의 경우 시스템에 이미 설치되어 있음
apptainer --version

# 설치되어 있지 않은 경우 (시스템 관리자에게 문의)
# conda로는 설치하지 않는 것이 좋음
```

#### Docker (WSL/로컬 환경)

```bash
# Docker는 시스템 레벨 설치 필요
# WSL에서는 Docker Desktop 사용 권장
# Linux 서버에서는 시스템 관리자가 설치

# Docker 설치 확인
docker --version
```

### 4.3 분석 도구 설치 (선택사항)

파이프라인이 컨테이너를 사용하므로 대부분의 도구는 필요 없지만, 로컬 분석을 위해:

```bash
# Python 데이터 분석 도구
conda install -c conda-forge \
    pandas \
    matplotlib \
    seaborn \
    jupyter \
    -y

# R 및 필수 패키지 (선택사항)
conda install -c conda-forge -c bioconda \
    r-base \
    r-essentials \
    bioconductor-deseq2 \
    -y

# 생물정보학 도구 (로컬 분석용, 선택사항)
conda install -c bioconda \
    samtools \
    bedtools \
    deeptools \
    fastqc \
    multiqc \
    -y
```

### 4.4 환경 파일로 한번에 설치

**environment.yml 생성:**

```yaml
name: atac-seq-pipeline
channels:
  - conda-forge
  - bioconda
  - defaults
dependencies:
  # Python
  - python=3.10
  
  # Nextflow
  - nextflow
  
  # 기본 도구
  - git
  - wget
  - curl
  
  # Python 패키지
  - pandas
  - matplotlib
  - seaborn
  - jupyter
  - pyyaml
  
  # 생물정보학 도구 (선택사항)
  - samtools
  - bedtools
  - deeptools
  - fastqc
  - multiqc
  
  # R 및 Bioconductor (선택사항)
  # - r-base=4.3
  # - r-essentials
  # - bioconductor-deseq2
```

**환경 생성:**

```bash
# environment.yml 파일이 있는 디렉토리에서
conda env create -f environment.yml

# 또는 mamba로 (더 빠름)
mamba env create -f environment.yml
```

---

## 6. 파이프라인 Repository 설정

### 6.1 작업 디렉토리 준비

```bash
# 작업 디렉토리 생성
mkdir -p ~/ngs_pipeline
cd ~/ngs_pipeline
```

### 6.2 Repository Clone

**방법 A: GitHub에서 Clone (이미 푸시한 경우)**

```bash
# HTTPS 사용
git clone https://github.com/YOUR_USERNAME/atac-seq-pipeline.git
cd atac-seq-pipeline

# 또는 SSH 사용
git clone git@github.com:YOUR_USERNAME/atac-seq-pipeline.git
cd atac-seq-pipeline
```

**방법 B: 로컬에서 복사 (GitHub 사용 안 하는 경우)**

```bash
# WSL에서 이미 설정한 경로에서
cd ~/ngs_pipeline
# 이미 /home/ygkim/ngs_pipeline/atac-seq-pipeline에 있음

# 또는 다른 위치에서 복사
cp -r /home/ygkim/ngs_pipeline/atac-seq-pipeline ~/ngs_pipeline/
```

### 5.3 작업 파일 생성

```bash
cd ~/ngs_pipeline/atac-seq-pipeline

# 템플릿에서 작업 파일 생성
cp samplesheet_template.csv samplesheet.csv
cp params_template.yaml params.yaml

# 편집
nano samplesheet.csv
nano params.yaml
```

---

## 6. 환경 활성화 및 검증

### 6.1 환경 활성화 스크립트

`activate_pipeline.sh` 생성:

```bash
#!/bin/bash
# ATAC-seq Pipeline 환경 활성화 스크립트

echo "=========================================="
echo "ATAC-seq Pipeline Environment Activation"
echo "=========================================="

# Conda 환경 활성화
source $(conda info --base)/etc/profile.d/conda.sh
conda activate atac-seq-pipeline

echo ""
echo "✓ Conda environment activated: atac-seq-pipeline"
echo ""

# 버전 정보 출력
echo "Installed versions:"
echo "  Python: $(python --version 2>&1)"
echo "  Nextflow: $(nextflow -version 2>&1 | grep version)"
echo "  Git: $(git --version)"
echo ""

# Singularity/Apptainer 확인
if command -v apptainer &> /dev/null; then
    echo "  Apptainer: $(apptainer --version)"
elif command -v singularity &> /dev/null; then
    echo "  Singularity: $(singularity --version)"
fi

echo ""
echo "Current directory: $(pwd)"
echo "=========================================="
echo ""
echo "Ready to run ATAC-seq pipeline!"
echo "Run './check_setup.sh' to verify setup."
echo ""
```

**사용법:**

```bash
# 스크립트에 실행 권한 부여
chmod +x activate_pipeline.sh

# 환경 활성화
source activate_pipeline.sh
```

### 6.2 설정 검증

```bash
# Conda 환경이 활성화된 상태에서
cd ~/ngs_pipeline/atac-seq-pipeline

# 설정 검증 스크립트 실행
./check_setup.sh
```

**예상 출력:**

```
==========================================
ATAC-seq Pipeline Setup Checker
==========================================

1. Checking Nextflow...
   ✓ Nextflow found: version 23.10.1

2. Checking container systems...
   ✓ Singularity found: apptainer version 1.4.5

3. Checking template files...
   ✓ samplesheet_template.csv exists
   ✓ params_template.yaml exists

4. Checking .gitignore configuration...
   ✓ .gitignore exists
   ✓ samplesheet.csv is gitignored
   ✓ params.yaml is gitignored

5. Checking Git repository...
   ✓ Git repository initialized
   ✓ Templates are tracked

6. Checking working files...
   ✓ samplesheet.csv exists
   ✓ params.yaml exists

==========================================
✓ Setup looks good! You're ready to run the pipeline.
==========================================
```

---

## 7. 환경 관리

### 7.1 환경 활성화/비활성화

```bash
# 환경 활성화
conda activate atac-seq-pipeline

# 환경 비활성화
conda deactivate

# base 환경으로 돌아감
```

### 7.2 환경 정보 확인

```bash
# 현재 활성화된 환경
conda env list
# 또는
conda info --envs

# 설치된 패키지 목록
conda list

# 특정 패키지 확인
conda list nextflow
```

### 7.3 환경 내보내기/가져오기

**환경 내보내기:**

```bash
# 환경을 YAML 파일로 내보내기
conda activate atac-seq-pipeline
conda env export > environment_exact.yml

# 크로스 플랫폼 호환 버전 (권장)
conda env export --from-history > environment.yml
```

**다른 시스템에서 가져오기:**

```bash
# environment.yml 파일로 환경 생성
conda env create -f environment.yml

# 또는 mamba 사용
mamba env create -f environment.yml
```

### 7.4 환경 업데이트

```bash
# 환경 활성화
conda activate atac-seq-pipeline

# 모든 패키지 업데이트
conda update --all -y

# 특정 패키지 업데이트
conda update nextflow -y

# environment.yml에서 업데이트
conda env update -f environment.yml --prune
```

### 7.5 환경 복제

```bash
# 기존 환경 복제
conda create --name atac-seq-pipeline-backup --clone atac-seq-pipeline

# 확인
conda env list
```

### 7.6 환경 삭제

```bash
# 환경 비활성화 (활성화된 경우)
conda deactivate

# 환경 삭제
conda env remove -n atac-seq-pipeline

# 확인
conda env list
```

---

## 8. 서버별 설정 예시

### 8.1 WSL Ubuntu (개발/테스트)

```bash
# Conda 환경 생성
conda create -n atac-seq-pipeline python=3.10 nextflow git -y

# 환경 활성화
conda activate atac-seq-pipeline

# Repository 설정 (이미 있음)
cd /home/ygkim/ngs_pipeline/atac-seq-pipeline

# 작업 파일 생성
cp samplesheet_template.csv samplesheet.csv
cp params_template.yaml params.yaml

# Docker 사용 (WSL)
# Docker Desktop이 설치되어 있어야 함
```

### 8.2 Linux 서버 (프로덕션)

```bash
# 서버에 로그인
ssh your-server

# Conda 환경 생성
conda create -n atac-seq-pipeline python=3.10 -y
conda activate atac-seq-pipeline

# Nextflow 설치
conda install -c bioconda nextflow -y

# Repository Clone
cd ~/ngs_pipeline
git clone https://github.com/YOUR_USERNAME/atac-seq-pipeline.git
cd atac-seq-pipeline

# 작업 파일 생성
cp samplesheet_template.csv samplesheet.csv
cp params_template.yaml params.yaml

# 서버 환경에 맞게 수정
vim samplesheet.csv
vim params.yaml

# Singularity 사용 (서버)
# 시스템에 이미 설치되어 있어야 함
```

---

## 9. 자동 활성화 설정 (선택사항)

### 9.1 디렉토리 진입 시 자동 활성화

**direnv 사용:**

```bash
# direnv 설치
conda install -c conda-forge direnv -y

# .envrc 파일 생성
cd ~/ngs_pipeline/atac-seq-pipeline
echo 'conda activate atac-seq-pipeline' > .envrc

# 허용
direnv allow

# 이제 디렉토리에 들어가면 자동으로 환경 활성화됨
```

### 9.2 셸 시작 시 자동 활성화

**~/.bashrc에 추가:**

```bash
# ~/.bashrc 편집
nano ~/.bashrc

# 다음 내용 추가:
# Auto-activate atac-seq-pipeline environment
if [[ $PWD == *"atac-seq-pipeline"* ]]; then
    conda activate atac-seq-pipeline 2>/dev/null
fi
```

---

## 10. 트러블슈팅

### 문제 1: "conda: command not found"

```bash
# Conda 경로 확인
ls ~/miniconda3/bin/conda

# 수동으로 초기화
source ~/miniconda3/etc/profile.d/conda.sh

# 또는 ~/.bashrc에 추가
echo 'source ~/miniconda3/etc/profile.d/conda.sh' >> ~/.bashrc
source ~/.bashrc
```

### 문제 2: "PackagesNotFoundError"

```bash
# 채널 설정 확인
conda config --show channels

# 채널 재설정
conda config --add channels conda-forge
conda config --add channels bioconda
conda config --add channels defaults

# 패키지 검색
conda search nextflow
```

### 문제 3: 환경 활성화 실패

```bash
# Conda 초기화
conda init bash
# 또는 zsh 사용 시
conda init zsh

# 터미널 재시작
source ~/.bashrc
```

### 문제 4: Nextflow Java 오류

```bash
# Java 메모리 설정
export NXF_OPTS='-Xms512m -Xmx2g'

# 또는 ~/.bashrc에 추가
echo 'export NXF_OPTS="-Xms512m -Xmx2g"' >> ~/.bashrc
```

### 문제 5: 환경이 느림

```bash
# Mamba 사용 (더 빠른 패키지 해결)
conda install -n base -c conda-forge mamba

# 이후 conda 대신 mamba 사용
mamba install nextflow
mamba update --all
```

---

## 11. 빠른 시작 요약

```bash
# 1. Conda 환경 생성 및 활성화
conda create -n atac-seq-pipeline python=3.10 -y
conda activate atac-seq-pipeline

# 2. 채널 설정
conda config --add channels bioconda
conda config --add channels conda-forge

# 3. Nextflow 및 도구 설치
conda install -c bioconda nextflow -y
conda install -c conda-forge git wget curl -y

# 4. Repository 설정
cd ~/ngs_pipeline
git clone https://github.com/YOUR_USERNAME/atac-seq-pipeline.git
cd atac-seq-pipeline

# 5. 작업 파일 생성
cp samplesheet_template.csv samplesheet.csv
cp params_template.yaml params.yaml

# 6. 검증
./check_setup.sh

# 7. 파이프라인 실행
nextflow run . -profile singularity -params-file params.yaml -resume
```

---

## 12. 참고 자료

- **Conda 공식 문서:** https://docs.conda.io/
- **Mamba 문서:** https://mamba.readthedocs.io/
- **Nextflow 문서:** https://www.nextflow.io/docs/latest/
- **Bioconda:** https://bioconda.github.io/

---

**작성일:** 2026-01-23  
**버전:** 1.0
