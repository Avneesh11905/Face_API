'use client'
import React, { useState } from 'react';
import { FileInput, Button, Alert, Card, Title } from '@mantine/core';

export default function FileUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading,setIsUploading] = useState(false)
  const handleFileUpload = async () => {
    setUploadStatus('');
    if (!file) {
      setUploadStatus('Please select a file to upload');
      return;
    }
    setIsUploading(true)
    // Assuming you have an API endpoint to handle the file upload
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`http://${window.location.hostname}:8000/upload-folder`, {
        method: 'POST',

        body: formData,
      });

      if (response.ok) {
        const data = await response.json()
        setUploadStatus(data.err);
    } else {
        setUploadStatus('Failed to upload file');
      }
    } catch (error:unknown) {
      setUploadStatus(`Error: ${error}`);
      console.log(error)
    }
    setIsUploading(false)

  };

  return (

    <Card radius={10} className='gap-5'>
      <Title className='justify-self-center self-center' order={2}>Organiser</Title>
      <FileInput
        placeholder="Choose .zip File to Upload"
        value={file}
        onChange={setFile}
        disabled={isUploading}
      />
      <Button 
      onClick={handleFileUpload} 
      disabled={isUploading} 
      loading={isUploading}
      size='md'

      >
        Upload
        </Button>
      {uploadStatus && <Alert>{uploadStatus}</Alert>}
      
     
    </Card>

  );
}
