# ATAC-seq 파이프라인 빠른 시작 가이드 (한글)

## 📋 개요

이 가이드는 nf-core/atacseq 파이프라인을 Windows WSL Ubuntu와 Linux 서버에서 사용하는 방법을 설명합니다.

---

## 🚀 빠른 시작

### 1단계: 샘플시트 준비

```bash
# 템플릿 복사
cp samplesheet_template.csv samplesheet.csv

# 편집기로 열기
nano samplesheet.csv
# 또는
vim samplesheet.csv
```

**예시 내용:**
```csv
sample,fastq_1,fastq_2,replicate
WT,/data/fastq/WT_rep1_R1.fastq.gz,/data/fastq/WT_rep1_R2.fastq.gz,1
WT,/data/fastq/WT_rep2_R1.fastq.gz,/data/fastq/WT_rep2_R2.fastq.gz,2
KO,/data/fastq/KO_rep1_R1.fastq.gz,/data/fastq/KO_rep1_R2.fastq.gz,1
KO,/data/fastq/KO_rep2_R1.fastq.gz,/data/fastq/KO_rep2_R2.fastq.gz,2
```

**주의사항:**
- 절대 경로 또는 상대 경로 사용
- FASTQ 파일은 반드시 gzip 압축 (`.fastq.gz` 또는 `.fq.gz`)
- Replicate 번호는 1부터 시작
- Single-end 데이터는 `fastq_2` 컬럼을 비워둠

### 2단계: 파라미터 파일 설정

```bash
# 템플릿 복사
cp params_template.yaml params.yaml

# 편집
nano params.yaml
```

**최소 설정 예시:**
```yaml
input: './samplesheet.csv'
outdir: './results'
genome: 'GRCh38'
read_length: 150
aligner: 'bwa'
```

**커스텀 유전체 사용 예시:**
```yaml
input: './samplesheet.csv'
outdir: './results'
genome: null
fasta: '/data/genomes/hg38/genome.fa'
gtf: '/data/genomes/hg38/genes.gtf'
blacklist: '/data/genomes/hg38/blacklist.bed'
mito_name: 'chrM'
read_length: 150
aligner: 'bwa'
```

### 3단계: 컨테이너 시스템 확인 ⚠️ 필수

**서버에서 실행 전 반드시 확인:**

```bash
# Apptainer 확인 (권장)
apptainer --version

# 또는 Docker 확인
docker --version
```

**Apptainer가 설치되지 않은 경우:**

```bash
# Ubuntu/Debian (관리자 권한 필요)
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:apptainer/ppa
sudo apt update
sudo apt install -y apptainer

# 설치 확인
apptainer --version
```

**컨테이너 시스템이 없는 경우 (대안):**

```bash
# Conda 프로파일 사용 (느리지만 작동함)
nextflow run nf-core/atacseq \
  -profile conda \
  -params-file params.yaml
```

### 4단계: 테스트 실행 (WSL Ubuntu)

```bash
# 파이프라인 문법 확인
nextflow run . --help

# 작은 테스트 데이터로 파이프라인 검증
nextflow run nf-core/atacseq \
  -profile test,docker \
  --outdir test_results

# 성공하면 실제 데이터로 dry-run
nextflow run . \
  -profile docker \
  -params-file params.yaml \
  --outdir test_run \
  -resume
```

### 5단계: 프로덕션 실행 (서버)

```bash
# 서버에서 실행
nextflow run /path/to/atac-seq-pipeline \
  -profile singularity \
  -params-file params.yaml \
  -resume

# 백그라운드 실행
nohup nextflow run /path/to/atac-seq-pipeline \
  -profile singularity \
  -params-file params.yaml \
  -resume > pipeline.log 2>&1 &

# 로그 확인
tail -f pipeline.log
```

---

## 📁 디렉토리 구조

### 권장 프로젝트 구조
```
your_project/
├── samplesheet.csv              # 실제 샘플 정보 (git에서 제외)
├── params.yaml                  # 실제 파라미터 (git에서 제외)
├── raw_data/                    # FASTQ 파일들
│   ├── sample1_R1.fastq.gz
│   ├── sample1_R2.fastq.gz
│   └── ...
├── results/                     # 분석 결과 (git에서 제외)
│   ├── multiqc/
│   ├── bwa/
│   └── ...
├── work/                        # Nextflow 임시 파일 (git에서 제외)
└── pipeline.log                 # 실행 로그
```

### Git 추적 파일
- ✅ `samplesheet_template.csv` (템플릿만 추적)
- ✅ `params_template.yaml` (템플릿만 추적)
- ✅ 파이프라인 설정 파일들
- ❌ `samplesheet.csv` (실제 데이터 경로 포함, 제외)
- ❌ `params.yaml` (실제 설정, 제외)
- ❌ `results/`, `work/` (결과물, 제외)

---

## 🔧 일반적인 사용 시나리오

### 시나리오 1: 표준 human ATAC-seq (paired-end)

**samplesheet.csv:**
```csv
sample,fastq_1,fastq_2,replicate
DMSO,/data/DMSO_rep1_R1.fq.gz,/data/DMSO_rep1_R2.fq.gz,1
DMSO,/data/DMSO_rep2_R1.fq.gz,/data/DMSO_rep2_R2.fq.gz,2
Drug,/data/Drug_rep1_R1.fq.gz,/data/Drug_rep1_R2.fq.gz,1
Drug,/data/Drug_rep2_R1.fq.gz,/data/Drug_rep2_R2.fq.gz,2
```

**params.yaml:**
```yaml
input: './samplesheet.csv'
outdir: './results_human_atac'
genome: 'GRCh38'
read_length: 150
aligner: 'bwa'
narrow_peak: false
keep_dups: false
keep_mito: false
skip_deseq2_qc: false
```

**실행:**
```bash
nextflow run nf-core/atacseq -profile docker -params-file params.yaml
```

### 시나리오 2: Mouse ATAC-seq (single-end)

**samplesheet.csv:**
```csv
sample,fastq_1,fastq_2,replicate
Control,/data/ctrl_rep1.fq.gz,,1
Control,/data/ctrl_rep2.fq.gz,,2
Treated,/data/treat_rep1.fq.gz,,1
Treated,/data/treat_rep2.fq.gz,,2
```

**params.yaml:**
```yaml
input: './samplesheet.csv'
outdir: './results_mouse_atac'
genome: 'GRCm39'
read_length: 75
aligner: 'bwa'
```

### 시나리오 3: Control 샘플 포함 (peak calling)

**samplesheet.csv:**
```csv
sample,fastq_1,fastq_2,replicate,control,control_replicate
Input,/data/input_rep1_R1.fq.gz,/data/input_rep1_R2.fq.gz,1,,
Input,/data/input_rep2_R1.fq.gz,/data/input_rep2_R2.fq.gz,2,,
ChIP,/data/chip_rep1_R1.fq.gz,/data/chip_rep1_R2.fq.gz,1,Input,1
ChIP,/data/chip_rep2_R1.fq.gz,/data/chip_rep2_R2.fq.gz,2,Input,2
```

**params.yaml:**
```yaml
input: './samplesheet.csv'
outdir: './results_with_control'
genome: 'GRCh38'
read_length: 150
with_control: true
aligner: 'bwa'
```

### 시나리오 4: 커스텀 유전체 (비모델 생물)

**params.yaml:**
```yaml
input: './samplesheet.csv'
outdir: './results_custom'
genome: null
fasta: '/data/genomes/my_organism/genome.fa'
gtf: '/data/genomes/my_organism/genes.gtf'
mito_name: 'MT'
macs_gsize: '1.2e9'
read_length: 150
aligner: 'bwa'
save_reference: true  # 인덱스 저장
```

---

## 🔄 Git 워크플로우

### 초기 설정 (한 번만)

```bash
# 저장소 초기화 (아직 안 했다면)
cd /home/ygkim/ngs_pipeline/atac-seq-pipeline
git init
git remote add origin https://github.com/your-username/atac-seq-pipeline.git

# 템플릿 파일 추가
git add samplesheet_template.csv
git add params_template.yaml
git add REFERENCE_GENOME_GUIDE.md
git add QUICK_START_KR.md
git add .gitignore
git commit -m "Add template files and documentation"
git push -u origin main
```

### 일반적인 워크플로우

**WSL Ubuntu에서 (개발/테스트):**
```bash
# 1. 최신 코드 받기
git pull origin main

# 2. 설정 파일 작성
cp samplesheet_template.csv samplesheet.csv
cp params_template.yaml params.yaml
nano samplesheet.csv
nano params.yaml

# 3. 테스트 실행
nextflow run . -profile test,docker --outdir test_out

# 4. 템플릿이나 문서 수정한 경우 커밋
git add samplesheet_template.csv params_template.yaml
git commit -m "Update templates"
git push origin main
```

**서버에서 (프로덕션):**
```bash
# 1. 최신 코드 동기화
cd /path/to/atac-seq-pipeline
git pull origin main

# 2. 설정 파일 작성 (서버용)
cp samplesheet_template.csv samplesheet.csv
cp params_template.yaml params.yaml
nano samplesheet.csv
nano params.yaml

# 3. 실제 분석 실행
nohup nextflow run . \
  -profile singularity \
  -params-file params.yaml \
  -resume > pipeline.log 2>&1 &

# 4. 진행 상황 모니터링
tail -f pipeline.log
```

---

## 🔗 GitHub 저장소 연결

### 저장소 생성

1. https://github.com 에서 `+` → `New repository`
2. 저장소 정보 입력:
   - **Repository name:** `atac-seq-pipeline`
   - **Visibility:** Private 또는 Public
   - ⚠️ "Initialize this repository with a README" **체크 해제** (이미 있음)
   - ⚠️ `.gitignore` / `license` 추가 **하지 않음** (이미 있음)
3. `Create repository` 클릭 후 표시되는 명령어 실행:

```bash
cd /home/ygkim/ngs_pipeline/atac-seq-pipeline
git remote add origin https://github.com/YOUR_USERNAME/atac-seq-pipeline.git
git push -u origin main
```

### 인증 설정

**방법 A: Personal Access Token (권장)**

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. `Generate new token` → `repo` 권한 체크 → 토큰 복사
3. `git push` 시 비밀번호 대신 토큰 입력

**방법 B: SSH Key**

```bash
# SSH 키 생성
ssh-keygen -t ed25519 -C "your_email@example.com"

# 공개키 확인 후 GitHub Settings → SSH and GPG keys에 등록
cat ~/.ssh/id_ed25519.pub

# 원격 URL을 SSH로 변경
git remote set-url origin git@github.com:YOUR_USERNAME/atac-seq-pipeline.git
```

### Git 추적 파일 확인

```bash
# 추적되는 파일 확인 (템플릿만 나와야 정상)
git ls-files | grep -E "(samplesheet|params)"
# 기대 출력:
# samplesheet_template.csv
# params_template.yaml

# .gitignore 적용 확인 (작업 파일이 ignored로 표시되어야 정상)
git status --ignored | grep -E "(samplesheet|params)"
```

### Git 명령어 빠른 참고

```bash
git status                    # 현재 상태
git diff                      # 변경사항 확인
git log --oneline             # 커밋 이력
git branch -a                 # 브랜치 목록
git remote -v                 # 원격 저장소 확인
git restore filename          # 변경사항 취소 (unstaged)
git restore --staged filename # 변경사항 취소 (staged)
git pull origin main --rebase # 원격 변경사항 가져오기 (충돌 최소화)
```

---

## 📊 결과 확인

### 주요 결과 파일

```bash
results/
├── multiqc/
│   └── multiqc_report.html          # ⭐ 가장 중요! 전체 QC 요약
├── bwa/                              # aligner 이름에 따라 다름
│   ├── merged_library/
│   │   ├── *.mLb.clN.bam            # 최종 필터링된 BAM
│   │   ├── bigwig/*.bigWig          # IGV 시각화용
│   │   ├── macs2/
│   │   │   └── *_peaks.{narrowPeak|broadPeak}  # Peak 파일
│   │   ├── macs2/consensus/
│   │   │   └── consensus_peaks.bed  # Consensus peaks
│   │   └── deseq2/
│   │       ├── *.results.txt        # Differential accessibility
│   │       └── *.pca.pdf            # PCA plot
│   └── merged_replicate/
│       └── macs2/
│           └── *_peaks.{narrowPeak|broadPeak}
├── fastqc/                           # Raw read QC
├── trimgalore/                       # Trimmed read QC
└── pipeline_info/                    # 파이프라인 실행 정보
```

### 결과 확인 순서

1. **MultiQC 리포트** (`multiqc/multiqc_report.html`)
   - 브라우저로 열어서 전체 QC 확인
   - Read quality, alignment rate, peak 수 등 확인

2. **Peak 파일** 확인
   ```bash
   # Peak 개수 확인
   wc -l results/bwa/merged_library/macs2/*_peaks.narrowPeak
   
   # Consensus peaks 확인
   head results/bwa/merged_library/macs2/consensus/consensus_peaks.bed
   ```

3. **Differential accessibility** 결과
   ```bash
   # DESeq2 결과 확인
   head results/bwa/merged_library/deseq2/*.results.txt
   ```

4. **IGV로 시각화**
   - `results/bwa/merged_library/igv/igv_session.xml` 열기
   - BigWig 파일과 peak 파일 함께 확인

---

## 🐛 트러블슈팅

### 문제 1: "No such file or directory" 에러

**원인:** samplesheet.csv의 파일 경로가 잘못됨

**해결:**
```bash
# 경로 확인
ls -lh /path/to/your/file.fastq.gz

# 절대 경로 사용 권장
realpath your_file.fastq.gz
```

### 문제 2: 메모리 부족 에러

**해결:** params.yaml에서 리소스 줄이기
```yaml
max_memory: '64.GB'
max_cpus: 8
```

### 문제 3: Docker/Singularity 권한 에러

**Docker (WSL):**
```bash
sudo usermod -aG docker $USER
# 로그아웃 후 재로그인
```

**Singularity (서버):**
```bash
# 캐시 디렉토리 권한 확인
export NXF_SINGULARITY_CACHEDIR="/path/to/writable/cache"
```

### 문제 4: Pipeline 중단 후 재시작

**해결:**
```bash
# -resume 플래그 사용 (항상 권장)
nextflow run . -profile docker -params-file params.yaml -resume
```

### 문제 5: Chromosome 이름 불일치

**에러:** "Chromosome chrM not found"

**해결:** REFERENCE_GENOME_GUIDE.md 참조
```yaml
# FASTA 파일의 실제 염색체 이름 확인 후 설정
mito_name: 'MT'  # 또는 'chrM', 'M'
```

### 문제 6: samplesheet.csv를 실수로 Git에 커밋했을 때

```bash
# Git 추적에서 제거 (파일은 로컬에 유지)
git rm --cached samplesheet.csv
git commit -m "Remove samplesheet.csv from tracking"
git push origin main
```

### 문제 7: Push가 거부됨 (rejected)

```bash
# 원격 변경사항을 먼저 가져온 후 재시도
git pull origin main --rebase
git push origin main
```

### 문제 8: Merge conflict 발생

```bash
# 충돌 파일 확인
git status

# 충돌 파일을 편집하여 해결 후
git add <conflicted-file>
git commit -m "Resolve merge conflict"
git push origin main
```

---

## 🔍 설정 검증

### check_setup.sh 실행

```bash
./check_setup.sh
```

정상 출력 예시:
```
==========================================
ATAC-seq Pipeline Setup Checker
==========================================

1. Checking Nextflow...
   ✅ Nextflow found

2. Checking container systems...
   ✅ Singularity found: apptainer version 1.4.5

3. Checking template files...
   ✅ samplesheet_template.csv exists
   ✅ params_template.yaml exists

4. Checking .gitignore configuration...
   ✅ samplesheet.csv is gitignored
   ✅ params.yaml is gitignored
   ✅ samplesheet_template.csv is tracked

5. Checking Git repository...
   ✅ samplesheet_template.csv is tracked by Git
   ✅ params_template.yaml is tracked by Git
   ✅ samplesheet.csv is not tracked (correct)

6. Checking working files...
   ✅ samplesheet.csv exists (working file)
   ✅ params.yaml exists (working file)
==========================================
```

### 파일 유효성 확인

```bash
# Samplesheet 형식 검증
python bin/check_samplesheet.py samplesheet.csv

# Params YAML 문법 확인
python -c "import yaml; yaml.safe_load(open('params.yaml'))"

# Nextflow dry-run (파이프라인 문법 확인)
nextflow run . --help
```

---

## ❓ FAQ

**Q: Nextflow가 없을 때 직접 설치하려면?**
```bash
# Conda 없이 직접 설치
curl -s https://get.nextflow.io | bash
sudo mv nextflow /usr/local/bin/
nextflow -version
```

**Q: 템플릿을 수정한 후 커밋하는 방법은?**
```bash
# 작업 파일(samplesheet.csv, params.yaml)은 자동으로 제외됨
# 템플릿만 선택적으로 커밋
git add samplesheet_template.csv
git commit -m "Update samplesheet template with new examples"
git push origin main
```

**Q: 여러 사람이 같은 저장소를 사용할 때 작업 파일 충돌을 피하려면?**
```bash
# 각자 프로젝트명을 붙인 파일 사용 — .gitignore가 자동 제외
cp samplesheet_template.csv samplesheet_personA.csv  # git 무시됨
cp samplesheet_template.csv samplesheet_personB.csv  # git 무시됨
```

**Q: Nextflow 실행 중 디스크 공간 확보가 필요할 때?**
```bash
# work/ 디렉토리 정리 (완료된 실행의 캐시 삭제)
nextflow clean -f
# 또는 특정 실행만
nextflow clean <run-name> -f
```

---

## 💡 유용한 팁

### 1. Dry-run으로 먼저 테스트
```bash
# 테스트 프로파일로 빠른 검증
nextflow run nf-core/atacseq -profile test,docker --outdir quick_test
```

### 2. 리소스 모니터링
```bash
# Nextflow Tower 사용 (웹 기반)
nextflow run . -with-tower

# 또는 execution report 생성
nextflow run . -with-report report.html -with-timeline timeline.html
```

### 3. 특정 단계만 스킵
```yaml
skip_trimming: false
skip_fastqc: false
skip_peak_qc: false
skip_deseq2_qc: true  # DESeq2만 스킵
```

### 4. 중간 파일 저장
```yaml
save_trimmed: true
save_align_intermeds: true
save_reference: true  # 인덱스 저장하여 재사용
```

### 5. 여러 aligner 비교
```bash
# BWA로 실행
nextflow run . -params-file params.yaml --aligner bwa --outdir results_bwa

# Bowtie2로 실행 (결과를 다른 디렉토리에)
nextflow run . -params-file params.yaml --aligner bowtie2 --outdir results_bowtie2
```

---

## 📚 추가 리소스

- **상세 사용법:** [usage.md](usage.md)
- **참조 유전체 가이드:** [REFERENCE_GENOME_GUIDE.md](REFERENCE_GENOME_GUIDE.md)
- **파이프라인 출력 설명:** [output.md](output.md)
- **Conda 환경 관리:** [CONDA_SETUP_GUIDE.md](CONDA_SETUP_GUIDE.md)
- **서버 설정:** [SERVER_SETUP.md](SERVER_SETUP.md)
- **nf-core 공식 문서:** https://nf-co.re/atacseq
- **Nextflow 문서:** https://www.nextflow.io/docs/latest/

---

## ❓ 도움말

### 파이프라인 도움말
```bash
nextflow run nf-core/atacseq --help
```

### 사용 가능한 파라미터 확인
```bash
nextflow run nf-core/atacseq --help | less
```

### 버전 확인
```bash
nextflow run nf-core/atacseq --version
```

---

**작성일:** 2026-01-23  
**버전:** 2.1.2
