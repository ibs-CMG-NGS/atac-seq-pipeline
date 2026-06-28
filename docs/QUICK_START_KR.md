# ATAC-seq 파이프라인 빠른 시작 가이드 (한글)

## 📋 개요

이 가이드는 nf-core/atacseq 파이프라인을 Windows WSL Ubuntu와 Linux 서버에서 사용하는 방법을 설명합니다.

---

## 🚀 빠른 시작

### 1단계: 샘플시트 준비 — `make_samplesheet.py` 사용 (권장)

> ⚠️ 샘플시트를 수동으로 작성하면 `replicate` 규칙 위반, 파일 경로 실수 등의 오류가 발생하기 쉽습니다.  
> **`bin/make_samplesheet.py`를 사용하면 자동 생성 + 실행 전 검증까지 한 번에 처리됩니다.**

#### 메타데이터 TSV 작성 (사람이 직접 하는 유일한 작업)

```tsv
sample_id       condition    replicate   folder
Veh_1           Veh          1           Neuron1
Veh_2           Veh          1           Neuron2
Veh_3           Veh          1           Neuron3
GABA_1          GABA         1           Neuron4
GABA_2          GABA         1           Neuron5
GABA_3          GABA         1           Neuron6
```

**컬럼 설명:**

| 컬럼 | 필수 | 설명 |
|------|------|------|
| `sample_id` | ✅ | 파이프라인 sample 이름 (결과 파일명에 사용) |
| `replicate` | ✅ | **같은 `sample_id` 내**에서 1부터 시작하는 정수. 독립적인 샘플은 항상 `1` |
| `condition` | - | 그룹 정보 (메모용, 파이프라인 미사용) |
| `folder` | - | raw_dir 아래 실제 폴더명 (생략 시 sample_id와 동일) |

#### ⚠️ `replicate` 규칙 (중요)

```
❌ 잘못된 예 — sample이 다르면 replicate도 달라지면 안 됨
   Veh_1, replicate=1
   Veh_2, replicate=2   ← ERROR: 'Veh_2'는 독립 샘플이므로 반드시 1부터

✅ 올바른 예 — 독립적인 샘플은 각각 replicate=1
   Veh_1, replicate=1
   Veh_2, replicate=1
   Veh_3, replicate=1

✅ 올바른 예 — 같은 sample_id로 생물학적 반복 표현 시
   KO, replicate=1
   KO, replicate=2
   KO, replicate=3
```

> 파이프라인이 동일한 `sample_id`의 여러 lane/run을 같은 replicate로 자동 merge합니다.  
> 각 샘플이 이미 독립 개체이면 `sample_id`를 다르게 지정하고 `replicate=1`을 사용하세요.

#### 샘플시트 자동 생성 + 검증

```bash
python3 bin/make_samplesheet.py \
    metadata_xxx.tsv \
    /path/to/01.RawData \
    samplesheet_xxx.csv \
    --validate
```

`--validate` 옵션이 파이프라인의 `check_samplesheet.py`를 실행하여 실제 파이프라인과 동일한 규칙으로 검증합니다.

**출력 예시:**
```
────────────────────────────────────────────────────
  Sample               Folder    Rep  Lanes
────────────────────────────────────────────────────
  Veh_1                Neuron1     1  L5, L6, L7, L8
  Veh_2                Neuron2     1  L5, L6, L7, L8
  GABA_1               Neuron4     1  L5, L6, L7, L8
  ...
────────────────────────────────────────────────────
  총 12개 샘플, 48개 행

✅ 샘플시트 저장: samplesheet_xxx.csv
✅ Pipeline 검증 통과 (check_samplesheet.py)
```

#### 수동 작성 시 형식 (make_samplesheet.py 미사용 시)

```csv
sample,fastq_1,fastq_2,replicate
Veh_1,/data/Neuron1_L5_1.fq.gz,/data/Neuron1_L5_2.fq.gz,1
Veh_1,/data/Neuron1_L6_1.fq.gz,/data/Neuron1_L6_2.fq.gz,1
Veh_2,/data/Neuron2_L5_1.fq.gz,/data/Neuron2_L5_2.fq.gz,1
```

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

**`run_pipeline.sh` 래퍼 사용 (권장) — 자동 resume + 무결성 검사 포함:**

```bash
cd /home/ngs/ngs-pipeline/atac-seq-pipeline

bash run_pipeline.sh \
    --params params_pym.yaml \
    --outdir /home/ngs/data/ygkim/2026/2026-pym-mouse-atac/results \
    --workdir /home/ngs/data/nextflow_work/atac-seq-pipeline-pym \
    --max-resume 2
```

> `run_pipeline.sh`는 파이프라인 종료 후 자동으로 출력 무결성을 검사하고,  
> 누락된 샘플이 있으면 `-resume`으로 자동 재실행합니다 (경합 조건 방지).

**screen으로 백그라운드 실행 (직접 nextflow 사용 시):**

```bash
# screen 세션 생성
screen -dmS {project}-atac bash -c "
source /home/ngs/program/anaconda3/etc/profile.d/conda.sh
conda activate atac-seq-pipeline
cd /home/ngs/ngs-pipeline/atac-seq-pipeline
nextflow run main.nf \
    -params-file params_{project}.yaml \
    -work-dir /home/ngs/data/nextflow_work/atac-seq-pipeline-{project} \
    -with-trace -with-report -with-timeline \
    > /home/ngs/data/ygkim/2026/2026-{project}/nextflow.log 2>&1
echo \"Exit: \$?\" >> /home/ngs/data/ygkim/2026/2026-{project}/nextflow.log
"

# 세션 확인
screen -ls

# 로그 확인
tail -f /home/ngs/data/ygkim/2026/2026-{project}/nextflow.log

# screen 접속 (진행 상황 직접 확인)
screen -r {project}-atac
# 나오기: Ctrl+A, D
```

> ⚠️ 새 프로젝트마다 `-work-dir`을 **반드시 분리**하세요.  
> 같은 work dir을 공유하면 캐시 충돌이 발생합니다.

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
read_length: 75        # mouse 프로토콜에 따라 75 또는 150
aligner: 'bwa'
# macs_gsize: '1.87e9'  # 커스텀 유전체 사용 시 필요, iGenomes 사용 시 생략
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

### 문제 1: "Replicate ids must start with 1..<num_replicates>!" 에러

**원인:** `replicate` 컬럼 규칙 위반. 같은 `sample_id` 내에서만 1부터 연속 번호여야 함.

```
ERROR: Please check samplesheet -> Replicate ids must start with 1..<num_replicates>!
  Sample: 'GABA_2, replicate ids: 2'
```

**해결:** `make_samplesheet.py`의 `--validate`로 실행 전에 검출 가능.

```bash
# 독립적인 샘플은 모두 replicate=1
# ❌ 잘못됨
Veh_2, replicate=2

# ✅ 올바름
Veh_2, replicate=1
```

자세한 규칙은 **1단계: 샘플시트 준비** 섹션의 `replicate` 규칙 참고.

---

### 문제 2: ATAQv/FRiP가 일부 샘플에서 누락 (경합 조건)

**원인:** MACS2가 파이프라인 마지막에 완료되면 downstream ATAQv/FRiP 태스크가 Nextflow 채널에 큐잉되지 못하는 timing race condition.

**예방:** `run_pipeline.sh` 래퍼 사용 (자동 `-resume` 포함).

**사후 수습:**
```bash
# 1. 무결성 검사로 누락 샘플 확인
python3 bin/check_pipeline_integrity.py <results_dir> <work_dir>

# 2. ATAQv 수동 재실행 스크립트 사용
bash run_ataqv_missing.sh   # 프로젝트별로 작성
```

**근본 원인과 설정 수정 (nextflow.config):**
```groovy
executor.cpus        = 24      // 서버 전체 CPU 사용 (기존 16 → CPU 슬롯 부족이 원인)
executor.queueSize   = 100     // 더 많은 태스크를 동시에 큐잉
executor.pollInterval = '5 sec' // 완료 감지 주기 단축
```

**프로세스별 CPU 최적화 (conf/base.config):**
```groovy
withName: '.*MACS2.*'  { cpus = 4 }  // 실제로 멀티스레드 미지원
withName: '.*ATAQV.*'  { cpus = 4 }  // 4스레드로 충분
withName: 'FRIP_SCORE' { cpus = 1 }  // bedtools intersect는 단일 스레드
```

---

### 문제 3: "No such file or directory" 에러

**원인:** samplesheet.csv의 파일 경로가 잘못됨

**해결:**
```bash
# 경로 확인
ls -lh /path/to/your/file.fastq.gz

# 절대 경로 사용 권장
realpath your_file.fastq.gz
```

### 문제 4: 메모리 부족 에러

**해결:** params.yaml에서 리소스 줄이기
```yaml
max_memory: '64.GB'
max_cpus: 8
```

### 문제 5: Docker/Singularity 권한 에러

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

### 문제 6: Pipeline 중단 후 재시작

**해결:**
```bash
# -resume 플래그 사용 (항상 권장)
nextflow run . -profile docker -params-file params.yaml -resume
```

### 문제 7: Chromosome 이름 불일치

**에러:** "Chromosome chrM not found"

**해결:** REFERENCE_GENOME_GUIDE.md 참조
```yaml
# FASTA 파일의 실제 염색체 이름 확인 후 설정
mito_name: 'MT'  # 또는 'chrM', 'M'
```

### 문제 8: samplesheet.csv를 실수로 Git에 커밋했을 때

```bash
# Git 추적에서 제거 (파일은 로컬에 유지)
git rm --cached samplesheet.csv
git commit -m "Remove samplesheet.csv from tracking"
git push origin main
```

### 문제 9: Push가 거부됨 (rejected)

```bash
# 원격 변경사항을 먼저 가져온 후 재시도
git pull origin main --rebase
git push origin main
```

### 문제 10: Merge conflict 발생

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
