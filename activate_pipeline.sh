#!/bin/bash
# ATAC-seq Pipeline 환경 활성화 스크립트
# Usage: source activate_pipeline.sh

echo "=========================================="
echo "  ATAC-seq Pipeline Environment Setup"
echo "=========================================="
echo ""

# Conda 초기화 확인
if ! command -v conda &> /dev/null; then
    echo "❌ Error: Conda not found!"
    echo "   Please install Miniconda or Anaconda first."
    echo "   Visit: https://docs.conda.io/en/latest/miniconda.html"
    return 1
fi

# Conda 환경 초기화
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"

# 환경 존재 여부 확인
ENV_NAME="atac-seq-pipeline"
if conda env list | grep -q "^${ENV_NAME} "; then
    # 환경이 존재하면 활성화
    conda activate "$ENV_NAME"
    
    if [ $? -eq 0 ]; then
        echo "✅ Conda environment activated: ${ENV_NAME}"
    else
        echo "❌ Failed to activate environment: ${ENV_NAME}"
        return 1
    fi
else
    # 환경이 없으면 생성 여부 확인
    echo "⚠️  Environment '${ENV_NAME}' not found."
    echo ""
    read -p "Would you like to create it now? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Creating conda environment..."
        
        # environment.yml 파일 확인
        if [ -f "environment.yml" ]; then
            echo "Using environment.yml file..."
            conda env create -f environment.yml
        else
            echo "Creating basic environment..."
            conda create -n "$ENV_NAME" python=3.10 nextflow git -y
        fi
        
        if [ $? -eq 0 ]; then
            conda activate "$ENV_NAME"
            echo "✅ Environment created and activated!"
        else
            echo "❌ Failed to create environment"
            return 1
        fi
    else
        echo "Skipping environment creation."
        return 1
    fi
fi

echo ""
echo "=========================================="
echo "  Installed Versions"
echo "=========================================="

# Python 버전
if command -v python &> /dev/null; then
    echo "Python:    $(python --version 2>&1 | awk '{print $2}')"
fi

# Nextflow 버전
if command -v nextflow &> /dev/null; then
    NXF_VERSION=$(nextflow -version 2>&1 | grep "version" | head -n1 | awk '{print $2}')
    echo "Nextflow:  ${NXF_VERSION}"
else
    echo "Nextflow:  ⚠️  Not installed (run: conda install -c bioconda nextflow)"
fi

# Git 버전
if command -v git &> /dev/null; then
    echo "Git:       $(git --version | awk '{print $3}')"
fi

# Singularity/Apptainer
if command -v apptainer &> /dev/null; then
    echo "Apptainer: $(apptainer --version | awk '{print $3}')"
elif command -v singularity &> /dev/null; then
    echo "Singularity: $(singularity --version 2>&1)"
fi

# Docker (시스템 레벨)
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    echo "Docker:    ${DOCKER_VERSION}"
fi

echo "=========================================="
echo ""

# 현재 디렉토리 확인
CURRENT_DIR=$(pwd)
echo "Current directory: ${CURRENT_DIR}"

# 파이프라인 디렉토리인지 확인
if [ -f "main.nf" ] && [ -f "nextflow.config" ]; then
    echo "✅ You are in the pipeline directory"
    echo ""
    echo "Quick start:"
    echo "  1. Check setup: ./check_setup.sh"
    echo "  2. Edit files:  nano samplesheet.csv"
    echo "  3. Run test:    nextflow run . -profile test,singularity --outdir test_results"
elif [ -f "check_setup.sh" ]; then
    echo "✅ Setup files found"
    echo ""
    echo "Run: ./check_setup.sh"
else
    echo "⚠️  Not in pipeline directory"
    echo ""
    echo "Navigate to: cd ~/ngs_pipeline/atac-seq-pipeline"
fi

echo "=========================================="
echo ""

# 환경 변수 설정 (선택사항)
# Nextflow Java 메모리 설정
export NXF_OPTS="${NXF_OPTS:--Xms1g -Xmx4g}"

# Singularity 캐시 디렉토리 (필요시 수정)
# export NXF_SINGULARITY_CACHEDIR="${HOME}/.singularity/cache"

echo "💡 Tip: To deactivate this environment, run: conda deactivate"
echo ""
