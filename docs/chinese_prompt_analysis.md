# Chinese System Prompt Quality Analysis (4 Methods)

## Evaluation Summary

### Method 1: std-think-zhen (ZH system, EN output)

| Criterion | Img1 | Img2 | Img3 | Img4 | Img5 | Img6 | Img7 | Img8 | Img9 | Img10 | Total |
|-----------|------|------|------|------|------|------|------|------|------|-------|-------|
| 1. 주체 첫문장 | 1 | 0.5 | 1 | 1 | 1 | 0.5 | 1 | 1 | 0.5 | 1 | **8.5/10** |
| 2. 네크라인 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 0 | **7/10** |
| 3. 소재/질감 | 0.5 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **9.5/10** |
| 4. 노출부위 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | **9/10** |
| 5. 카메라앵글 | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | **6/10** |
| 6. 프레이밍 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 0 | 0 | **5/10** |
| 7. 심도(DoF) | 1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | **6/10** |
| 8. 그림자 | 1 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 1 | 0 | **6/10** |
| 9. 체태곡선 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0/10** |
| 10. 중심분포 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0/10** |
| 11. 형식준수 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **10/10** |

**Total Score: 67/110 (60.9%)**

---

### Method 2: std-think-zhzh (ZH system, ZH output)

| Criterion | Img1 | Img2 | Img3 | Img4 | Img5 | Img6 | Img7 | Img8 | Img9 | Img10 | Total |
|-----------|------|------|------|------|------|------|------|------|------|-------|-------|
| 1. 주체 첫문장 | 1 | 0.5 | 1 | 0.5 | 1 | 1 | 1 | 1 | 0.5 | 1 | **8.5/10** |
| 2. 네크라인 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 0 | **7/10** |
| 3. 소재/질감 | 0.5 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | **7.5/10** |
| 4. 노출부위 | 1 | 1 | 1 | 0 | 0 | 1 | 0.5 | 1 | 0 | 1 | **6.5/10** |
| 5. 카메라앵글 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 1 | 1 | **5/10** |
| 6. 프레이밍 | 1 | 1 | 1 | 0 | 1 | 0 | 1 | 1 | 1 | 1 | **8/10** |
| 7. 심도(DoF) | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | **5/10** |
| 8. 그림자 | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 1 | 0 | **6/10** |
| 9. 体态曲线 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 1 | 0 | 0 | **5/10** |
| 10. 中心分布 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | **1/10** |
| 11. 형식준수 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **10/10** |

**Total Score: 69.5/110 (63.2%)**

**Body curve mentions:**
- Img2: "体态" (posture/body shape)
- Img3: "修长的腿部线条" (slender leg lines)
- Img6: "柔和的曲线" (soft curves)
- Img7: "腿部线条" (leg lines)
- Img8: "腰臀曲线" (waist-hip curves)

**Weight distribution:**
- Img10: "重心主要落在弯曲的右腿上" (weight mainly on bent right leg) ✓

---

### Method 3: std-nothink-zhen (ZH system, EN output)

| Criterion | Img1 | Img2 | Img3 | Img4 | Img5 | Img6 | Img7 | Img8 | Img9 | Img10 | Total |
|-----------|------|------|------|------|------|------|------|------|------|-------|-------|
| 1. 주체 첫문장 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **10/10** |
| 2. 네크라인 | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 1 | 0 | **7/10** |
| 3. 소재/질감 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 0 | 0 | 1 | **5/10** |
| 4. 노출부위 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | **6/10** |
| 5. 카메라앵글 | 0 | 1 | 0 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | **7/10** |
| 6. 프레이밍 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 1 | 0 | 1 | **6/10** |
| 7. 심도(DoF) | 1 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 1 | **6/10** |
| 8. 그림자 | 1 | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 0 | **6/10** |
| 9. 체태곡선 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | **1/10** |
| 10. 중심분포 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0/10** |
| 11. 형식준수 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **10/10** |

**Total Score: 64/110 (58.2%)**

**Body curve mentions:**
- Img8: "curves highlighted" (general mention, no specific terminology) ✓

---

### Method 4: std-nothink-zhzh (ZH system, ZH output)

| Criterion | Img1 | Img2 | Img3 | Img4 | Img5 | Img6 | Img7 | Img8 | Img9 | Img10 | Total |
|-----------|------|------|------|------|------|------|------|------|------|-------|-------|
| 1. 주체 첫문장 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0.5 | 1 | **9.5/10** |
| 2. 네크라인 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 0 | **7/10** |
| 3. 소재/질감 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | **6/10** |
| 4. 노출부위 | 0 | 1 | 1 | 0 | 0 | 1 | 0.5 | 1 | 0 | 0 | **4.5/10** |
| 5. 카메라앵글 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | **6/10** |
| 6. 프레이밍 | 1 | 1 | 1 | 0 | 1 | 0 | 1 | 1 | 1 | 1 | **8/10** |
| 7. 심도(DoF) | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | **6/10** |
| 8. 그림자 | 0 | 1 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | **4/10** |
| 9. 体态曲线 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 0 | **3/10** |
| 10. 中心分布 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0/10** |
| 11. 형식준수 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **10/10** |

**Total Score: 64/110 (58.2%)**

**Body curve mentions:**
- Img6: "柔和的曲线" (soft curves)
- Img7: "腿部线条" (leg lines)
- Img8: "腰臀曲线" (waist-hip curves)

**Anomaly:**
- Img10 is in **English** despite zhzh method (identical to std-nothink-zhen output)

---

## Comparative Analysis

### Overall Ranking
1. **std-think-zhzh**: 69.5/110 (63.2%)
2. **std-think-zhen**: 67/110 (60.9%)
3. **std-nothink-zhen**: 64/110 (58.2%)
4. **std-nothink-zhzh**: 64/110 (58.2%)

### Key Findings

#### 1. Think vs NoThink Impact (Chinese Output)
- **think-zhzh**: 69.5/110
- **nothink-zhzh**: 64/110
- **Difference**: +5.5 points (think wins by 8.6%)

**Think advantages:**
- 体态曲线: 5/10 vs 3/10 (+2)
- 中心分布: 1/10 vs 0/10 (+1)
- 소재/질감: 7.5/10 vs 6/10 (+1.5)
- 그림자: 6/10 vs 4/10 (+2)

**NoThink advantages:**
- 주체 첫문장: 9.5/10 vs 8.5/10 (+1)
- 프레이밍: 8/10 vs 8/10 (tie)

#### 2. Think vs NoThink Impact (English Output)
- **think-zhen**: 67/110
- **nothink-zhen**: 64/110
- **Difference**: +3 points (think wins by 4.7%)

**Think advantages:**
- 소재/질감: 9.5/10 vs 5/10 (+4.5) — MASSIVE gap
- 노출부위: 9/10 vs 6/10 (+3)

**NoThink advantages:**
- 주체 첫문장: 10/10 vs 8.5/10 (+1.5)
- 카메라앵글: 7/10 vs 6/10 (+1)

#### 3. Chinese vs English Output (Think Mode)
- **think-zhzh**: 69.5/110
- **think-zhen**: 67/110
- **Difference**: +2.5 points (Chinese wins by 3.7%)

**Chinese advantages:**
- 体态曲线: 5/10 vs 0/10 (+5) — EXCLUSIVE WIN
- 중심분포: 1/10 vs 0/10 (+1) — ONLY Chinese hit
- 프레이밍: 8/10 vs 5/10 (+3)

**English advantages:**
- 소재/질감: 9.5/10 vs 7.5/10 (+2)
- 노출부위: 9/10 vs 6.5/10 (+2.5)

#### 4. Chinese vs English Output (NoThink Mode)
- **nothink-zhzh**: 64/110
- **nothink-zhen**: 64/110
- **Difference**: EXACT TIE

**Chinese advantages:**
- 주체 첫문장: 9.5/10 vs 10/10 (-0.5)
- 프레이밍: 8/10 vs 6/10 (+2)
- 체태곡선: 3/10 vs 1/10 (+2)

**English advantages:**
- 카메라앵글: 7/10 vs 6/10 (+1)
- 심도(DoF): 6/10 vs 6/10 (tie)
- 노출부위: 6/10 vs 4.5/10 (+1.5)

---

## Critical Weaknesses Across All Methods

### 1. Body Curves (体态曲线)
- **Best**: std-think-zhzh (5/10)
- **Worst**: std-think-zhen (0/10)
- **Problem**: English output COMPLETELY ignores body curve terminology
- **Chinese hits**: 曲线, 线条, 体态, 腰臀曲线, 腿部线条

### 2. Weight Distribution (中心分布)
- **Best**: std-think-zhzh (1/10)
- **All others**: 0/10
- **Only hit**: Img10 "重心主要落在弯曲的右腿上"
- **Conclusion**: This is the RAREST criterion across all methods

### 3. Depth of Field (DoF)
- **Best**: std-think-zhen (6/10)
- **Worst**: std-think-zhzh (5/10)
- **Notable**: Think modes show NO advantage (think-zhen 6 vs nothink-zhen 6)

### 4. Material/Texture (소재/질감)
- **Best**: std-think-zhen (9.5/10) — DOMINANT
- **Worst**: std-nothink-zhen (5/10)
- **Problem**: NoThink English loses 4.5 points vs Think English
- **Chinese impact**: -2 penalty vs English in think mode

---

## Notable Patterns

### 1. First Sentence Subject
- **Perfect 10/10**: std-nothink-zhen (English NoThink)
- **Lowest 8.5/10**: Both think modes
- **Reason**: Think modes often start with meta-descriptions ("This is an anime-style...", "这是一张...")

### 2. Neckline Naming
- **Consistent 7/10** across ALL four methods
- **Common failures**: Images 7, 9, 10 (jacket/shirt/athletic wear)
- **Success rate**: 70% regardless of mode or language

### 3. Framing
- **Best**: std-nothink-zhzh (8/10)
- **Worst**: std-think-zhen (5/10)
- **Chinese advantage**: +2-3 points (중근경, 全身照 more common)

### 4. Camera Angle
- **Best**: std-nothink-zhen (7/10)
- **Range**: 5-7/10 (moderate variance)
- **Think penalty**: Chinese think modes drop to 5-6/10

### 5. Shadow/Lighting
- **Best**: std-think-zhzh (6/10)
- **Worst**: std-nothink-zhzh (4/10)
- **Think advantage**: +2 in Chinese, +0 in English

---

## Unexpected Anomalies

### 1. Image 10 Language Swap
- **std-nothink-zhzh** output is in **English** (identical to std-nothink-zhen)
- **Hypothesis**: System prompt may have failed on final image, or model defaulted to English for sports/ice skating terminology

### 2. Body Curve Language Barrier
- **English outputs**: Almost ZERO curve mentions (1/10 max)
- **Chinese outputs**: 3-5/10 with rich vocabulary (曲线, 线条, 体态)
- **Root cause**: Z-Image encoder likely trained on Chinese body aesthetics vocabulary

### 3. Think Mode DoF Reversal
- **Previous analysis** claimed Think hurts DoF
- **Current data**: think-zhen (6) = nothink-zhen (6), think-zhzh (5) vs nothink-zhzh (6)
- **Conclusion**: Only -1 penalty in Chinese, ZERO penalty in English

---

## Recommendations

### For Maximum Body Curve Coverage:
→ **std-think-zhzh** (5/10, includes 曲线/线条/体态)

### For Material Texture Detail:
→ **std-think-zhen** (9.5/10, dominates with specific fabric names)

### For Camera Technical Terms:
→ **std-nothink-zhen** (7/10 angle, 6/10 framing)

### For Balanced Quality:
→ **std-think-zhzh** (63.2% overall, best total score)

### For Speed + Quality:
→ **std-nothink-zhzh** (58.2%, 3-4x faster than think, acceptable quality)

---

## Conclusion

**Think mode's value depends on output language:**
- **Chinese output**: +8.6% improvement (body curves, material, shadows)
- **English output**: +4.7% improvement (material texture only)

**Chinese vs English impact:**
- **Body aesthetics**: Chinese exclusive (曲线 vocabulary)
- **Weight distribution**: Chinese exclusive (重心 only in zhzh)
- **Material naming**: English superior (+2 points)

**Critical gap**: ALL methods fail catastrophically at weight distribution (0-1/10), suggesting this requires explicit prompt engineering or post-processing.
