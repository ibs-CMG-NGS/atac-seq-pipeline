# GitHub 저장소 연결 가이드

## 현재 상태 ✅

로컬 Git 저장소가 성공적으로 초기화되었습니다:
- ✅ Git repository initialized
- ✅ 234 파일 커밋됨
- ✅ 템플릿 파일들이 Git에 추적됨
- ✅ 작업 파일들 (samplesheet.csv, params.yaml)이 .gitignore에 의해 제외됨

---

## GitHub에 연결하기

### 1단계: GitHub에서 새 저장소 생성

1. https://github.com 에 로그인
2. 우측 상단의 `+` → `New repository` 클릭
3. 저장소 정보 입력:
   - **Repository name:** `atac-seq-pipeline` (원하는 이름)
   - **Description:** `nf-core ATAC-seq pipeline with custom templates`
   - **Visibility:** Private 또는 Public 선택
   - ⚠️ **중요:** "Initialize this repository with a README" 체크 **해제**
   - ⚠️ `.gitignore` 및 `license` 추가 **하지 않음** (이미 있음)
4. `Create repository` 클릭

### 2단계: 로컬 저장소를 GitHub에 연결

GitHub에서 새 저장소를 만들면 다음과 같은 명령어가 표시됩니다:

```bash
# 예시 (실제 GitHub 페이지의 명령어를 사용하세요)
git remote add origin https://github.com/your-username/atac-seq-pipeline.git
git branch -M main
git push -u origin main
```

**WSL Ubuntu에서 실행:**

```bash
cd /home/ygkim/ngs_pipeline/atac-seq-pipeline

# GitHub 저장소 주소로 변경하세요!
git remote add origin https://github.com/YOUR_USERNAME/atac-seq-pipeline.git

# 메인 브랜치로 푸시
git push -u origin main
```

### 3단계: 인증

GitHub 인증 방법:

**방법 A: Personal Access Token (권장)**

1. GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. `Generate new token (classic)` 클릭
3. 권한 선택:
   - ✅ `repo` (전체 repo 접근)
4. Token 생성 및 복사
5. 푸시할 때 비밀번호 대신 토큰 입력

**방법 B: SSH Key**

```bash
# SSH 키 생성
ssh-keygen -t ed25519 -C "your_email@example.com"

# 공개키 복사
cat ~/.ssh/id_ed25519.pub

# GitHub Settings → SSH and GPG keys에 추가
# 원격 저장소 URL을 SSH로 변경
git remote set-url origin git@github.com:YOUR_USERNAME/atac-seq-pipeline.git
```

---

## 서버와 동기화하기

### 서버에서 처음 클론

```bash
# 서버에 SSH 접속
ssh your-server

# 저장소 클론
cd /path/to/your/workspace
git clone https://github.com/YOUR_USERNAME/atac-seq-pipeline.git
cd atac-seq-pipeline

# 작업 파일 생성
cp samplesheet_template.csv samplesheet.csv
cp params_template.yaml params.yaml

# 서버 환경에 맞게 편집
vim samplesheet.csv
vim params.yaml
```

### 정기적인 동기화 워크플로우

**WSL Ubuntu (개발/테스트):**

```bash
cd /home/ygkim/ngs_pipeline/atac-seq-pipeline

# 1. 최신 변경사항 받기
git pull origin main

# 2. 템플릿 수정 (필요시)
nano samplesheet_template.csv
nano params_template.yaml

# 3. 커밋 및 푸시
git add samplesheet_template.csv params_template.yaml
git commit -m "Update templates with new examples"
git push origin main
```

**서버 (프로덕션):**

```bash
cd /path/to/atac-seq-pipeline

# 최신 변경사항 동기화
git pull origin main

# 작업 파일 업데이트 (필요시)
cp samplesheet_template.csv samplesheet.csv
vim samplesheet.csv

# 파이프라인 실행
nextflow run . -profile singularity -params-file params.yaml -resume
```

---

## 브랜치 전략 (선택사항)

협업하거나 다양한 실험을 할 경우:

```bash
# 새 브랜치 생성
git checkout -b experiment-1

# 설정 파일 수정
nano params_template.yaml

# 커밋
git add params_template.yaml
git commit -m "Add parameters for experiment 1"
git push origin experiment-1

# Pull Request 생성 후 main에 병합
```

---

## Git 명령어 참고

### 기본 워크플로우

```bash
# 상태 확인
git status

# 변경사항 확인
git diff

# 특정 파일 추가
git add filename

# 모든 변경사항 추가 (주의!)
git add .

# 커밋
git commit -m "Descriptive message"

# 푸시
git push origin main

# 풀
git pull origin main
```

### 유용한 명령어

```bash
# 로그 확인
git log --oneline

# 브랜치 확인
git branch -a

# 원격 저장소 확인
git remote -v

# 변경사항 취소 (unstaged)
git restore filename

# 변경사항 취소 (staged)
git restore --staged filename

# 최신 커밋 수정
git commit --amend
```

---

## 문제 해결

### Q: "samplesheet.csv를 실수로 커밋했어요!"

```bash
# Git 추적에서 제거 (파일은 유지)
git rm --cached samplesheet.csv
git commit -m "Remove samplesheet.csv from tracking"
git push origin main
```

### Q: "Push가 거부되었습니다 (rejected)"

```bash
# 원격 변경사항 먼저 가져오기
git pull origin main --rebase
git push origin main
```

### Q: "Merge conflict 발생"

```bash
# 충돌 파일 확인
git status

# 파일 편집하여 충돌 해결
nano conflicted-file

# 해결 후 추가 및 커밋
git add conflicted-file
git commit -m "Resolve merge conflict"
git push origin main
```

---

## 다음 단계

1. ✅ GitHub에 새 저장소 생성
2. ✅ 로컬 저장소를 GitHub에 연결
3. ✅ 첫 푸시 완료
4. ✅ 서버에서 클론
5. ✅ 작업 파일 생성 및 편집
6. ✅ 파이프라인 실행

---

## 체크리스트

- [ ] GitHub 저장소 생성
- [ ] 로컬 저장소와 GitHub 연결
- [ ] 첫 push 완료
- [ ] 서버에서 clone 완료
- [ ] 서버에서 작업 파일 (samplesheet.csv, params.yaml) 생성
- [ ] 서버 환경에 맞게 params.yaml 수정
- [ ] 테스트 실행 성공

---

## 참고 자료

- [GitHub Docs](https://docs.github.com)
- [Git 기초](https://git-scm.com/book/ko/v2)
- [Pro Git Book (한글)](https://git-scm.com/book/ko/v2)

---

**작성일:** 2026-01-23  
**문의:** GitHub Issues 또는 README 참조
