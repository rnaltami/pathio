# Current formatPerplexityResponse Function - BACKUP

**Date:** $(date)
**Status:** Working but has parsing issues with bullet points

## Current Function (Lines 67-134 in frontend-react/app/page.tsx)

```typescript
const formatPerplexityResponse = (text: string) => {
  // Split by section headers (both **Header** and ### Header formats)
  const sections = text.split(/(\*\*[^*]+\*\*|### [^\n]+)/g)
  const formatted = []
  
  for (let i = 0; i < sections.length; i++) {
    const section = sections[i].trim()
    if (!section) continue
    
    if (section.startsWith('**') && section.endsWith('**')) {
      // This is a header
      const headerText = section.replace(/\*\*/g, '')
      formatted.push(
        <div key={i} className="font-bold text-xl text-purple-400 mb-3 mt-6 first:mt-0">
          {headerText}
        </div>
      )
    } else if (section.startsWith('### ')) {
      // This is a subheader
      const headerText = section.replace(/### /g, '')
      formatted.push(
        <div key={i} className="font-semibold text-lg text-blue-400 mb-2 mt-4">
          {headerText}
        </div>
      )
    } else {
      // This is content
      const lines = section.split('\n').filter(line => line.trim())
      lines.forEach((line, lineIndex) => {
        const trimmedLine = line.trim()
        if (trimmedLine.startsWith('- ')) {
          // Bullet point
          formatted.push(
            <div key={`${i}-${lineIndex}`} className="flex items-start mb-2 ml-4">
              <span className="text-purple-400 mr-3 mt-1 text-sm">•</span>
              <span className="text-gray-300 text-sm leading-relaxed">{trimmedLine.replace('- ', '')}</span>
            </div>
          )
        } else if (trimmedLine.startsWith('• ')) {
          // Alternative bullet point
          formatted.push(
            <div key={`${i}-${lineIndex}`} className="flex items-start mb-2 ml-4">
              <span className="text-purple-400 mr-3 mt-1 text-sm">•</span>
              <span className="text-gray-300 text-sm leading-relaxed">{trimmedLine.replace('• ', '')}</span>
            </div>
          )
        } else if (trimmedLine.match(/^\d+\./)) {
          // Numbered list
          formatted.push(
            <div key={`${i}-${lineIndex}`} className="flex items-start mb-2 ml-4">
              <span className="text-purple-400 mr-3 mt-1 text-sm font-medium">{trimmedLine.split('.')[0]}.</span>
              <span className="text-gray-300 text-sm leading-relaxed">{trimmedLine.replace(/^\d+\.\s*/, '')}</span>
            </div>
          )
        } else if (trimmedLine) {
          // Regular paragraph
          formatted.push(
            <div key={`${i}-${lineIndex}`} className="text-gray-300 mb-3 text-sm leading-relaxed">
              {trimmedLine}
            </div>
          )
        }
      })
    }
  }
  
  return formatted.length > 0 ? formatted : [<div key="fallback" className="text-gray-300">{text}</div>]
}
```

## Known Issues
- Bullet points sometimes show as blank (missing content after company names)
- Inconsistent bullet point rendering
- Some content gets lost in the parsing process

## Rollback Plan
If the fix doesn't work, restore this exact function to lines 67-134 in frontend-react/app/page.tsx

