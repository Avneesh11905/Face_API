'use client'
import { Button } from '@mantine/core'
import { useRouter } from 'next/navigation'
import React from 'react'

export default function HomeButton() {
    const router = useRouter()  
  return (
    <Button onClick={() => router.push('/')} size='md' m={20} pos='fixed'> Home</Button>
  )
}
