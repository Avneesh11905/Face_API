'use client'
import { Button, Card, Flex } from "@mantine/core";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter()
  return (
    <main>
      <Flex 
      h='100vh'
      w='100vw'
      justify='center'
      align='center'
      >
      <Card radius={10} >
        <Flex className="flex-row" gap={15}>

        <Button onClick={()=>router.push('/Organizer')} size="md" >Organizer</Button>
        <Button onClick={()=>router.push('/Attendee')} size="md">Attendee</Button>
        </Flex>
      </Card>

      </Flex>
    </main>
  );
}
