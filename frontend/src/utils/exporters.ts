import { ContentType } from '../types'

function stripHTML(html: string): string {
  const tmp = document.createElement('DIV')
  tmp.innerHTML = html
  return tmp.textContent || tmp.innerText || ''
}

function htmlToMarkdown(html: string): string {
  // Simple conversion - content is already in markdown/text format from backend
  let md = stripHTML(html)
  // Basic markdown conversions
  md = md.replace(/\n{3,}/g, '\n\n')
  return md.trim()
}

// Handle markdown content (content from backend is already markdown)
function cleanMarkdown(md: string): string {
  return md.trim()
}

export function exportToPlainText(content: string): void {
  // Content is already plain text/markdown from backend
  const text = content.replace(/#{1,6}\s+/g, '').replace(/\*\*/g, '').replace(/\*/g, '')
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `content-ai-${Date.now()}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export function exportToMarkdown(content: string): void {
  // Content is already in markdown format
  const md = cleanMarkdown(content)
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `content-ai-${Date.now()}.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export function exportToHTML(content: string): void {
  // Convert markdown to HTML (simple conversion)
  let htmlContent = content
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
    
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Content AI</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
      line-height: 1.6;
      background: #020617;
      color: #f1f5f9;
    }
    h1, h2, h3 {
      color: #06b6d4;
      margin-top: 1.5em;
    }
    p {
      margin: 1em 0;
    }
  </style>
</head>
<body>
  ${htmlContent}
</body>
</html>`
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `content-ai-${Date.now()}.html`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export async function exportToPDF(content: string, contentType: ContentType): Promise<void> {
  try {
    // Call backend PDF generation endpoint
    const response = await fetch('/api/export/pdf', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content, content_type: contentType }),
    })

    if (!response.ok) {
      throw new Error('Failed to generate PDF')
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `content-ai-${contentType}-${Date.now()}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('PDF export error:', error)
    // Fallback: show alert
    alert('PDF generation failed. Please try exporting as HTML or Markdown instead.')
  }
}
