#!/bin/bash

# ATAC-seq Pipeline Setup Verification Script
# This script helps verify your setup before running the pipeline

echo "=========================================="
echo "ATAC-seq Pipeline Setup Checker"
echo "=========================================="
echo ""

# Check Nextflow installation
echo "1. Checking Nextflow..."
if command -v nextflow &> /dev/null; then
    NXF_VERSION=$(nextflow -version 2>&1 | head -n1)
    echo "   ✓ Nextflow found: $NXF_VERSION"
else
    echo "   ✗ Nextflow not found. Please install from: https://www.nextflow.io/"
fi
echo ""

# Check Docker/Singularity
echo "2. Checking container systems..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "   ✓ Docker found: $DOCKER_VERSION"
else
    echo "   ⚠ Docker not found"
fi

if command -v singularity &> /dev/null; then
    SING_VERSION=$(singularity --version)
    echo "   ✓ Singularity found: $SING_VERSION"
else
    echo "   ⚠ Singularity not found"
fi
echo ""

# Check required files
echo "3. Checking template files..."
if [ -f "samplesheet_template.csv" ]; then
    echo "   ✓ samplesheet_template.csv exists"
else
    echo "   ✗ samplesheet_template.csv not found"
fi

if [ -f "params_template.yaml" ]; then
    echo "   ✓ params_template.yaml exists"
else
    echo "   ✗ params_template.yaml not found"
fi
echo ""

# Check if working files are properly gitignored
echo "4. Checking .gitignore configuration..."
if [ -f ".gitignore" ]; then
    echo "   ✓ .gitignore exists"
    
    if grep -q "samplesheet.csv" .gitignore; then
        echo "   ✓ samplesheet.csv is gitignored"
    else
        echo "   ⚠ samplesheet.csv should be added to .gitignore"
    fi
    
    if grep -q "params.yaml" .gitignore; then
        echo "   ✓ params.yaml is gitignored"
    else
        echo "   ⚠ params.yaml should be added to .gitignore"
    fi
    
    if grep -q "!samplesheet_template.csv" .gitignore; then
        echo "   ✓ samplesheet_template.csv is tracked"
    else
        echo "   ⚠ samplesheet_template.csv should be tracked"
    fi
else
    echo "   ✗ .gitignore not found"
fi
echo ""

# Check Git status
echo "5. Checking Git repository..."
if [ -d ".git" ]; then
    echo "   ✓ Git repository initialized"
    
    # Check if templates are tracked
    if git ls-files | grep -q "samplesheet_template.csv"; then
        echo "   ✓ samplesheet_template.csv is tracked by Git"
    else
        echo "   ⚠ samplesheet_template.csv is not tracked. Run: git add samplesheet_template.csv"
    fi
    
    if git ls-files | grep -q "params_template.yaml"; then
        echo "   ✓ params_template.yaml is tracked by Git"
    else
        echo "   ⚠ params_template.yaml is not tracked. Run: git add params_template.yaml"
    fi
    
    # Check if working files are not tracked
    if git ls-files | grep -q "^samplesheet.csv$"; then
        echo "   ⚠ WARNING: samplesheet.csv is tracked but should be ignored!"
    else
        echo "   ✓ samplesheet.csv is not tracked (correct)"
    fi
    
    if git ls-files | grep -q "^params.yaml$"; then
        echo "   ⚠ WARNING: params.yaml is tracked but should be ignored!"
    else
        echo "   ✓ params.yaml is not tracked (correct)"
    fi
else
    echo "   ⚠ Not a Git repository"
fi
echo ""

# Check for actual working files
echo "6. Checking working files..."
if [ -f "samplesheet.csv" ]; then
    echo "   ✓ samplesheet.csv exists (working file)"
    SAMPLE_COUNT=$(grep -v "^#" samplesheet.csv | grep -v "^sample," | grep -c ".")
    echo "     → $SAMPLE_COUNT samples found"
else
    echo "   ⚠ samplesheet.csv not found. Copy from template: cp samplesheet_template.csv samplesheet.csv"
fi

if [ -f "params.yaml" ]; then
    echo "   ✓ params.yaml exists (working file)"
    if grep -q "^genome:" params.yaml; then
        GENOME=$(grep "^genome:" params.yaml | head -n1)
        echo "     → $GENOME"
    fi
else
    echo "   ⚠ params.yaml not found. Copy from template: cp params_template.yaml params.yaml"
fi
echo ""

# Summary
echo "=========================================="
echo "Setup Status Summary"
echo "=========================================="

# Count checks
PASSED=0
FAILED=0

if command -v nextflow &> /dev/null; then ((PASSED++)); else ((FAILED++)); fi
if [ -f "samplesheet_template.csv" ]; then ((PASSED++)); else ((FAILED++)); fi
if [ -f "params_template.yaml" ]; then ((PASSED++)); else ((FAILED++)); fi
if [ -f ".gitignore" ]; then ((PASSED++)); else ((FAILED++)); fi

echo "Checks passed: $PASSED"
echo "Issues found: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✓ Setup looks good! You're ready to run the pipeline."
    echo ""
    echo "Next steps:"
    echo "  1. Copy templates: cp samplesheet_template.csv samplesheet.csv"
    echo "  2. Copy templates: cp params_template.yaml params.yaml"
    echo "  3. Edit your samplesheet.csv and params.yaml"
    echo "  4. Test run: nextflow run nf-core/atacseq -profile test,docker --outdir test_results"
else
    echo "⚠ Please fix the issues above before running the pipeline."
fi

echo "=========================================="
