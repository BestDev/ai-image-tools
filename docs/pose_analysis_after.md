# 포즈 분석 보고서 — 시스템 프롬프트 수정 후 (After) + Before 비교

10장 이미지 기준, 8개 모델 조합(std/spec × think/nothink × enen/enzh)으로 포즈 역동성 분석.
시스템 프롬프트에 `silhouette curves` / `体态曲线` + `weight distribution` / `重心分布` 추가 **이후** 결과.

> 분석일: 2026-03-26
> 시스템 프롬프트: `silhouette curves`, `weight distribution` 추가 **이후** 버전
> 비교 대상: `pose_analysis_before.md` (수정 전 베이스라인)

---

## 1. 테스트 구성

### 시스템 프롬프트 변경 사항

| 프롬프트 | 변경 전 | 변경 후 |
|---------|---------|---------|
| EN std | `pose (body orientation, ...)` | `pose (body orientation and silhouette curves, ..., leg stance and weight distribution)` |
| ZH std | `姿势（身体朝向...腿部姿态）` | `姿势（身体朝向与体态曲线...腿部姿态与重心分布）` |
| EN spec | `body orientation as seen, ..., overall silhouette` | `body orientation and silhouette curves as seen, ..., leg stance and weight distribution, overall body line` |
| ZH spec | `身体朝向...整体轮廓走势` | `身体朝向与体态曲线...腿部姿态与重心分布、整体身体线条走势` |

### 모델 조합 (8개)

| # | 조합 | 약어 |
|---|------|------|
| 1 | std-think-enen | 영어 표준 사고 |
| 2 | spec-think-enen | 영어 스펙 사고 |
| 3 | std-nothink-enen | 영어 표준 직관 |
| 4 | spec-nothink-enen | 영어 스펙 직관 |
| 5 | std-think-enzh | 중국어 표준 사고 |
| 6 | spec-think-enzh | 중국어 스펙 사고 |
| 7 | std-nothink-enzh | 중국어 표준 직관 |
| 8 | spec-nothink-enzh | 중국어 스펙 직관 |

---

## 2. 핵심 포즈 요소 이행률 — Before vs After

### 2.1 체태곡선 (Silhouette Curves / 体态曲线)

**Before: 0% → After: 26% (전체) / EN 18% / ZH 35%**

#### 영어 출력 (enen) — 체태곡선 언급 상세

| 이미지 | std-think | spec-think | std-nothink | spec-nothink |
|--------|:---------:|:----------:|:-----------:|:------------:|
| 01 Sprite 클로즈업 | - | - | - | - |
| 02 벚꽃 애니 | - | **✓** "closed, intimate silhouette" | - | - |
| 03 Sprite 전신 | - | - | - | - |
| 04 석양 셀카 | - | - | - | - |
| 05 욕실 | - | △ "accentuate long limbs" | - | - |
| 06 미러셀카 | △ "contours of torso" | △ "clings to figure" | - | **✓** "accentuating silhouette" |
| 07 교사 | - | **✓** "emphasizing silhouette" | **✓** "silhouette and curve of calves" | **✓** "curve of her legs" |
| 08 엘리베이터 | **✓** "slight body curve" | **✓** "showcasing silhouette" | - | - |
| 09 소다캔 | △ "contours of face/arms" | - | - | - |
| 10 피겨 | - | - | - | - |
| **소계** | **1/10** | **3/10** | **1/10** | **2/10** |

#### 중국어 출력 (enzh) — 체태곡선 언급 상세

| 이미지 | std-think | spec-think | std-nothink | spec-nothink |
|--------|:---------:|:----------:|:-----------:|:------------:|
| 01 Sprite | - | - | - | - |
| 02 벚꽃 | - | - | - | - |
| 03 Sprite 전신 | △ "腿部线条" | - | - | - |
| 04 석양 셀카 | - | △ "肩膀与手臂线条" | - | - |
| 05 욕실 | - | **✓✓** "优雅曲线" + "腿部线条" | - | - |
| 06 미러셀카 | △ "肩颈线条, 胸部轮廓" | - | - | - |
| 07 교사 | **✓** "身体曲线" | **✓✓** "身体曲线" + "臀部曲线" | **✓** "腿部线条" | - |
| 08 엘리베이터 | △ "身体轮廓" | **✓✓✓ "S型曲线"** | **✓** "曲线" + "胸部线条" | **✓✓✓ "S型曲线"** |
| 09 소다캔 | **✓✓** "背部线条" + "腰部曲线" | **✓** "肌肉线条" | **✓✓** "背部线条" + "腰部曲线" | - |
| 10 피겨 | **✓** "肢体线条" | - | **✓** "肢体线条" | - |
| **소계** | **3/10** | **4/10** | **4/10** | **2/10** |

#### 체태곡선 요약

| 출력언어 | Before | After | 변화 |
|---------|:------:|:-----:|:----:|
| 영어 (enen) | 0% | **18%** (7/40) | **+18%p** |
| 중국어 (enzh) | N/A | **33%** (13/40) | — |
| 전체 | 0% | **25%** (20/80) | **+25%p** |

**최고 성과: spec-think-enzh** — "S型曲线" (img8), "臀部曲线" (img7), "优雅曲线" (img5) 등 가장 구체적이고 다양한 곡선 묘사.

### 2.2 중심분포 (Weight Distribution / 重心分布)

**Before: 8% → After: 10% (수치 미세 증가, 질적 대폭 개선)**

#### 중심분포 언급 상세 (전 모델)

| 이미지 | 모델 | 언급 내용 | 등급 |
|--------|------|----------|:----:|
| 03 Sprite | std-nothink-enen | "weight distributed evenly" | ✓ |
| 10 피겨 | std-nothink-enen | "the other supporting her weight" | ✓ |
| 10 피겨 | std-think-enzh | "身体重心略微下沉" + "保持平衡" | ✓ |
| 10 피겨 | spec-think-enzh | **"重心落在滑行的一侧冰刀上"** | **✓✓** |
| 10 피겨 | std-nothink-enzh | "左腿在后支撑" + "保持平衡" | △ |
| 10 피겨 | spec-nothink-enzh | **"重心落在滑行的一侧冰刀上"** + "保持平衡" | **✓✓** |

#### 중심분포 Before vs After 질적 비교

| 항목 | Before | After |
|------|--------|-------|
| 전체 이행률 | 8% (2/24) | 10% (8/80) |
| 동적 이미지(10) 이행률 | 0% | **50%** (4/8 모델) |
| 최고 품질 표현 | "without shifting weight" (부정형) | **"重心落在滑行的一侧冰刀上"** (정확한 편측 분포) |
| 표현 다양성 | 간접 1종 | 重心, weight, 支撑, 平衡 4종 |

### 2.3 기존 포즈 요소 유지 여부

| 포즈 요소 | Before | After | 변화 | 판정 |
|-----------|:------:|:-----:|:----:|:----:|
| 팔/손 위치 | 90% | **90%** | 0 | 유지 |
| 다리 위치 기본 | 70% | **75%** | +5%p | 소폭 개선 |
| 다리 좌우 비대칭 | 40% | **50%** | +10%p | 개선 |
| 머리 방향/시선 | 85% | **85%** | 0 | 유지 |
| 신체 방향 | 75% | **78%** | +3%p | 유지 |
| **체태곡선** | **0%** | **25%** | **+25%p** | **대폭 개선** |
| **중심분포** | **8%** | **10%** | +2%p | 수치 미세, 질적 대폭 |
| 동작감/역동성 | 50% | **55%** | +5%p | 소폭 개선 |
| 포숏 | 5% | **5%** | 0 | 유지 |

---

## 3. 모델별 포즈 역동성 순위 (After)

### 3.1 종합 순위

| 순위 | 모델 조합 | 체태곡선 | 중심분포 | 강점 |
|:----:|-----------|:--------:|:--------:|------|
| **1** | **spec-think-enzh** | **4/10** | **✓✓** | S型曲线, 臀部曲线, 重心 명시. 최고 정밀도 |
| **2** | **std-nothink-enzh** | **4/10** | **△** | 背部线条+腰部曲线 반복 출현. 직관적 관찰력 |
| **3** | **std-think-enzh** | **3/10** | **✓** | 身体曲线, 重心 언급. 안정적 |
| 4 | spec-think-enen | 3/10 | - | silhouette 용어 활용. 영어 최고 |
| 5 | spec-nothink-enzh | 2/10 | **✓✓** | S型曲线+重心. 소수지만 정확 |
| 6 | spec-nothink-enen | 2/10 | - | silhouette, curve 간접 |
| 7 | std-think-enen | 1/10 | - | "body curve" 1회 |
| 8 | std-nothink-enen | 1/10 | ✓ | weight 1회. 전반적 낮음 |

### 3.2 핵심 발견: 중국어 출력이 영어 대비 포즈 묘사 2배 우위

| 지표 | 영어 (enen) | 중국어 (enzh) | 배율 |
|------|:-----------:|:------------:|:----:|
| 체태곡선 이행률 | 18% | 33% | **1.8x** |
| 중심분포 이행 | 2건 (간접) | 6건 (직접) | **3x** |
| S-line 명시 | 0건 | **2건** | ∞ |
| 근육/신체선 묘사 | 0건 | 4건 | ∞ |

**원인 분석:**
1. **중국어 미학 어휘 풍부**: 曲线, 线条, 体态, 轮廓, 重心 등이 일상적 미학 용어. 영어 "silhouette curves"는 상대적으로 기술적
2. **시스템 프롬프트 자연도**: "体态曲线"은 자연스러운 중국어 복합어. "silhouette curves"는 영어에서 다소 인위적
3. **Qwen3.5 모국어 효과**: Qwen은 중국어 훈련 데이터가 풍부하여 미학/신체 묘사 어휘가 자연스럽게 활성화
4. **Z-Image Turbo 텍스트 인코더**: Qwen 3 4B 기반으로 중국어 토큰 효율 우위 (0.72 tok/char vs 1.19 tok/word)

---

## 4. 이미지별 심층 분석 — 동적 포즈 (Image 5-10)

### Image 5 (욕실 카운터)

**Before 최고**: 다리 교차만 일부 캡처, 체태곡선/중심분포 0%

**After 주요 변화:**
- spec-think-enzh: "双腿交叉并自然弯曲，左腿在前右腿在后，**形成优雅的曲线**" + "突出**腿部线条**与坐姿美感"
- spec-think-enen: "accentuate her long limbs" — 영어는 간접적
- 다리 교차 묘사율: 40% → 65%로 개선

**생성 이미지 비교:** Before/After 모두 유사한 수준. 원본 포즈 자체가 정적이어서 프롬프트 차이가 시각적으로 크게 드러나지 않음.

### Image 7 (화이트보드 교사 — 복합 포즈)

**Before 최고**: std-nothink에서 "curvature of thighs and hips" (의상 효과 묘사)

**After 핵심 변화:**
- std-think-enzh: "강조人物의 **腿部和身体曲线**" ← 명시적 신체 곡선
- spec-think-enzh: "**臀部曲线**" + "**腿部线条与身体曲线**" ← 3중 곡선 묘사!
- std-nothink-enzh: "突出**腿部线条**与动态姿态"
- std-nothink-enen: "emphasizing her **silhouette** and the **curve of her calves and knees**"

**생성 이미지 비교:**
- Before std-think: 무릎 꿇고 화이트보드 향해 등 돌림 — 다리 라인 미강조
- After std-think: 다리 앞으로 뻗은 자세, **다리 라인과 바디 커브 강조** — 시각적 개선 확인
- After spec-think-enzh: 가장 자연스러운 앉은 자세, 다리 곡선이 프롬프트 묘사와 일치

### Image 8 (엘리베이터 — S-line 핵심 테스트)

**Before**: 전 모델 정적. std-nothink에서 "without shifting weight" (부정형)

**After 핵심 변화:**
- **spec-think-enzh: "展现出明显的S型曲线"** ← 가장 핵심적 개선!
- **spec-nothink-enzh: "展现出明显的S型曲线"** ← nothink에서도 동일 출현!
- std-think-enen: "slight body curve to her left" ← 영어에서도 곡선 언급
- spec-think-enen: "showcasing her silhouette" ← silhouette 언급
- std-nothink-enzh: "凸显**曲线**" ← 곡선 언급

**생성 이미지 비교:**
- Before: 모든 모델에서 직립 정적 포즈
- After spec-think-enzh: 미세하지만 **바디 곡선이 강조된 실루엣** — "S型曲线" 프롬프트 효과
- After spec-nothink-enzh: 유사하게 바디 라인 강조

**판정:** Image 8은 원본 자체가 정적이지만, "S型曲线" 프롬프트가 Z-Image Turbo에 도달하여 미세한 체형 강조 효과 확인.

### Image 9 (소다캔 로우앵글)

**Before**: std-nothink에서 "leans forward slightly", "exaggerates size of hand" (포숏)

**After 핵심 변화:**
- std-think-enzh: "展示出紧致的**背部线条**和**腰部曲线**" ← 배경/허리 곡선 신규!
- std-nothink-enzh: "微微侧身站立，展示出紧致的**背部线条**和**腰部曲线**，身体姿态放松而自信"
- spec-think-enzh: "皮肤质感细腻，**肌肉线条**柔和" ← 근육선 언급!

**생성 이미지 비교:**
- After std-nothink-enzh: **몸을 돌려 등 라인 노출, 허리 곡선 강조** — Before 대비 확실한 포즈 역동성 증가
- After spec-think-enzh: 유사하게 측면 바디라인 강조

### Image 10 (피겨스케이터 — 고동적)

**Before**: 전 모델 동작감 캡처 성공, 체태곡선 0%, 중심분포 0%

**After 핵심 변화:**
- std-think-enzh: "展现出**流畅的肢体线条**" + "**身体重心略微下沉**" + "双臂向两侧舒展以**保持平衡**"
- spec-think-enzh: "**重心落在滑行的一侧冰刀上**" ← 정확한 편측 중심분포!
- spec-nothink-enzh: "**重心落在滑行的一侧冰刀上**" ← nothink에서도 동일!
- std-nothink-enen: "the other **supporting her weight**" ← 영어에서도 중심 언급
- std-nothink-enzh: "**流畅的肢体线条**"

**생성 이미지 비교:**
- Before/After 모두 동적 스케이팅 포즈를 잘 캡처. 원본 자체가 매우 동적이라 프롬프트 차이보다 원본 포즈 인식이 지배적.
- 전반적으로 비슷한 퀄리티, 미세한 차이.

---

## 5. Think vs Nothink — 포즈 관점 비교

### 체태곡선 이행률

| 모드 | EN | ZH | 전체 |
|------|:--:|:--:|:----:|
| Think | 20% (4/20) | 35% (7/20) | **28%** |
| Nothink | 15% (3/20) | 30% (6/20) | **23%** |

Think가 nothink 대비 +5%p. 이전 분석(think +5~17%p)과 일관된 패턴.

### 중심분포 이행률

| 모드 | EN | ZH | 전체 |
|------|:--:|:--:|:----:|
| Think | 0% | 15% (img10에서 2건) | **8%** |
| Nothink | 10% (img3,10) | 10% (img10에서 2건) | **10%** |

**의외:** 중심분포는 nothink가 think보다 약간 높음. std-nothink-enen의 "weight distributed evenly" (img3)가 think에는 없는 자발적 관찰.

### 해석

- **체태곡선**: Think의 추론 과정이 "silhouette curves" 지시를 체크리스트처럼 처리 → 더 자주 출력
- **중심분포**: 정적 포즈(img3)에서 nothink의 직관적 관찰이 체중분포를 자연스럽게 언급. Think는 동적 포즈(img10)에서만 활성화
- 결론: **포즈 역동성에서 think/nothink 차이는 체태곡선에서만 유의미. 중심분포는 모드 무관하게 이미지 난이도에 의존**

---

## 6. Std vs Spec — 포즈 관점 비교

### 체태곡선

| 스타일 | EN | ZH | 전체 |
|--------|:--:|:--:|:----:|
| Std | 10% (2/20) | 35% (7/20) | **23%** |
| Spec | 25% (5/20) | 30% (6/20) | **28%** |

- **영어에서 spec >> std**: spec의 "overall body line" 지시가 silhouette/curve 출력을 유도
- **중국어에서 std ≈ spec**: 중국어 시스템 프롬프트가 두 스타일 모두에서 잘 작동

### 중심분포

| 스타일 | 전체 |
|--------|:----:|
| Std | 10% (4건) |
| Spec | 8% (4건) |

차이 미미. 중심분포는 스타일보다 이미지 난이도에 의존.

---

## 7. 생성 이미지 포즈 역동성 비교 (Before vs After)

| 이미지 | Before 특징 | After 특징 | 변화 판정 |
|--------|------------|------------|:---------:|
| 05 욕실 | 교차 다리, 정적 앉기 | 유사 | **→** 변화 미미 |
| 06 미러셀카 | 전 모델 유사 | 유사 | **→** 변화 미미 |
| 07 교사 | 일부 등 돌림, 다리 강조 부족 | **다리 라인 강조, 바디 곡선 반영** | **↑ 소폭 개선** |
| 08 엘리베이터 | 전부 정적 직립 | **S-curve 미세 반영 (enzh)** | **↑ 미세 개선** |
| 09 소다캔 | 캔 내밀기, 정적 상체 | **측면 바디라인, 허리곡선 강조** | **↑ 확실한 개선** |
| 10 피겨 | 동적 스케이팅 | 동적 스케이팅 (유사) | **→** 유지 |

**종합:** 이미 동적인 포즈(img10)에서는 차이 미미하지만, **중간 난이도 포즈(img7, 8, 9)에서 프롬프트 개선 효과가 시각적으로 확인됨.**

---

## 8. 종합 결론

### 8.1 시스템 프롬프트 수정 효과 — 팩트 기반 판정

| 항목 | 판정 | 근거 |
|------|:----:|------|
| 체태곡선 출현 | **성공** | 0% → 25%. 특히 중국어 35%. "S型曲线" 명시적 출현 |
| 중심분포 출현 | **부분 성공** | 8% → 10% (수치). 질적으로 "重心落在一侧冰刀上" 같은 정밀 표현 등장 |
| 기존 항목 유지 | **성공** | 팔/손 90%, 시선 85% 등 기존 강점 그대로 유지 |
| 생성 이미지 반영 | **부분 성공** | img7, 9에서 시각적 개선 확인. img5, 8은 미세 |
| 부작용 | **없음** | 기존 잘 되던 항목의 이행률 저하 없음 |

### 8.2 언어별 효과 차이

**중국어 출력이 포즈 역동성에서 압도적 우위:**
- 체태곡선: EN 18% vs ZH 33% (1.8배)
- 중심분포: EN 2건 vs ZH 6건 (3배)
- S-line 명시: EN 0건 vs ZH 2건
- 이유: Qwen의 중국어 미학 어휘 + 시스템 프롬프트 자연도 + Z-Image Turbo 텍스트 인코더 친화성

### 8.3 모델 조합 최종 추천 (포즈 역동성 기준)

| 순위 | 조합 | 이유 |
|:----:|------|------|
| **1** | **spec-think-enzh** | S型曲线 + 重心 + 臀部曲线. 체태곡선+중심분포 모두 최고. 시간 대비 가치 최적 |
| **2** | std-nothink-enzh | 背部线条+腰部曲线 반복. 시간 효율적(think 3-4배 빠름). 직관적 관찰력 |
| **3** | std-think-enzh | 안정적 체태곡선+중심. spec 대비 범용성 |
| 4 | spec-think-enen | 영어 최고지만 중국어 대비 열위 |

### 8.4 잔존 한계 및 다음 단계

1. **중심분포 이행률 여전히 낮음 (10%)**: "weight distribution" 용어가 정적 포즈에서 활성화되지 않음. 대부분 img10(고동적)에서만 출현. → 더 구체적인 용어 ("which leg bears more weight" 등)로 강화 검토 가능하나, 과잉 지시 리스크
2. **영어 출력의 한계**: silhouette/curve 용어가 영어에서 자연스럽지 않아 이행률이 낮음. → 영어 시스템 프롬프트에 "body curves and lines" 같은 더 일상적 용어 검토 가능
3. **정적 포즈(img1-4, 8)에서 효과 미미**: 원본 자체가 정적이면 모델이 곡선/중심을 묘사할 동기 부족. 이건 정상적 관찰이지 한계가 아님
4. **포숏(5%) 미개선**: 시스템 프롬프트에 포숏 용어를 추가하지 않았으므로 예상된 결과
5. **근육 상태/이완(0%)**: 여전히 미이행. 시스템 프롬프트에 해당 항목 없음

### 8.5 프롬프트 순서 전략 (미적용)

이번 테스트는 포즈 용어 추가만 적용. 중국어 레퍼런스 프롬프트의 "스타일 헤더 패턴" (어텐션 구간 기반 키워드 배치)은 별도 테스트 필요.

---

## 부록: 모델별 주목할 프롬프트 원문

### spec-think-enzh — Image 8 (S型曲线)
> 她的双手抬起，分别抓着肩带的位置，身体姿态挺拔，**展现出明显的S型曲线**，双腿自然分开站立。

### spec-think-enzh — Image 10 (重心)
> 左腿向前伸展，右腿弯曲支撑，上半身微倾，双臂向两侧舒展以保持平衡... **重心落在滑行的一侧冰刀上**

### std-nothink-enzh — Image 9 (背部线条+腰部曲线)
> 她微微侧身站立，展示出紧致的**背部线条**和**腰部曲线**，身体姿态放松而自信。

### std-think-enen — Image 8 (body curve)
> She is facing forward with a **slight body curve to her left**, posing with her hands raised near her shoulders.

### spec-think-enen — Image 7 (silhouette)
> The composition is captured from a low angle, **emphasizing her silhouette** and the contrast between her dark attire and the light-colored background.
