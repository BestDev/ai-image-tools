# 포즈 분석 보고서 — 시스템 프롬프트 수정 전 (Baseline)

10장 이미지 기준, 포즈 역동성 분석. 시스템 프롬프트 수정 전(old) 결과.
수정 후 결과와 비교하기 위한 베이스라인.

> 분석일: 2026-03-26
> 시스템 프롬프트: `silhouette curves`, `weight distribution` 추가 **이전** 버전

---

## 테스트 이미지 구성

| # | 이미지 | 포즈 유형 | 난이도 |
|---|--------|----------|:---:|
| 01 | Sprite 병 클로즈업 | 정적 서기 | 하 |
| 02 | 벚꽃 애니 소녀 | 정적 앉기 | 하 |
| 03 | Sprite 전신 | 정적 서기 | 하 |
| 04 | 애니 석양 셀카 | 약간 동적 (기대기) | 중 |
| 05 | 욕실 카운터 | **동적 앉기** (다리 교차, 기대기) | 중 |
| 06 | 미러 셀카 | **팔 뒤로** (한 팔 머리 뒤) | 중 |
| 07 | 화이트보드 교사 | **복합** (쪼그려앉기+글쓰기+다리 꼬기) | 상 |
| 08 | 엘리베이터 | **정면 서기** (스트랩 잡기) | 중 |
| 09 | 소다캔 로우앵글 | **역동적** (팔 뻗기+포숏) | 상 |
| 10 | 피겨스케이터 | **고동적** (스케이팅+팔 펼침+체중이동) | 상 |

---

## 포즈 프롬프트 분석 — 이미지 5-10 (신규 이미지)

### Image 5 (욕실 카운터 — 다리 교차, 턱 받침)

**원본 포즈 특성**: 대리석 카운터 위에 앉음, 왼손으로 턱 받침, 다리 교차(발목), 오른손 핸드백 체인, 하이힐, S형 바디라인

| 모델 | 포즈 서술 | 체태곡선 | 중심분포 | 다리비대칭 |
|------|----------|:---:|:---:|:---:|
| Qwen std-think | "sits atop...angling her body slightly to the left, chin resting on left hand, legs crossed at ankles" | ✗ | ✗ | ✓ 교차 |
| Qwen spec-think | "sits...left arm rests on counter, hand near face" | ✗ | ✗ | ✗ |
| Qwen std-nothink | "sits...three-quarter pose, body angled slightly left, head tilts right" | ✗ | ✗ | ✓ "crossed at ankles" |
| Qwen spec-nothink | "sits...left arm rests, hand near face" | ✗ | ✗ | ✗ |
| Joy std (tag) | "sitting...resting chin on right hand, left leg bent, right leg extended" | ✗ | ✗ | ✓ 좌우구분 |
| Joy spec (tag) | "sitting...resting chin on right hand, left leg bent" | ✗ | ✗ | △ |

**결론**: 전 모델 체태곡선/중심분포 0%. 다리 교차는 일부 모델만 캡처.

### Image 6 (미러 셀카 — 한 팔 머리 뒤)

**원본 포즈 특성**: 한 팔 머리 뒤로, 반대 손 스마트폰, 약간 틀어진 자세

| 모델 | 포즈 서술 | 체태곡선 | 중심분포 | 팔 비대칭 |
|------|----------|:---:|:---:|:---:|
| Qwen std-think | "right arm bent, hand behind head; left hand holds phone" | ✗ | ✗ | ✓ |
| Qwen spec-think | "left hand rests behind head, right grips phone" | ✗ | ✗ | ✓ |
| Qwen std-nothink | "right arm raised behind head, left hand holds phone" | ✗ | ✗ | ✓ |
| Joy std (tag) | "right hand holding phone, left hand behind head" | ✗ | ✗ | ✓ |

**결론**: 팔 비대칭은 전 모델 캡처. 체태곡선/중심분포는 0%.

### Image 7 (화이트보드 교사 — 복합 포즈)

**원본 포즈 특성**: 바닥에 앉아, 몸 비틀어 화이트보드에 글쓰기, 한 다리 구부림, 스타킹+힐, 역동적 체형 강조

| 모델 | 포즈 서술 | 체태곡선 | 중심분포 | 다리묘사 |
|------|----------|:---:|:---:|:---:|
| Qwen std-think | "kneels on floor, leaning against whiteboard, angled slightly right, turns head to gaze at camera, legs bent in seated position" | ✗ | ✗ | △ "bent at knees" |
| Qwen spec-think | "sits on floor leaning against whiteboard, left arm on knee" | ✗ | ✗ | ✗ |
| Qwen std-nothink | "sits...leaning forward, one knee bent, other extended, revealing curvature of thighs and hips" | **△ 부분** | ✗ | ✓ 좌우 |
| Joy std (tag) | "sitting on floor, low camera angle, emphasis on legs and outfit" | ✗ | ✗ | △ |

**주목**: std-nothink에서 "revealing the curvature of thighs and hips through the tights"라는 체형 묘사가 등장. 하지만 이건 의상 효과 묘사이지 포즈 역동성 묘사는 아님.

### Image 8 (엘리베이터 — 정면 서기)

**원본 포즈 특성**: 정면 서기, 양손 스트랩 잡기, 약간 어깨 안쪽, 자신감 포즈

| 모델 | 포즈 서술 | 체태곡선 | 중심분포 | 특이사항 |
|------|----------|:---:|:---:|------|
| Qwen std-think | "stands facing forward, hands raised near neck holding straps" | ✗ | ✗ | 정적 |
| Qwen spec-think | "faces forward, tilted slightly, hands raised near collarbone" | ✗ | ✗ | 정적 |
| Qwen std-nothink | "stands...legs positioned with slight separation, standing naturally without crossing or shifting weight" | ✗ | **△ 역표현** | "without shifting weight" 명시 |
| Joy std (tag) | "standing...hands holding top of dress, confident expression" | ✗ | ✗ | 정적 |

**주목**: std-nothink에서 "without crossing or shifting weight"라는 표현이 있음. 중심분포 개념은 인식하지만 "없다"고 보고한 것. 시스템 프롬프트에 weight distribution이 없어서 적극적으로 묘사하지 않음.

### Image 9 (소다캔 로우앵글 — 포숏+역동적)

**원본 포즈 특성**: 팔을 카메라 쪽으로 뻗어 캔 제시, 로우앵글, 포숏(foreshortening), 체중 약간 앞으로

| 모델 | 포즈 서술 | 체태곡선 | 중심분포 | 포숏 |
|------|----------|:---:|:---:|:---:|
| Qwen std-think | "extends right arm toward camera, holding can...left hand supports from side" | ✗ | ✗ | ✗ 암시적 |
| Qwen spec-think | "holding can directly toward camera lens...left arm rests at side" | ✗ | ✗ | ✗ |
| Qwen std-nothink | "extends right arm...creating sense of immediacy in foreground, leans forward slightly" | ✗ | △ "leans forward" | ✓ "exaggerates size of hand" |
| Joy std (tag) | "pointing can towards camera, low angle, right arm extended" | ✗ | ✗ | ✗ |

**주목**: std-nothink에서 "leans forward slightly"(체중 이동), "exaggerates the size of the hand and can"(포숏 인식). 가장 정확한 포즈 묘사.

### Image 10 (피겨스케이터 — 고동적)

**원본 포즈 특성**: 스케이팅 중, 팔 양옆 수평 펼침, 한 다리 앞+한 다리 뒤, 상체 앞 기울임, 머리카락 날림, 체중 한 다리에 집중

| 모델 | 포즈 서술 | 체태곡선 | 중심분포 | 동작감 |
|------|----------|:---:|:---:|:---:|
| Qwen std-think | "body angled slightly forward, arms extended wide...graceful open posture, hair flying dynamically, speed of movement" | ✗ | △ "forward" | ✓ "speed", "dynamically" |
| Qwen spec-think | "body angled forward in motion, arms extended outward, knees bent, gliding" | ✗ | △ "forward" | ✓ "in motion", "gliding" |
| Qwen std-nothink | "executing a graceful glide, arms extended horizontally, gaze slightly upward, legs crossed at ankles, ponytail flows due to motion" | ✗ | ✗ | ✓ "glide", "motion" |
| Joy std (tag) | "mid-motion, slightly leaning forward, arms extended, dynamic pose, motion captured" | ✗ | △ "leaning forward" | ✓ "dynamic", "mid-motion" |

**결론**: 전 모델이 동작감은 캡처하지만, 체태곡선(graceful arc), 체중분포(한 다리에 체중)는 명시하지 않음.

---

## 전체 포즈 요소 이행률 (수정 전 베이스라인)

10장 이미지 × 4개 모델(std-think, spec-think, std-nothink, joy-std) 기준

| 포즈 요소 | 이행률 | 비고 |
|-----------|:---:|------|
| 팔/손 위치 | **90%** | 전 모델 양호 |
| 다리 위치 기본 | **70%** | "bent", "extended" 수준 |
| 다리 좌우 비대칭 | **40%** | 일부만 좌우 분리 묘사 |
| 머리 방향/시선 | **85%** | 양호 |
| 신체 방향 | **75%** | "angled slightly", "facing forward" |
| **체태곡선 (S-line)** | **0%** | 전 모델 전 이미지 미언급 |
| **중심분포 (weight)** | **8%** | std-nothink img8,9에서만 간접 언급 |
| **동작감/역동성** | **50%** | 동적 이미지(9,10)에서만 |
| 포숏(foreshortening) | **5%** | std-nothink img9에서만 |
| 근육 상태/이완 | **0%** | 전 모델 미언급 |

---

## 모델별 포즈 묘사 특성

### Qwen3.5 std-think
- 팔/손 위치 정확
- 기본 포즈 묘사 양호
- 체태곡선, 중심분포 완전 부재
- 동적 이미지에서 "speed", "dynamically" 사용하지만 신체 곡선은 무시

### Qwen3.5 spec-think
- std-think과 거의 동일한 포즈 묘사 수준
- "overall silhouette" 지시가 있었으나 이행하지 않음
- 간결한 경향 — 포즈 묘사가 std보다 짧은 경우 있음

### Qwen3.5 std-nothink
- **의외로 포즈 묘사에서 가장 세밀한 경우 있음**
- img7: "curvature of thighs and hips" (체형 묘사)
- img8: "without shifting weight" (중심분포 인식 증거)
- img9: "leans forward", "exaggerates size of hand" (포숏 인식)
- 단, 이건 시스템 프롬프트 지시가 아닌 모델 자체 판단

### JoyCaption std (태그 형식)
- 태그 특성상 포즈 관련 키워드 다수 생성: "dynamic pose", "low angle", "mid-motion"
- 체태곡선, 중심분포는 역시 부재
- img10에서 가장 동적인 이미지 생성 (피겨스케이터)
- img9에서 의상 오인 (분리 세트 → 원피스)

---

## 생성 이미지 포즈 비교 (Z-Image Turbo 출력)

| 이미지 | 최고 포즈 역동성 | 최고 바디라인 | 가장 정적 |
|--------|:---:|:---:|:---:|
| 05 (욕실) | spec-think | 전체 양호 | — |
| 06 (미러셀카) | 전체 유사 | std/spec-think | — |
| 07 (교사) | std-think (가장 자연스러운 글쓰기 동작) | joy-std | spec-think |
| 08 (엘리베이터) | 전체 유사 (전부 정적) | 전체 유사 | 전부 |
| 09 (소다캔) | std-think | std/spec-think | joy-std |
| 10 (피겨) | **joy-std** (가장 동적, 깊은 무릎 굽힘) | joy-std | — |

---

## 핵심 발견 (수정 전 베이스라인)

1. **체태곡선(S-line)과 중심분포(weight distribution)는 전 모델 0-8%**: 시스템 프롬프트에 해당 용어가 없어서 모델이 묘사하지 않음.

2. **std-nothink가 의외의 포즈 세밀함**: img7, 8, 9에서 think보다 더 세밀한 포즈 묘사. "curvature", "without shifting weight", "leans forward" 등. 이는 nothink 모드에서 직관적 관찰이 때로 think의 구조적 서술보다 자유로운 표현을 허용하기 때문으로 추정.

3. **JoyCaption 태그 형식의 장단**: img10(피겨)에서 가장 동적 이미지 생성, 하지만 img9에서 의상 오인. 태그 형식은 "dynamic pose" 같은 생성 모델 친화적 키워드를 직접 출력하여 이미지 역동성에 유리.

4. **Image 8(엘리베이터)은 전 모델 정적**: 원본 자체가 정면 정적 포즈이므로 모델이 정확히 반영한 것. 이건 VLM의 한계가 아니라 올바른 관찰.

5. **동적 포즈(img 9, 10)에서 차이가 가장 큼**: 정적 포즈에서는 모든 모델이 유사하지만, 동적 포즈에서 모델/스타일 간 차이가 극대화.

---

## 수정 후 비교를 위한 체크리스트

시스템 프롬프트에 `silhouette curves`와 `weight distribution` 추가 후, 동일 10장으로 비교할 항목:

- [ ] 체태곡선 언급 빈도 (0% → ?)
- [ ] 중심분포 언급 빈도 (8% → ?)
- [ ] 생성 이미지 포즈 역동성 변화
- [ ] 기존 잘 되던 항목(팔/손, 시선, 의상) 유지 여부
- [ ] Image 7, 9, 10 같은 고난이도 포즈에서의 개선 정도
