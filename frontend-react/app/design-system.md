# Pathio Design System
**Gen Z/Alpha Career Platform - Bold, Bubbly, Purpose-Driven**

## Brand Colors

### Primary Purple Palette
- **Light Purple**: `#A78BFA` - Slogan, secondary text, interactive elements
- **Medium Purple**: `#7C3AED` - Gradient start, accents
- **Dark Purple**: `#5B21B6` - Gradient end, depth
- **Border Purple**: `#D8B4FE` - Input borders (light)

### Neutrals
- **Pure Black**: `#0A0A0A` - Logo, primary headlines
- **Dark Grey**: `#313338` - Body text (Discord-inspired)
- **Mid Grey**: `#505050` - Subtle text
- **Light Grey**: `#FAFAF9` - Input backgrounds

## Typography

### Font Weights (Inter font family)
- **900 (Black)**: Logo "pathio" only
- **800 (Extra Bold)**: Reserved for special emphasis
- **700 (Bold)**: Buttons, CTAs
- **600 (Semibold)**: Slogan, Upload link, subheadings
- **500 (Medium)**: Action links, body text
- **400 (Regular)**: Placeholder text, descriptions

### Font Sizes
- **2.4rem**: Logo "pathio"
- **1.05rem**: Slogan
- **1rem**: Action links, body text
- **0.95rem**: Button text
- **0.9rem**: Secondary links (Upload file)
- **0.85rem**: Small text, labels

### Line Heights
- Headlines: 1.2-1.3
- Body: 1.6-1.7
- Compact: 1.4-1.5

## Components

### Primary Button (Analyze, Submit)
```css
background: linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)
padding: 12px 36px
color: #FFFFFF
border: none
borderRadius: 24px
boxShadow: 0 4px 14px rgba(124, 58, 237, 0.3)
fontWeight: 700 (bold)
fontSize: 0.95rem
```

### Text Input / Textarea
```css
border: 2px solid #D8B4FE
background: #FAFAF9
borderRadius: 20px
padding: 18px 22px
fontSize: 1rem
fontWeight: 500 (medium)
focus:borderColor: #A78BFA
```

### Action Links (Secondary CTAs)
```css
color: #313338
fontSize: 1rem
fontWeight: 500
background: none
border: none
hover:color: #5865F2 (Discord purple) or #7C3AED
marginBottom: 5px (between items)
```

### Interactive Links (Upload file, etc)
```css
color: #A78BFA
fontSize: 0.9rem
fontWeight: 600
hover:opacity: 0.8
```

## Layout

### Spacing Scale
- **XS**: 5px - Tight spacing (action links)
- **SM**: 20px - Standard gaps
- **MD**: 40px - Section separation
- **LG**: 60px - Major sections
- **XL**: 100px+ - Page-level spacing

### Container
- **Max width**: 720px
- **Padding**: 32px bottom, variable top

### Header (Logo + Slogan)
- **Position**: Top-left, fixed
- **Top**: 40px
- **Left**: 40px
- **z-index**: 100

## Voice & Tone

### Copy Style
- **Direct**: "Start with your resume" not "Please paste your resume here"
- **Playful**: "the old-fashioned kind with paychecks"
- **Gen Z**: Casual but smart, knowing but not condescending
- **Action-oriented**: Verbs first - "Find", "Help me", "Upload"

### Button Labels
- **Short**: "Analyze" not "Analyze Resume"
- **Active**: "Analyzing..." for loading states
- **No arrows**: Keep it clean

## Animations

### Transitions
- **Hover**: opacity 0.8-0.9, 200-300ms
- **Color changes**: 200ms ease
- **Page transitions**: 400-500ms ease-out

### Loading States
- **Pulse**: 1.5s ease-in-out infinite (for content loading)
- **Slide up**: 0.4s ease-out (for new content appearing)

## Design Principles

1. **Bold over subtle** - Gen Z expects confidence
2. **Purple = brand** - Use consistently for interactive/brand elements
3. **Rounded corners** - Friendly, approachable (16-24px)
4. **Shadows for depth** - Subtle glows on buttons (purple tint)
5. **Weight hierarchy** - Logo heaviest, then descending
6. **Color consistency** - Black for primary, purple for interactive, grey for body

## Future Considerations

### Premium Features
- Gold/yellow accents for premium badges
- Gradient borders for pro features
- Subtle animations for delight

### Dark Mode (Future)
- Background: `#1E1F22` (Discord dark)
- Text: `#F2F3F5`
- Purple stays the same
- Adjust borders to lighter variants

---

*This design system prioritizes Gen Z/Alpha expectations: bold, visual, interactive, purposeful.*


