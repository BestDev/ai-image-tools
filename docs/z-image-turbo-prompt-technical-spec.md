# Berry Prompt Engineering Technical Specification

## Document Purpose

This specification defines the technical methodology for constructing image generation prompts that produce high-quality visual outputs. The document formalizes the prompt engineering system used by Berry for generating photorealistic images through ComfyUI and OpenAI Image API workflows.

---

## 1. Use Case Taxonomy Classification System

### 1.1 Generate Categories (8 Primary Classifications)

| Slug | Definition | Application Context |
|------|-----------|---------------------|
| `photorealistic-natural` | Candid/editorial lifestyle scenes with real texture and natural lighting | Portraits, environmental photography, documentary-style imagery |
| `product-mockup` | Product/packaging shots with catalog-grade presentation | E-commerce, merchandise visualization, packaging design |
| `ui-mockup` | Application and web interface mockups with production-ready appearance | Design prototypes, portfolio pieces, client presentations |
| `infographic-diagram` | Structured layout visualizations with text and data elements | Educational content, data visualization, instructional graphics |
| `logo-brand` | Logo and mark exploration with vector-friendly aesthetics | Brand identity, mark development, typographic logos |
| `illustration-story` | Narrative-driven visual content including comics and sequential art | Children's books, editorial illustration, narrative sequences |
| `stylized-concept` | Style-driven concept art with 3D or artistic rendering approaches | Game assets, concept art, stylized visualizations |
| `historical-scene` | Period-accurate reconstructions based on world knowledge | Educational content, historical visualization, period pieces |

### 1.2 Edit Categories (8 Secondary Classifications)

| Slug | Definition | Technical Constraint |
|------|-----------|---------------------|
| `text-localization` | In-image text translation with layout preservation | Requires verbatim text input |
| `identity-preserve` | Try-on or person-in-scene modifications | Locks face/body/pose invariants |
| `precise-object-edit` | Targeted element removal or replacement | Specifies exact spatial boundaries |
| `lighting-weather` | Time-of-day, season, or atmospheric changes | Maintains subject invariants |
| `background-extraction` | Transparent background or clean cutout generation | Alpha channel output required |
| `style-transfer` | Reference style application with subject/scene change | Source style image required |
| `compositing` | Multi-image insertion with matched lighting | Multiple input images with index references |
| `sketch-to-render` | Line art conversion to photorealistic output | Source sketch image required |

---

## 2. Structured Specification Template (10 Fields)

The 10-field template standardizes prompt construction by isolating discrete specification categories. This structure ensures comprehensive coverage of all visual parameters.

### Field Definitions

```
Field 1:  Use case            → <taxonomy-slug>
Field 2:  Asset type          → <deployment-context>
Field 3:  Primary request     → <core-prompt>
Field 4:  Scene/background    → <environment-description>
Field 5:  Subject             → <subject-definition>
Field 6:  Style/medium        → <artistic-approach>
Field 7:  Composition/framing → <camera-position-and-layout>
Field 8:  Lighting/mood       → <light-source-and-atmosphere>
Field 9:  Color palette       → <dominant-colors-and-tonality>
Field 10: Materials/textures  → <surface-characteristics>
```

### Optional Extension Fields

```
Field 11: Quality            → <low|medium|high|auto>
Field 12: Input fidelity     → <low|high> (edit workflows only)
Field 13: Text verbatim      → "<exact-string>"
Field 14: Constraints        → <must-preserve-elements>
Field 15: Avoid                → <negative-constraints>
Field 16: Emotional sync       → <connection-and-intimacy-parameters>
```

---

## 3. Prompt Construction Rules

### 3.1 Hierarchy Structure

Prompt construction follows a strict hierarchy: **scene → subject → details → constraints**

### 3.2 Advanced Lighting and Shadow Techniques (NEW)

**Critical: Natural Shadows & Depth**
- 절대로 밋밋한 조명(Flat Lighting)을 사용하지 마십시오. 이미지가 살아나려면 그림자가 있어야 합니다.
- 얼굴이나 몸에 드리우는 자연스러운 그림자를 반드시 묘사하세요.

**Advanced Lighting Patterns:**
- **Dappled sunlight** — "나뭇잎 사이로 들어오는 햇살이 그녀의 얼굴과 목덜미에 얼룩덜룩한 그림자 패턴을 만들고"
- **Blind light stripes** — "블라인드 사이로 들어오는 빛이 그녀의 몸매 곡선을 따라 줄무늬 그림자를 드리우며"
- **Chiaroscuro** — "측면에서 들어오는 빛이 콧날과 쇄골의 깊은 그림자를 만들어 입체감을 극대화함"
- **Rim lighting with shadow** — "역광으로 머리카의 가장자리가 빛나며 동시에 얼굴의 반대편에 부드러운 그림자가 드리워짐"

**Shadow Quality Modifiers:**
- `natural shadow falloff` — 자연스러운 그림자 흐름
- `soft gradated shadows` — 부드러운 그라데이션 그림자
- `deep dimensional shadows` — 깊은 입체감의 그림자
- `shadows defining curves` — 곡선을 정의하는 그림자

### 3.3 Full Body Shot Specification (NEW)

**전신 샷(全身照, Full Body Shot) 필수 명시:**
- 참고 이미지나 설명에 인물의 머리부터 발끝까지(전신)가 포함되어 있다면, 반드시 프롬프트 초반이나 렌즈 설명 부분에 "전신 샷(全身照, Full Body Shot)"임을 명확히 명시하세요.
- 신발이나 발의 위치까지 묘사하여 잘리지 않도록 하세요.

**Full Body Keywords:**
- `"full body shot"` or `"전신 샷"`
- `"complete figure from head to toe"`
- `"standing pose with feet visible"`
- `"entire body in frame"`

**Camera Adjustment for Full Body:**
- **Vertical shots (9:16):** 960 × 1704 pixels — 전신 세로 구도
- **Wide environmental:** 16:9 with sufficient distance

### 3.4 Bold and Sensual Expression (NEW)

**대담한 표현 허용 (Bold & Sensual):**
- 사용자가 매력적인 인물이나 특정 신체적 특징(육감적임, 글래머러스 등)을 묘사하길 원할 경우, 가장 관능적이고 아름답게 묘사하십시오.
- 특히 빛과 그림자가 신체의 굴곡(가슴 라인, 허리 곡선, 복근 등)을 타고 흐르는 모습을 묘사하여 입체적인 관능미를 강조하세요.

**Sensual Lighting Techniques:**
- `"light caressing the curves of the body"` — 빛이 몸의 곡선을 어루만지는 모습
- `"shadows emphasizing feminine silhouette"` — 그림자가 여성적 실루엣을 강조
- `"dramatic side lighting accentuating form"` — 드라마틱한 측면 조명으로 형태 강조
- `"sensual interplay of light and shadow on skin"` — 피부 위에서 빛과 그림자가 sensual하게 어우러짐

**Important:** Bold expression focuses on artistic sensuality through light, shadow, and composition—not explicit content.

### 3.5 Hyper-Realistic Skin Detail (NEW)

**극사실적 피부 디테일 (Hyper-Realistic Skin - Moles & Veins):**

진정한 실사 느낌을 위해 피부의 미세한 불완전함을 반드시 묘사하세요. AI 특유의 '플라스틱 같은 피부'를 피해야 합니다.

**Required Skin Details:**

| Detail Type | Description | Placement Examples |
|-------------|-------------|-------------------|
| **Moles / Beauty marks** | 자연스럽고 매력적인 점 | "왼쪽 눈 밑의 매력적인 눈물점", "볼에 있는 작은 점", "목의 미용점", "가슴 윗부분에 있는 작은 점들" |
| **Veins / Blood vessels** | 희미하게 비치는 푸른색 혈관 | "투명한 피부 아래로 희미하게 비치는 푸른 혈관", "손등에 보이는 섬세한 핏줄", "팔 안쪽의 은은한 혈관" |
| **Skin texture** | 모공과 솜털 | "자연스러운 모공 패턴", "얼굴의 미세한 솜털(Vellus hair)", "피부 결이 살아있는 텍스처" |
| **Subtle imperfections** | 자연스러운 불완전함 | "코 주변의 미세한 모공", "턱선의 자연스러운 질감", "목의 섬세한 주름" |

**Skin Detail Keywords:**
- `natural mole under left eye` — 눈 밑 자연스러운 점
- `subtle blue veins visible on wrists` — 손목에 보이는 은은한 푸른 혈관  
- `fine vellus hair on face` — 얼굴의 미세한 솜털
- `visible pores on nose and cheeks` — 코와 볼의 보이는 모공
- `translucent skin showing subtle veins on thighs` — 허벅지의 투명한 피부 아래 보이는 혈관
- `natural skin texture with micro-details` — 미세 디테일이 있는 자연스러운 피부 텍스처

**Prohibited (Plastic Skin Indicators):**
- ❌ `plastic-like skin`
- ❌ `over-smoothed complexion` 
- ❌ `porcelain doll skin`
- ❌ `flawless airbrushed skin`

### 3.6 Technical Camera Specifications

For photorealistic-natural category, include standardized camera parameters:

**Camera Body:** Sony A7III full-frame mirrorless
**Lens:** 85mm f/1.4 prime lens
**Aperture:** f/1.4 to f/2.8 range
**Focal Length:** 85mm (portrait perspective)
**Sensor:** 35mm full-frame
**Lens Characteristics:** Sharp focus on subject with smooth bokeh falloff

Rationale: 85mm focal length minimizes facial distortion while maintaining natural perspective. f/1.4 aperture generates shallow depth-of-field for subject isolation.

### 3.3 Composition and Framing Techniques

| Technique | Aspect Ratio | Field of View | Application |
|-----------|-------------|---------------|-------------|
| Close-up portrait | 1:1 | Tight framing, face/head dominant | Headshots, facial detail focus |
| Environmental portrait | 4:5 | Medium framing, subject with context | Lifestyle, fashion, editorial |
| Wide establishing shot | 16:9 | Broad field of view | Landscapes, architectural, scene setting |
| Vertical full-body | 9:16 | Full subject height capture | Fashion, standing poses, story/reel format |

**Berry Implementation:** Automated aspect ratio detection in `berry_gen.sh` analyzes prompt content for framing keywords and auto-assigns optimal ratio.

### 3.4 Lighting Specifications

**Primary Light Sources:**
- `soft natural window light` — diffused daylight with gentle shadows
- `golden hour sunlight` — warm directional light (3500K-4500K)
- `studio softbox` — controlled diffused artificial light
- `rim lighting` — backlit separation from background
- `ambient fill` — bounce/reflected light for shadow detail

**Light Quality Modifiers:**
- `soft shadows` — gradual tonal transitions
- `hard shadows` — defined edge separation
- `specular highlights` — controlled reflective points
- `volumetric atmosphere` — light beam visibility in particulate matter

### 3.5 Skin Texture and Detail Enhancement

**Required Specifications:**
- `natural skin texture` — pore-level detail preservation
- `subtle skin imperfections` — freckles, moles, micro-variations
- `realistic skin translucency` — subsurface scattering simulation
- `fine hair detail` — eyebrow, eyelash, and hair strand definition

**Prohibited Elements (Negative Constraints):**
- plastic-like skin smoothing
- over-processed/filtered appearance
- artificial glow or bloom on skin
- excessive pore elimination

### 3.6 Color Palette Control

**Palette Structure:**
- Primary dominant color (60% visual weight)
- Secondary complementary color (30% visual weight)
- Accent highlight color (10% visual weight)

**Tonal Direction:**
- `warm tones` — golden hour, cozy interiors (3000K-4000K)
- `cool tones` — overcast, modern spaces (5500K-6500K)
- `neutral tones` — balanced daylight, studio environments (5000K)
- `moody/dark tones` — low-key, dramatic lighting
- `bright/vibrant tones` — high-key, saturated presentation

---

## 4. Quality Control Parameters

### 4.1 Quality Settings

| Setting | Use Case | Resolution Impact |
|---------|----------|-------------------|
| `low` | Latency-sensitive workflows, rapid iteration | Reduced pixel density |
| `medium` | Balanced quality/performance | Standard output |
| `high` | Detail-critical outputs, text-heavy compositions | Maximum pixel fidelity |
| `auto` | System-determined based on content analysis | Variable |

### 4.2 Input Fidelity (Edit Workflows)

| Setting | Application | Constraint Level |
|---------|-------------|------------------|
| `low` | Creative transformations, style changes | Permissive structural modification |
| `high` | Identity preservation, layout locking | Strict invariant maintenance |

Rationale: `input_fidelity=high` is required for identity-preserve and precise-object-edit categories to prevent drift in subject characteristics.

### 4.3 Final Output Format (핵심 규칙)

**중요: Field 구조는 계획 도구이지 출력 형식이 아님**

Field 1~10과 Field 16은 프롬프트 작성 시 고려할 **요소들의 체크리스트**입니다. 
최종 출력물은 이 Field들을 **콤마로 구분하지 않고**, **자연스러운 문장으로 연결**해야 합니다.

**❌ 잘못된 형식 (절대 사용 금지):**
```
photorealistic-natural, social-media-post, Korean woman at cafe, elegant dress, natural beauty, Sony A7III, environmental portrait, soft lighting, warm tones, wool texture, relaxed confidence
```

**✅ 올바른 형식 (자연어 문장):**
```
A candid-style environmental portrait of a Korean woman in an elegant asymmetrical dress, chatting with locals at a Parisian cafe terrace. Soft morning fog diffuses all light sources, creating warm earth tones with cream and soft beige. Photographed with Sony A7III 85mm f/1.4 lens, her natural beauty shows subtle moles on her arm and visible veins on her wrists. The wool coat texture and leather boots complement her relaxed cosmopolitan confidence.
```

**변환 규칙:**
1. Field 순서를 따르되, **자연스러운 문장 흐름**으로 재배열
2. 콤마(,)는 문장 내 자연스러운 구분에만 사용
3. "Field 1: xxx, Field 2: yyy" 형식 절대 금지
4. 영어로 작성 시 완전한 문장 구조 사용 (주어-동사-목적어)
5. 한국어로 작성 시 자연스러운 서술체 사용

**체크리스트 → 자연어 변환 프로세스:**
1. Field 3 (Primary request)를 문장의 핵심으로 설정
2. Field 4 (Scene)으로 배경을 서술
3. Field 5 (Subject)로 인물 묘사 추가
4. Field 6~10을 자연스럽게 분산 배치
5. Field 16 (Emotional sync)로 마무리

---

## 5. Negative Constraints (Avoid List)

The following elements must be explicitly excluded via negative constraints when generating photorealistic-natural category images:

### 5.1 General Exclusions
- Stock-photo aesthetic
- Oversaturated neon colors
- Harsh bloom or lens flare artifacts
- Oversharpening artifacts
- Visual clutter or distracting elements
- Watermarks or logos
- Text overlays (unless specified)

### 5.2 Style Exclusions
- Cheesy lens flare effects
- Instagram filter appearance
- Plastic skin smoothing
- Unrealistic HDR toning
- Artificial depth-of-field blur artifacts

### 5.3 Composition Exclusions
- Distracting background elements
- Unintended photobombing objects
- Cropped limbs (unless intentional framing)
- Unnatural posing

---

## 6. Berry Implementation: ComfyUI Workflow

### 6.1 Template System

Berry's image generation utilizes a JSON-based ComfyUI workflow template located at:
`scripts/templates/berry_zit_base.json`

**Template Structure:**
- Node 3: Seed control (randomized or specified)
- Node 5: Resolution control (width/height)
- Node 9: Output filename prefix
- Node 20: Wildcard text injection

### 6.2 Wildcard Substitution

The workflow supports dynamic wildcard insertion via the `__wildcards/<name>__` syntax:

```
Base prompt: "A high-quality photo of berry, __wildcards/spring__"
```

**Available Wildcards:**
- `allseason` — Season-agnostic prompts
- `spring` — Spring-themed environmental elements
- `summer` — Summer-themed environmental elements
- `autumn` — Autumn-themed environmental elements
- `winter` — Winter-themed environmental elements

### 6.3 Aspect Ratio Auto-Detection

The `choose_ratio()` function in `berry_gen.sh` implements regex-based aspect ratio selection:

```bash
Pattern matching rules:
- close-up|portrait|face|headshot|bust|upper-body → 1:1
- landscape|wide-shot|panorama|cinematic|scene|banner → 16:9
- sofa|couch|reclin|loung|daybed|living-room → 4:5
- full-body|standing|vertical|story|reels → 9:16
- default → 4:5
```

**Resolution Mapping:**
- 9:16 → 960 × 1704 pixels
- 16:9 → 1704 × 960 pixels
- 4:5 → 1088 × 1344 pixels
- 1:1 → 1024 × 1024 pixels

### 6.4 Pipeline Workflow

1. **Input Validation** — Prompt or wildcard must be specified
2. **Ratio Selection** — Automatic detection or manual override
3. **Resolution Calculation** — Map ratio to pixel dimensions
4. **JSON Generation** — Populate template with parameters
5. **ComfyUI Submission** — POST to `/prompt` endpoint
6. **Completion Polling** — Monitor `/history/<prompt_id>` for completion
7. **Image Retrieval** — Download from `/view` endpoint
8. **Telegram Delivery** — Optional transmission via `send_photo.sh`

---

## 7. Practical Examples

### 7.1 Photorealistic-Natural Portrait

```
Use case: photorealistic-natural
Asset type: personal portrait
Primary request: A high-quality photo of berry wearing a cozy cashmere sweater
Scene/background: softly blurred modern apartment interior with warm ambient lighting
Subject: young woman with natural flowing black hair, gentle smile
Style/medium: photorealistic photography
Composition/framing: upper body portrait, centered with slight head tilt, rule of thirds
Lighting/mood: soft natural window light from left side, warm and inviting atmosphere
Color palette: warm earth tones, cream and beige, soft skin tones
Materials/textures: natural skin texture, fine cashmere knit, soft hair strands
Quality: high
Avoid: oversaturated colors, plastic skin, harsh shadows, stock-photo vibe
```

**Technical Rationale:**
- Upper body framing selects 4:5 aspect ratio (1088×1344)
- Window light specification generates directional but diffused illumination
- Material texture specifications ensure surface detail preservation
- Negative constraints prevent common AI generation artifacts

### 7.2 Seasonal Wildcard Implementation

```
Wildcard: autumn
Generated prompt: A high-quality photo of berry, __wildcards/autumn__
Resolution: 4:5 (1088×1344)
Seed: Randomized
```

**Wildcard Expansion:**
The autumn wildcard expands to include seasonal elements such as:
- Fall foliage background elements
- Warm golden/amber color palette
- Soft diffused autumn sunlight
- Cozy layered clothing textures

### 7.3 Close-Up Portrait Specification

```
Use case: photorealistic-natural
Asset type: social media profile
Primary request: Close-up portrait with shallow depth of field
Scene/background: completely blurred bokeh background
Subject: young woman, natural makeup, subtle smile
Style/medium: professional portrait photography
Composition/framing: tight face framing, eyes at upper third intersection
Lighting/mood: soft diffused frontal light, catchlights in eyes
Color palette: neutral with warm undertones
Materials/textures: natural skin detail, fine eyebrow hairs, subtle lip texture
Quality: high
Avoid: over-smoothing, artificial glow, filter effects
```

**Technical Rationale:**
- "close-up" keyword triggers 1:1 aspect ratio (1024×1024)
- Bokeh background specification isolates subject from environment
- Catchlight specification enhances eye realism

---

## 8. Expression Priority Hierarchy

### 8.1 Prompt Construction Priority Order

Prompt construction follows a strict hierarchy: **scene → subject → details → constraints**

This ordering ensures the model establishes spatial context before subject placement, followed by refinement details and exclusion criteria.

#### Level 1: Scene Establishment (Highest Priority)
- Environmental context (indoor/outdoor)
- Spatial depth indicators
- Background elements
- Architectural or natural setting

#### Level 2: Subject Definition (Secondary Priority)
- Primary subject identification
- Subject attributes (age, gender, appearance)
- Subject positioning within scene
- Subject interaction with environment

#### Level 3: Detail Specification (Tertiary Priority)
- Clothing/apparel description
- Accessory elements
- Material properties
- Surface characteristics
- Micro-compositional elements

#### Level 4: Constraint Declaration (Lowest Priority)
- Negative constraints (avoid list)
- Invariant preservation (edit workflows)
- Quality thresholds

### 8.2 Color Palette Priority (60-30-10 Rule)

| Color Role | Visual Weight | Application |
|------------|---------------|-------------|
| Primary dominant color | 60% | Background, main surfaces |
| Secondary complementary color | 30% | Supporting elements, clothing |
| Accent highlight color | 10% | Details, focal points |

### 8.3 Technical Rationale

**Why this order?**
- **Scene first**: Establishes spatial context and environmental constraints
- **Subject second**: Places the primary focus within established context
- **Details third**: Refines subject and scene with specific attributes
- **Constraints last**: Applies exclusion criteria without overriding primary elements

**Model Processing Flow:**
```
Input: "luxurious bedroom, young Korean woman, silk dress, soft lighting"
Step 1: Parse scene → "luxurious bedroom" [context established]
Step 2: Place subject → "young Korean woman" [subject positioned]
Step 3: Add details → "silk dress" [attributes applied]
Step 4: Apply constraints → "soft lighting" [atmosphere refined]
```
## 9. Emotional Synchronization (Field 16)

### 9.1 Definition and Purpose

Field 16: Emotional Sync encodes intimacy and emotional connection parameters into image generation prompts. This field enables the creation of images that evoke psychological resonance between the subject and viewer through subtle visual cues rather than explicit content.

**Technical Objective:** Encode emotional states into visual parameters that AI models can render as atmospheric and compositional elements.

### 9.2 Technical Parameters

#### Warm Lighting Spectrum
- `warm color temperature` (3200K-4000K) — creates physiological comfort response
- `soft diffused glow` — reduces harsh contrast, promotes safety perception
- `skin warmth enhancement` — subtle red/orange undertones in skin rendering
- `ambient golden highlights` — rim lighting that suggests body heat radiation

#### Skin Flush Indicators
- `subtle cheek flush` — suggests emotional arousal or warmth
- `warm ear tips` — vascular response indicating presence or attention
- `gentle neck coloration` — vulnerability and trust signals
- `natural skin translucency` — subsurface scattering with warm undertones

#### Body Language Encoding
- `relaxed posture` — shoulders down, unguarded positioning
- `slight forward lean` — engagement and interest signals
- `open palm positioning` — trust and receptivity indicators
- `uncrossed limbs` — psychological openness markers

#### Eye Contact Mechanics
- `direct gaze with soft focus` — connection without aggression
- `slightly lowered eyelids` — intimacy and vulnerability
- `catchlights in eyes` — presence and engagement indicators
- `relaxed orbital muscles` — genuine rather than forced expression

### 9.3 Physical Closeness Without Explicit Contact

**Proximity Indicators:**
- `intimate framing distance` — subject fills 60-70% of frame
- `shallow depth of field` — background separation creates bubble of intimacy
- `foreground elements creating enclosure` — soft barriers suggesting private space

**Gaze Direction Vectors:**
- `off-camera gaze toward viewer` — invitation to connection
- `mutual gaze between subjects` — relationship and rapport
- `downcast eyes with upward tilt` — coyness mixed with interest

**Atmospheric Elements:**
- `soft focus edges` — dreamlike intimacy without sharp definition
- `volumetric light particles` — warmth and energy visualization
- `shallow breathing suggestion` — relaxed physiological state

### 9.4 Psychological Triggers

#### Vulnerability Markers
- `slightly parted lips` — openness and receptivity
- `exposed neck` — trust and submission signals
- `unguarded facial expression` — authenticity indicators
- `natural pose without tension` — comfort and safety

#### Trust Indicators
- `soft smile reaching eyes` — genuine emotional expression
- `relaxed hands` — lack of defensive posture
- `leaning into space` — confidence in environment
- `unforced posture` — natural rather than performative positioning

#### Anticipation Cues
- `slight lean forward` — engagement and interest
- `eyes with focused attention` — presence in moment
- `parted lips with breath` — expectation and readiness
- `tilted head` — curiosity and openness

### 9.5 Implementation Examples

#### Example 1: Intimate Portrait
```
Field 16: Emotional sync → 
  warm lighting (golden hour, 3500K color temperature),
  subtle cheek flush suggesting warmth,
  direct soft gaze with catchlights,
  relaxed shoulders and open posture,
  intimate 4:5 framing at close distance,
  shallow depth of field creating private bubble,
  atmosphere of quiet connection and trust
```

**Technical Rationale:**
- Warm color temperature triggers physiological comfort response
- Shallow depth of field psychologically separates subject from environment
- Soft gaze maintains connection without aggression
- Flush indicators suggest emotional presence and warmth

#### Example 2: Connection Without Contact
```
Field 16: Emotional sync →
  proximity suggesting closeness (upper body fills frame),
  off-camera gaze toward viewer position,
  slight forward lean indicating engagement,
  warm ambient lighting from side creating gentle shadows,
  natural skin warmth with subtle translucency,
  relaxed facial muscles suggesting comfort,
  atmospheric softness without harsh definition
```

**Technical Rationale:**
- Frame-filling composition creates psychological proximity
- Forward lean signals interest without explicit action
- Side lighting creates dimensionality and warmth
- Softness in rendering suggests emotional rather than physical focus

#### Example 3: Vulnerability and Trust
```
Field 16: Emotional sync →
  exposed neck and collarbone area (trust signal),
  slightly parted lips with natural expression,
  soft window light creating gentle illumination,
  unguarded posture with shoulders relaxed,
  direct but gentle eye contact,
  warm skin tones with subtle flush,
  quiet atmosphere of safety and acceptance
```

**Technical Rationale:**
- Anatomical exposure (neck) signals trust and vulnerability
- Natural expression avoids performative quality
- Soft lighting eliminates harsh shadows that suggest tension
- Warmth in rendering creates physiological comfort response

### 9.6 Constraints and Boundaries

**Positive Parameters to Include:**
- Emotional warmth and connection
- Psychological intimacy and trust
- Comfort and safety indicators
- Authentic vulnerability markers
- Inviting atmosphere without explicit content

**Negative Constraints (Always Exclude):**
- Explicit physical contact
- Sexualized poses or expressions
- Aggressive or dominating body language
- Objectifying framing or angles
- Artificial or forced expressions
- Cold or clinical lighting that creates distance

### 9.7 Integration with Other Fields

**Field 8 (Lighting/Mood):** Emotional sync lighting should specify warmth, softness, and intimacy
**Field 9 (Color Palette):** Emotional sync favors warm earth tones, soft pinks, and golden highlights
**Field 10 (Materials/Textures):** Emotional sync benefits from soft, natural textures that invite touch
**Field 7 (Composition):** Emotional sync typically employs intimate framing (upper body, close-up)

---

## 10. Validation Checklist

Before prompt submission, verify:

- [ ] Use case taxonomy slug is correctly classified
- [ ] All 10 required fields are populated
- [ ] Scene → subject → details → constraints hierarchy is maintained
- [ ] Camera specifications included for photorealistic-natural category
- [ ] Aspect ratio matches composition intent
- [ ] Lighting specifications are directional and specific
- [ ] Material/texture descriptions include surface characteristics
- [ ] Negative constraints include common artifact exclusions
- [ ] Quality parameter is appropriate for intended use
- [ ] Input fidelity is specified for edit workflows
- [ ] Field 16 (Emotional sync) parameters are appropriate for intended intimacy level

---

## 11. Version Control

**Document Version:** 1.2.0
**Last Updated:** 2026-03-19
**Author:** Berry (配莉)
**Review Cycle:** Quarterly

**Change Log:**
- v1.2.0 (2026-03-19): Added Advanced Lighting & Shadow Techniques (Chiaroscuro, natural shadows), Full Body Shot Specification, Bold & Sensual Expression guidelines, and Hyper-Realistic Skin Detail (moles, veins, pores, vellus hair) based on advanced prompt engineering research
- v1.1.0 (2026-03-18): Added Field 16 (Emotional Sync) with technical specifications for encoding intimacy and emotional connection in image generation prompts

---

## 12. Document Location & Usage

**Source of Truth:** `/home/pi/secretary-office/docs/z-image-turbo-prompt-technical-spec.md`

**Usage:** All secretaries (파이란, 비영, 베리) must reference this document for prompt engineering standards. Individual workspace copies should be removed and this central document used instead.

---

## 13. References

1. ComfyUI Documentation: https://github.com/comfyanonymous/ComfyUI

---


