import React from 'react'
import FileUpload from '../components/organiser'
import { Flex } from '@mantine/core'

export default function page() {
  return (
    <Flex h='100vh' w='100vw' justify='center' align='center'>

      <FileUpload/>
    </Flex>
  )
}
