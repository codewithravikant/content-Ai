import { Box, Button, HStack } from '@chakra-ui/react'
import { ContentType } from '../types'

interface ContentTypeSelectorProps {
  selectedType: ContentType | null
  onSelectType: (type: ContentType) => void
}

export function ContentTypeSelector({ selectedType, onSelectType }: ContentTypeSelectorProps) {
  return (
    <Box p={4} bg="white" borderRadius="lg" boxShadow="md">
      <HStack spacing={4} justify="center">
        <Button
          colorScheme={selectedType === 'blog_post' ? 'primary' : 'gray'}
          variant={selectedType === 'blog_post' ? 'solid' : 'outline'}
          onClick={() => onSelectType('blog_post')}
          size="lg"
        >
          📝 Blog Post
        </Button>
        <Button
          colorScheme={selectedType === 'email' ? 'primary' : 'gray'}
          variant={selectedType === 'email' ? 'solid' : 'outline'}
          onClick={() => onSelectType('email')}
          size="lg"
        >
          ✉️ Email
        </Button>
      </HStack>
    </Box>
  )
}
