import { Flex } from '@mantine/core'
import React from 'react'
import AttendeeUpload from '../components/attendee'

export default function page() {
  return (
    <Flex h='100vh' w='100vw' justify='center' align='center'> 
      <AttendeeUpload/>
    </Flex>
  )
}
