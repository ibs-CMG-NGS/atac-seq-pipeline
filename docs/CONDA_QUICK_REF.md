# 🚀 ATAC-seq Pipeline - Conda 환경 빠른 참조

## 📋 빠른 설치 (3단계)

### 1️⃣ 자동 설치
```bash
cd ~/ngs_pipeline/atac-seq-pipeline
./install_conda_env.sh
```

### 2️⃣ 환경 활성화
```bash
source activate_pipeline.sh
# 또는
conda activate atac-seq-pipeline
```

### 3️⃣ 검증
```bash
./check_setup.sh
```

---

## 🎯 주요 명령어

### 환경 관리
```bash
# 활성화
conda activate atac-seq-pipeline

# 비활성화
conda deactivate

# 환경 목록
conda env list

# 설치된 패키지 확인
conda list
```

### 패키지 관리
```bash
# 패키지 설치
conda install -c bioconda package_name

# 패키지 업데이트
conda update package_name

# 모두 업데이트
conda update --all
```

### 환경 복제/백업
```bash
# 환경 내보내기
conda env export > my_environment.yml

# 환경 복제
conda create --name backup --clone atac-seq-pipeline

# 환경 삭제
conda env remove -n environment_name
```

---

## 📖 상세 문서

| 문서 | 내용 |
|------|------|
| **[CONDA_SETUP_GUIDE.md](CONDA_SETUP_GUIDE.md)** | 완벽한 Conda 설정 가이드 |
| **[QUICK_START_KR.md](QUICK_START_KR.md)** | 한글 빠른 시작 |
| **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** | 전체 설정 완료 가이드 |

---

## 🔧 트러블슈팅

### "conda: command not found"
```bash
# Conda 초기화
source ~/miniconda3/etc/profile.d/conda.sh
conda init bash
source ~/.bashrc
```

### 환경 활성화 실패
```bash
# 환경 재생성
conda env remove -n atac-seq-pipeline
./install_conda_env.sh
```

### 패키지 설치 실패
```bash
# 채널 재설정
conda config --add channels conda-forge
conda config --add channels bioconda
conda config --add channels defaults
```

---

## 💡 유용한 팁

```bash
# 환경 활성화 단축키 만들기
echo 'alias activate-atac="conda activate atac-seq-pipeline"' >> ~/.bashrc
source ~/.bashrc

# 이제 짧게 활성화
activate-atac
```

---

**작성일:** 2026-01-23
