import { Box, VStack, Button, HStack, Spinner, Text } from '@chakra-ui/react'
import { useState, useEffect } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import ReactMarkdown from 'react-markdown'
import { ContentType } from '../types'
import { exportToPlainText, exportToMarkdown, exportToHTML, exportToPDF } from '../utils/exporters'

interface ContentEditorProps {
  content: string
  isGenerating: boolean
  contentType: ContentType
}

export function ContentEditor({ content, isGenerating, contentType }: ContentEditorProps) {
  const [editedContent, setEditedContent] = useState(content)
  const [showPreview, setShowPreview] = useState(true)

  const editor = useEditor({
    extensions: [StarterKit],
    content: editedContent,
    onUpdate: ({ editor }) => {
      setEditedContent(editor.getHTML())
    },
    editorProps: {
      attributes: {
        class: 'prose prose-lg max-w-none p-4 min-h-[400px] border border-gray-300 rounded',
      },
    },
  })

  useEffect(() => {
    if (editor && content) {
      editor.commands.setContent(content)
      setEditedContent(content)
    }
  }, [content, editor])

  if (isGenerating) {
    return (
      <Box p={8} textAlign="center">
        <Spinner size="xl" color="primary.500" thickness="4px" speed="0.65s" />
        <Text mt={4} color="gray.600">
          Generating your content...
        </Text>
      </Box>
    )
  }

  if (!content) {
    return (
      <Box p={8} textAlign="center" color="gray.500">
        Generate content first to see it here
      </Box>
    )
  }

  const handleExport = async (format: 'txt' | 'md' | 'html' | 'pdf') => {
    const contentToExport = editedContent || content
    switch (format) {
      case 'txt':
        exportToPlainText(contentToExport)
        break
      case 'md':
        exportToMarkdown(contentToExport)
        break
      case 'html':
        exportToHTML(contentToExport)
        break
      case 'pdf':
        await exportToPDF(contentToExport, contentType)
        break
    }
  }

  return (
    <VStack spacing={4} align="stretch">
      <HStack justify="space-between">
        <HStack>
          <Button
            size="sm"
            variant={!showPreview ? 'solid' : 'outline'}
            onClick={() => setShowPreview(false)}
          >
            Edit
          </Button>
          <Button
            size="sm"
            variant={showPreview ? 'solid' : 'outline'}
            onClick={() => setShowPreview(true)}
          >
            Preview
          </Button>
        </HStack>
        <HStack>
          <Button size="sm" onClick={() => handleExport('txt')}>
            Export TXT
          </Button>
          <Button size="sm" onClick={() => handleExport('md')}>
            Export MD
          </Button>
          <Button size="sm" onClick={() => handleExport('html')}>
            Export HTML
          </Button>
          <Button size="sm" colorScheme="primary" onClick={() => handleExport('pdf')}>
            Export PDF
          </Button>
        </HStack>
      </HStack>

      <Box bg="white" borderRadius="lg" boxShadow="md" minH="500px">
        {showPreview ? (
          <Box p={6} overflowY="auto" maxH="600px">
            <ReactMarkdown>{editedContent || content}</ReactMarkdown>
          </Box>
        ) : (
          <EditorContent editor={editor} />
        )}
      </Box>
    </VStack>
  )
}
