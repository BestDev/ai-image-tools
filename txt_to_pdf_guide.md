# txt_to_pdf.py 사용 가이드

TXT 파일을 PDF로 변환하는 스크립트입니다.
한글, 일본어(히라가나/카타카나), 한자를 모두 지원합니다.

---

## 필수 조건

### Python 패키지
```
pip install reportlab fonttools pymupdf
```

### 폰트
사용자 폰트 폴더에 **NotoSansCJK-VF.ttf.ttc** 설치 필요.
경로: `%USERPROFILE%\AppData\Local\Microsoft\Windows\Fonts\`

폰트가 없을 경우 시스템 폰트(NotoSansKR, 맑은 고딕)로 자동 대체됩니다.

---

## 사용법

### 기본 (단일 파일)
```
python txt_to_pdf.py document.txt
```
→ `document.pdf` 생성 (같은 경로)

### 출력 파일명 지정
```
python txt_to_pdf.py document.txt result.pdf
```

### 폴더 내 전체 변환
```
python txt_to_pdf.py "*.txt"
python txt_to_pdf.py "폴더명/*.txt"
```
> 따옴표 필수 (쉘의 와일드카드 확장 방지)

### 일본어/한자 위주 문서
```
python txt_to_pdf.py document.txt --font jp
```

---

## 옵션

| 옵션 | 값 | 설명 |
|------|----|------|
| `--font` | `kr` (기본) | 한국식 자형 기준 (한글 포함 문서) |
| `--font` | `jp` | 일본식 자형 기준 (일본어/한자 위주 문서) |

> 동일 한자라도 나라별 자형 차이가 있으므로 문서 언어에 맞게 선택

---

## 지원 사양

| 항목 | 내용 |
|------|------|
| 페이지 크기 | A4 |
| 여백 | 상하좌우 20mm |
| 폰트 크기 | 11pt |
| 폰트 굵기 | Regular (wght=400) |
| 긴 줄 처리 | 자동 줄바꿈 |
| 다중 페이지 | 자동 페이지 추가 |

### 인코딩 자동 감지 순서
UTF-8 → UTF-8 BOM → CP949 → EUC-KR

### 문자 커버리지 (NotoSansCJK-VF.ttf.ttc 사용 시)

| 문자 | 커버리지 |
|------|---------|
| 한글 | 100% |
| 히라가나 | 97% (미정의 코드포인트 3자 제외 시 100%) |
| 카타카나 | 100% |
| CJK 기본 한자 | 100% |
| CJK 확장A 한자 | 100% |

---

## 폰트 우선순위 (자동 fallback)

| 순위 | 폰트 | 비고 |
|------|------|------|
| 1 | NotoSansCJK-VF.ttf.ttc | 한중일 통합, 최우선 |
| 2 | NotoSansKR-VF.ttf / NotoSansJP-VF.ttf | Windows 설치 폰트 |
| 3 | 맑은 고딕 (malgun.ttf) | Windows 기본 |
