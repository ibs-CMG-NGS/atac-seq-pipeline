# 🧬 ATAC-seq Pipeline 설정 가이드

이 저장소에 추가된 파일들과 Git 추적 설정을 정리한 문서입니다.

## 📁 새로 추가된 파일들

### 1. 템플릿 파일 (Git 추적 ✅)

#### `samplesheet_template.csv`
- **용도:** 샘플 정보를 입력하기 위한 템플릿
- **Git 추적:** ✅ YES (템플릿이므로 추적)
- **사용법:**
  ```bash
  cp samplesheet_template.csv samplesheet.csv
  nano samplesheet.csv  # 실제 데이터 경로 입력
  ```

#### `params_template.yaml`
- **용도:** 파이프라인 파라미터 설정 템플릿
- **Git 추적:** ✅ YES (템플릿이므로 추적)
- **사용법:**
  ```bash
  cp params_template.yaml params.yaml
  nano params.yaml  # 실제 분석 설정 입력
  ```

### 2. 작업 파일 (Git 추적 ❌)

#### `samplesheet.csv`
- **용도:** 실제 샘플 정보 (개인 데이터 경로 포함)
- **Git 추적:** ❌ NO (.gitignore에 추가됨)
- **이유:** 프로젝트마다 다른 데이터 경로를 사용하므로

#### `params.yaml`
- **용도:** 실제 분석 파라미터 (프로젝트별 설정)
- **Git 추적:** ❌ NO (.gitignore에 추가됨)
- **이유:** 분석마다 다른 설정을 사용하므로

### 3. 문서 파일 (Git 추적 ✅)

#### `REFERENCE_GENOME_GUIDE.md`
- **용도:** 참조 유전체 준비 상세 가이드
- **내용:**
  - iGenomes 사용법
  - 커스텀 유전체 준비
  - 다운로드 예시 (human, mouse)
  - 인덱스 빌드 방법
  - 트러블슈팅

#### `QUICK_START_KR.md`
- **용도:** 한글 빠른 시작 가이드
- **내용:**
  - 단계별 사용법
  - 실제 사용 시나리오
  - Git 워크플로우
  - 트러블슈팅

#### `check_setup.sh`
- **용도:** 설정 검증 스크립트
- **사용법:**
  ```bash
  ./check_setup.sh
  ```
- **기능:**
  - Nextflow 설치 확인
  - Docker/Singularity 확인
  - 템플릿 파일 존재 확인
  - Git 추적 상태 확인
  - 작업 파일 확인

### 4. 업데이트된 파일

#### `.gitignore`
```gitignore
# Samplesheet files (ignore copies, but track template)
samplesheet.csv
samplesheet_*.csv
!samplesheet_template.csv

# Params files (track template only)
params.yaml
params_*.yaml
!params_template.yaml

# Reference genome files
genome/
references/
*.fa
*.fasta
*.gtf
...
```

#### `README.md`
- Quick Start Guide 섹션 추가
- 새 문서들에 대한 링크 추가

---

## 🚀 빠른 시작

### 1. 설정 검증
```bash
cd /home/ygkim/ngs_pipeline/atac-seq-pipeline
./check_setup.sh
```

### 2. 템플릿 복사
```bash
cp samplesheet_template.csv samplesheet.csv
cp params_template.yaml params.yaml
```

### 3. 설정 파일 편집
```bash
nano samplesheet.csv  # 샘플 정보 입력
nano params.yaml      # 분석 파라미터 설정
```

### 4. 테스트 실행
```bash
# WSL Ubuntu에서
nextflow run nf-core/atacseq -profile test,docker --outdir test_results
```

### 5. 실제 분석 실행
```bash
# WSL Ubuntu (테스트)
nextflow run . -profile docker -params-file params.yaml -resume

# 서버 (프로덕션)
nohup nextflow run . -profile singularity -params-file params.yaml -resume > pipeline.log 2>&1 &
```

---

## 🔄 Git 워크플로우

### 초기 설정

```bash
# Git 상태 확인
git status

# 새 파일들 추가 (템플릿과 문서만)
git add samplesheet_template.csv
git add params_template.yaml
git add REFERENCE_GENOME_GUIDE.md
git add QUICK_START_KR.md
git add README_SETUP.md
git add check_setup.sh
git add .gitignore
git add README.md

# 커밋
git commit -m "Add pipeline templates and documentation

- Add samplesheet_template.csv for sample configuration
- Add params_template.yaml for pipeline parameters
- Add comprehensive reference genome guide
- Add Korean quick start guide
- Add setup verification script
- Update .gitignore to exclude working files
- Update README with quick start section
"

# GitHub에 푸시
git push origin main
```

### 일반적인 작업 흐름

**개발/테스트 환경 (WSL Ubuntu):**
```bash
# 1. 최신 버전 받기
git pull origin main

# 2. 작업 파일 생성 (Git에서 제외됨)
cp samplesheet_template.csv samplesheet.csv
cp params_template.yaml params.yaml

# 3. 편집 및 테스트
nano samplesheet.csv
nano params.yaml
nextflow run . -profile test,docker --outdir test

# 4. 템플릿 수정한 경우에만 커밋
git add samplesheet_template.csv  # 템플릿만
git commit -m "Update template"
git push origin main

# 5. samplesheet.csv, params.yaml은 자동으로 제외됨
```

**프로덕션 환경 (서버):**
```bash
# 1. 동기화
cd /path/to/atac-seq-pipeline
git pull origin main

# 2. 작업 파일 생성
cp samplesheet_template.csv samplesheet.csv
cp params_template.yaml params.yaml

# 3. 편집
vim samplesheet.csv
vim params.yaml

# 4. 실행
nohup nextflow run . -profile singularity -params-file params.yaml -resume > pipeline.log 2>&1 &
```

---

## 📊 Git 추적 상태 요약

### ✅ Git에 추적되는 파일
```
atac-seq-pipeline/
├── samplesheet_template.csv     ✅ 템플릿
├── params_template.yaml          ✅ 템플릿
├── REFERENCE_GENOME_GUIDE.md     ✅ 문서
├── QUICK_START_KR.md             ✅ 문서
├── README_SETUP.md               ✅ 문서
├── check_setup.sh                ✅ 스크립트
├── README.md                     ✅ 메인 문서
├── .gitignore                    ✅ Git 설정
├── main.nf                       ✅ 파이프라인 코드
├── nextflow.config               ✅ 설정
└── ...                           ✅ 기타 파이프라인 파일들
```

### ❌ Git에서 제외되는 파일
```
atac-seq-pipeline/
├── samplesheet.csv               ❌ 작업 파일 (개인 데이터 경로)
├── params.yaml                   ❌ 작업 파일 (프로젝트별 설정)
├── samplesheet_project1.csv      ❌ 복사본들
├── params_project1.yaml          ❌ 복사본들
├── results/                      ❌ 분석 결과
├── work/                         ❌ Nextflow 임시 파일
├── .nextflow/                    ❌ Nextflow 메타데이터
├── .nextflow.log                 ❌ 로그 파일
├── pipeline.log                  ❌ 실행 로그
└── genome/                       ❌ 참조 유전체 파일들
```

---

## 💡 사용 시나리오 예시

### 시나리오 1: 새 프로젝트 시작

```bash
# 1. 저장소 클론
git clone https://github.com/your-username/atac-seq-pipeline.git
cd atac-seq-pipeline

# 2. 설정 확인
./check_setup.sh

# 3. 프로젝트별 설정 파일 생성
cp samplesheet_template.csv samplesheet_cardiac.csv
cp params_template.yaml params_cardiac.yaml

# 4. 편집
nano samplesheet_cardiac.csv
nano params_cardiac.yaml

# 5. 실행
nextflow run . -profile docker -params-file params_cardiac.yaml
```

### 시나리오 2: 여러 프로젝트 관리

```bash
atac-seq-pipeline/
├── samplesheet_template.csv      # Git 추적 ✅
├── params_template.yaml           # Git 추적 ✅
├── samplesheet_project_A.csv      # Git 무시 ❌
├── params_project_A.yaml          # Git 무시 ❌
├── samplesheet_project_B.csv      # Git 무시 ❌
├── params_project_B.yaml          # Git 무시 ❌
└── results_project_A/             # Git 무시 ❌
└── results_project_B/             # Git 무시 ❌
```

**실행:**
```bash
# Project A
nextflow run . -profile docker -params-file params_project_A.yaml --outdir results_project_A

# Project B
nextflow run . -profile docker -params-file params_project_B.yaml --outdir results_project_B
```

### 시나리오 3: 서버와 동기화

**WSL Ubuntu (로컬):**
```bash
# 템플릿 업데이트
nano samplesheet_template.csv
git add samplesheet_template.csv
git commit -m "Add more examples to template"
git push origin main
```

**서버:**
```bash
# 업데이트 받기
git pull origin main

# 최신 템플릿 사용
cp samplesheet_template.csv samplesheet.csv
vim samplesheet.csv  # 서버 경로로 수정
```

---

## 🔍 검증 방법

### Git 추적 상태 확인
```bash
# 추적되는 파일 확인
git ls-files | grep -E "(samplesheet|params)"

# 출력 예상:
# samplesheet_template.csv  ✓
# params_template.yaml      ✓

# 추적되지 않는 파일 확인 (.gitignore 적용)
git status --ignored | grep -E "(samplesheet|params)"

# 출력 예상:
# samplesheet.csv           (ignored)
# params.yaml               (ignored)
```

### 설정 파일 유효성 확인
```bash
# Samplesheet 검증 (Python 스크립트 사용)
python bin/check_samplesheet.py samplesheet.csv

# Params 문법 확인 (YAML)
python -c "import yaml; yaml.safe_load(open('params.yaml'))"

# Nextflow 문법 확인
nextflow run . --help
```

---

## 📚 추가 문서

- **[REFERENCE_GENOME_GUIDE.md](REFERENCE_GENOME_GUIDE.md)** - 참조 유전체 준비 상세 가이드
- **[QUICK_START_KR.md](QUICK_START_KR.md)** - 한글 빠른 시작 가이드
- **[docs/usage.md](docs/usage.md)** - nf-core 공식 사용법
- **[docs/output.md](docs/output.md)** - 출력 파일 설명

---

## ❓ FAQ

**Q: samplesheet.csv를 실수로 Git에 추가했어요!**
```bash
# Git에서 제거 (파일은 유지)
git rm --cached samplesheet.csv
git commit -m "Remove samplesheet.csv from Git tracking"

# .gitignore가 제대로 설정되어 있는지 확인
cat .gitignore | grep samplesheet.csv
```

**Q: 템플릿을 수정하면 어떻게 하나요?**
```bash
# 템플릿만 수정하고 커밋
nano samplesheet_template.csv
git add samplesheet_template.csv
git commit -m "Update samplesheet template with new examples"
git push origin main

# 작업 파일은 자동으로 제외됨
```

**Q: 여러 사람과 협업할 때는?**
```bash
# 각자 자신의 작업 파일 사용
# Person A
cp samplesheet_template.csv samplesheet_personA.csv

# Person B  
cp samplesheet_template.csv samplesheet_personB.csv

# 둘 다 Git에서 자동으로 제외됨 (samplesheet_*.csv 패턴)
```

---

**작성일:** 2026-01-23  
**작성자:** Pipeline Setup Documentation
