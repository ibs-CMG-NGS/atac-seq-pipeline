# 🎉 ATAC-seq 파이프라인 설정 완료!

## ✅ 완료된 작업

### 1. 파일 생성 및 설정
- ✅ `samplesheet_template.csv` - 샘플 정보 템플릿
- ✅ `params_template.yaml` - 파이프라인 파라미터 템플릿
- ✅ `REFERENCE_GENOME_GUIDE.md` - 참조 유전체 준비 가이드 (영문)
- ✅ `QUICK_START_KR.md` - 빠른 시작 가이드 (한글)
- ✅ `README_SETUP.md` - 설정 및 Git 워크플로우 문서
- ✅ `GITHUB_SETUP.md` - GitHub 저장소 연결 가이드
- ✅ `check_setup.sh` - 자동 설정 검증 스크립트
- ✅ `.gitignore` - 작업 파일 제외 설정

### 2. Git 저장소 초기화
- ✅ Git 저장소 초기화 완료
- ✅ 234개 파일 커밋 완료
- ✅ 템플릿 파일들 Git 추적 설정
- ✅ 작업 파일들 (samplesheet.csv, params.yaml) Git 제외

### 3. 작업 파일 생성
- ✅ `samplesheet.csv` - 실제 샘플 정보 (Git 제외)
- ✅ `params.yaml` - 실제 파라미터 설정 (Git 제외)

---

## 📊 설정 검증 결과

```
==========================================
ATAC-seq Pipeline Setup Checker
==========================================

1. Checking Nextflow...
   ⚠️ Nextflow not found (서버에서 설치 필요)

2. Checking container systems...
   ⚠️ Docker not found (WSL에서는 선택사항)
   ✅ Singularity found: apptainer version 1.4.5

3. Checking template files...
   ✅ samplesheet_template.csv exists
   ✅ params_template.yaml exists

4. Checking .gitignore configuration...
   ✅ .gitignore exists
   ✅ samplesheet.csv is gitignored
   ✅ params.yaml is gitignored
   ✅ samplesheet_template.csv is tracked

5. Checking Git repository...
   ✅ Git repository initialized
   ✅ samplesheet_template.csv is tracked by Git
   ✅ params_template.yaml is tracked by Git
   ✅ samplesheet.csv is not tracked (correct)
   ✅ params.yaml is not tracked (correct)

6. Checking working files...
   ✅ samplesheet.csv exists (working file)
   ✅ params.yaml exists (working file)
==========================================
```

---

## 🚀 다음 단계

### 1. GitHub에 푸시 (선택사항, 권장)

**방법 A: HTTPS 사용**
```bash
# GitHub에서 새 저장소 생성 후:
cd /home/ygkim/ngs_pipeline/atac-seq-pipeline

# 원격 저장소 추가 (YOUR_USERNAME을 실제 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/atac-seq-pipeline.git

# 푸시
git push -u origin main
```

**방법 B: SSH 사용**
```bash
# SSH 키 생성 (아직 없다면)
ssh-keygen -t ed25519 -C "your_email@example.com"

# 공개키를 GitHub에 추가 후:
git remote add origin git@github.com:YOUR_USERNAME/atac-seq-pipeline.git
git push -u origin main
```

자세한 내용은 **[GITHUB_SETUP.md](GITHUB_SETUP.md)** 참조!

### 2. 서버에서 설정

**서버에 Nextflow 설치:**
```bash
# 서버 SSH 접속
ssh your-server

# Nextflow 설치
curl -s https://get.nextflow.io | bash
sudo mv nextflow /usr/local/bin/

# 또는 특정 디렉토리에:
mkdir -p ~/bin
mv nextflow ~/bin/
echo 'export PATH=$PATH:~/bin' >> ~/.bashrc
source ~/.bashrc

# 확인
nextflow -version
```

**저장소 클론 (GitHub에 푸시한 경우):**
```bash
cd /path/to/your/workspace
git clone https://github.com/YOUR_USERNAME/atac-seq-pipeline.git
cd atac-seq-pipeline
```

**또는 직접 복사 (GitHub 사용 안 하는 경우):**
```bash
# WSL에서 서버로 복사
scp -r /home/ygkim/ngs_pipeline/atac-seq-pipeline your-server:/path/to/workspace/
```

**서버에서 작업 파일 생성:**
```bash
cd atac-seq-pipeline
cp samplesheet_template.csv samplesheet.csv
cp params_template.yaml params.yaml

# 서버 환경에 맞게 수정
vim samplesheet.csv  # FASTQ 파일 경로 수정
vim params.yaml      # 서버 리소스에 맞게 조정
```

### 3. 참조 유전체 준비

**Option A: iGenomes 사용 (가장 쉬움)**

`params.yaml` 설정:
```yaml
genome: 'GRCh38'
read_length: 150
```

**Option B: 커스텀 유전체**

상세 가이드는 **[REFERENCE_GENOME_GUIDE.md](REFERENCE_GENOME_GUIDE.md)** 참조!

간단 예시:
```bash
# 서버에서
mkdir -p /data/genomes/GRCh38
cd /data/genomes/GRCh38

# 다운로드 (Ensembl)
wget http://ftp.ensembl.org/pub/release-109/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
wget http://ftp.ensembl.org/pub/release-109/gtf/homo_sapiens/Homo_sapiens.GRCh38.109.gtf.gz
wget https://github.com/Boyle-Lab/Blacklist/raw/master/lists/hg38-blacklist.v2.bed.gz

# 압축 해제
gunzip *.gz
```

`params.yaml` 설정:
```yaml
genome: null
fasta: '/data/genomes/GRCh38/Homo_sapiens.GRCh38.dna.primary_assembly.fa'
gtf: '/data/genomes/GRCh38/Homo_sapiens.GRCh38.109.gtf'
blacklist: '/data/genomes/GRCh38/hg38-blacklist.v2.bed'
mito_name: 'MT'
read_length: 150
save_reference: true
```

### 4. 테스트 실행

**WSL Ubuntu (Dry-run):**
```bash
cd /home/ygkim/ngs_pipeline/atac-seq-pipeline

# 간단한 테스트 (Docker 필요)
# nextflow run . -profile test,docker --outdir test_results

# Singularity로 테스트 (현재 환경)
# nextflow run . -profile test,singularity --outdir test_results
```

**서버 (실제 분석):**
```bash
cd /path/to/atac-seq-pipeline

# samplesheet.csv와 params.yaml 준비 후
nextflow run . \
  -profile singularity \
  -params-file params.yaml \
  -resume

# 백그라운드 실행
nohup nextflow run . \
  -profile singularity \
  -params-file params.yaml \
  -resume > pipeline.log 2>&1 &

# 로그 확인
tail -f pipeline.log
```

---

## 📚 문서 가이드

### 처음 사용하는 경우
1. **[QUICK_START_KR.md](QUICK_START_KR.md)** - 한글 빠른 시작 (필수!)
2. **[README_SETUP.md](README_SETUP.md)** - 설정 및 Git 워크플로우

### 참조 유전체 준비
3. **[REFERENCE_GENOME_GUIDE.md](REFERENCE_GENOME_GUIDE.md)** - 상세 가이드

### GitHub 연동
4. **[GITHUB_SETUP.md](GITHUB_SETUP.md)** - 저장소 연결 방법

### 일반 정보
5. **[README.md](README.md)** - 파이프라인 개요
6. **[docs/usage.md](docs/usage.md)** - nf-core 공식 사용법
7. **[docs/output.md](docs/output.md)** - 출력 파일 설명

---

## 🔍 주요 명령어 모음

### 설정 검증
```bash
./check_setup.sh
```

### Git 작업
```bash
git status                    # 상태 확인
git add filename              # 파일 추가
git commit -m "message"       # 커밋
git push origin main          # 푸시
git pull origin main          # 풀
```

### 파이프라인 실행
```bash
# 도움말
nextflow run . --help

# 테스트
nextflow run . -profile test,singularity --outdir test

# 실제 분석
nextflow run . -profile singularity -params-file params.yaml -resume
```

---

## ⚠️ 중요 참고사항

### Git 추적 파일
- ✅ **추적됨 (공유):** 템플릿 파일들, 문서, 파이프라인 코드
- ❌ **제외됨 (개인):** samplesheet.csv, params.yaml, results/, work/

### 작업 흐름
1. **WSL Ubuntu:** 템플릿 수정, 테스트, Git 커밋/푸시
2. **서버:** Git pull, 작업 파일 생성/수정, 실제 분석 실행

### 주의사항
- `samplesheet.csv`와 `params.yaml`은 각 환경마다 별도로 관리
- 템플릿 파일만 Git에 커밋
- 결과 파일들 (results/, work/)은 자동으로 Git에서 제외됨

---

## 💡 유용한 팁

### Nextflow 설치 (WSL Ubuntu)
```bash
curl -s https://get.nextflow.io | bash
sudo mv nextflow /usr/local/bin/
nextflow -version
```

### Docker 설치 (WSL Ubuntu, 선택사항)
```bash
# WSL2에서 Docker Desktop 사용 권장
# https://docs.docker.com/desktop/windows/wsl/
```

### 리소스 모니터링
```bash
# 실행 보고서 생성
nextflow run . -with-report report.html -with-timeline timeline.html

# Nextflow Tower (웹 기반)
nextflow run . -with-tower
```

---

## ✅ 체크리스트

### 초기 설정
- [x] Git 저장소 초기화
- [x] 템플릿 파일 생성
- [x] 작업 파일 생성
- [x] .gitignore 설정
- [ ] GitHub에 푸시 (선택사항)
- [ ] 서버에 Nextflow 설치
- [ ] 서버에 저장소 클론 또는 복사

### 분석 준비
- [ ] samplesheet.csv 작성
- [ ] params.yaml 설정
- [ ] 참조 유전체 준비
- [ ] FASTQ 파일 준비
- [ ] 테스트 실행

### 실행
- [ ] 테스트 프로파일로 파이프라인 검증
- [ ] 실제 데이터로 분석 실행
- [ ] 결과 확인 (MultiQC 리포트)

---

## 🆘 문제 해결

### "Nextflow not found"
→ 서버에 Nextflow 설치 필요 (위 명령어 참조)

### "Docker not found"
→ WSL: Docker Desktop 설치 권장
→ 서버: Singularity/Apptainer 사용 (이미 설치됨!)

### "Permission denied"
→ `chmod +x check_setup.sh` 실행

### 기타 문제
→ **[QUICK_START_KR.md](QUICK_START_KR.md)** 트러블슈팅 섹션 참조

---

## 📞 추가 도움

- **nf-core 문서:** https://nf-co.re/atacseq
- **Nextflow 문서:** https://www.nextflow.io/docs/latest/
- **GitHub Issues:** 저장소에 이슈 등록

---

**축하합니다! 🎉**  
ATAC-seq 파이프라인 설정이 완료되었습니다.

이제 데이터 분석을 시작할 준비가 되었습니다!

---

**작성일:** 2026-01-23  
**버전:** 1.0
**파이프라인:** nf-core/atacseq v2.1.2
