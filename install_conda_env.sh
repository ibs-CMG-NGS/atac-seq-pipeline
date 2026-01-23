#!/bin/bash
# ATAC-seq Pipeline 빠른 설치 스크립트
# This script sets up the complete conda environment for ATAC-seq pipeline

set -e  # Exit on error

echo "=========================================="
echo "  ATAC-seq Pipeline Quick Setup"
echo "=========================================="
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수: 성공 메시지
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# 함수: 경고 메시지
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 함수: 에러 메시지
error() {
    echo -e "${RED}✗${NC} $1"
}

# 1. Conda 확인
echo "Step 1: Checking Conda installation..."
if ! command -v conda &> /dev/null; then
    error "Conda not found!"
    echo ""
    echo "Please install Miniconda first:"
    echo "  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    echo "  bash Miniconda3-latest-Linux-x86_64.sh"
    echo ""
    exit 1
else
    CONDA_VERSION=$(conda --version)
    success "Conda found: ${CONDA_VERSION}"
fi
echo ""

# Conda 초기화
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"

# 2. 환경 생성 확인
ENV_NAME="atac-seq-pipeline"
echo "Step 2: Checking if environment exists..."

if conda env list | grep -q "^${ENV_NAME} "; then
    warning "Environment '${ENV_NAME}' already exists"
    echo ""
    read -p "Remove and recreate? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing environment..."
        conda deactivate 2>/dev/null || true
        conda env remove -n "$ENV_NAME" -y
        success "Environment removed"
    else
        echo "Keeping existing environment"
        conda activate "$ENV_NAME"
        success "Environment activated"
        echo ""
        echo "Run this script again to update packages or skip to verification."
        exit 0
    fi
fi
echo ""

# 3. 환경 생성 방법 선택
echo "Step 3: Creating conda environment..."
echo ""
echo "Choose installation method:"
echo "  1) Full installation (with bioinformatics tools, ~2GB)"
echo "  2) Minimal installation (Nextflow + essentials, ~500MB)"
echo "  3) Use environment.yml file (if available)"
echo ""
read -p "Enter choice (1/2/3): " -n 1 -r
echo ""
echo ""

case $REPLY in
    1)
        echo "Installing full environment..."
        if [ -f "environment.yml" ]; then
            conda env create -f environment.yml
        else
            conda create -n "$ENV_NAME" python=3.10 -y
            conda activate "$ENV_NAME"
            
            # Add channels
            conda config --env --add channels defaults
            conda config --env --add channels bioconda
            conda config --env --add channels conda-forge
            
            # Install packages
            conda install -y \
                nextflow \
                git wget curl \
                pandas numpy matplotlib seaborn pyyaml \
                jupyter ipython \
                samtools bedtools deeptools fastqc multiqc \
                pigz parallel
        fi
        ;;
    2)
        echo "Installing minimal environment..."
        conda create -n "$ENV_NAME" python=3.10 -y
        conda activate "$ENV_NAME"
        
        # Add channels
        conda config --env --add channels defaults
        conda config --env --add channels bioconda
        conda config --env --add channels conda-forge
        
        # Install essential packages only
        conda install -y \
            nextflow \
            git wget curl \
            pandas pyyaml
        ;;
    3)
        if [ -f "environment.yml" ]; then
            echo "Using environment.yml..."
            conda env create -f environment.yml
        else
            error "environment.yml not found!"
            exit 1
        fi
        ;;
    *)
        error "Invalid choice"
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    success "Environment created successfully"
else
    error "Failed to create environment"
    exit 1
fi

echo ""

# 4. 환경 활성화
echo "Step 4: Activating environment..."
conda activate "$ENV_NAME"
success "Environment activated"
echo ""

# 5. 환경 정보 출력
echo "Step 5: Verifying installation..."
echo "=========================================="
echo "  Installed Versions"
echo "=========================================="

python --version 2>&1 | sed 's/^/  /'

if command -v nextflow &> /dev/null; then
    nextflow -version 2>&1 | grep version | head -n1 | sed 's/^/  /'
else
    error "  Nextflow not found!"
fi

git --version 2>&1 | sed 's/^/  /'

echo "=========================================="
echo ""

# 6. 환경 내보내기
echo "Step 6: Exporting environment specification..."
conda env export --from-history > environment_installed.yml
success "Environment exported to: environment_installed.yml"
echo ""

# 7. 설정 파일 확인
echo "Step 7: Checking pipeline files..."
if [ -f "main.nf" ]; then
    success "main.nf found"
else
    warning "main.nf not found (you may need to clone the repository)"
fi

if [ -f "check_setup.sh" ]; then
    success "check_setup.sh found"
    chmod +x check_setup.sh
else
    warning "check_setup.sh not found"
fi

if [ -f "activate_pipeline.sh" ]; then
    success "activate_pipeline.sh found"
    chmod +x activate_pipeline.sh
else
    warning "activate_pipeline.sh not found"
fi
echo ""

# 8. 최종 안내
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Activate environment (in future sessions):"
echo "   ${GREEN}source activate_pipeline.sh${NC}"
echo "   or"
echo "   ${GREEN}conda activate ${ENV_NAME}${NC}"
echo ""
echo "2. Verify setup:"
echo "   ${GREEN}./check_setup.sh${NC}"
echo ""
echo "3. Prepare your analysis:"
echo "   ${GREEN}cp samplesheet_template.csv samplesheet.csv${NC}"
echo "   ${GREEN}cp params_template.yaml params.yaml${NC}"
echo "   Edit these files with your data"
echo ""
echo "4. Run test pipeline:"
echo "   ${GREEN}nextflow run . -profile test,singularity --outdir test_results${NC}"
echo ""
echo "=========================================="
echo ""

# 셸 설정 파일에 추가 제안
echo "💡 Tip: Add activation to your ~/.bashrc:"
echo "   echo 'alias activate-atac=\"source ~/ngs_pipeline/atac-seq-pipeline/activate_pipeline.sh\"' >> ~/.bashrc"
echo ""

# 환경이 활성화된 상태 유지를 위한 메시지
echo "Note: The environment is now active in this session."
echo "To keep it active, run: ${GREEN}conda activate ${ENV_NAME}${NC}"
echo ""
