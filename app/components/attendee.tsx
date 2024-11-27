'use client'
import React, { use, useEffect, useState } from 'react';
import { FileInput, Button, Alert, Card, LoadingOverlay, TextInput, Title } from '@mantine/core';
import { MIMEType } from 'util';
import { tree } from 'next/dist/build/templates/app-page';

export default function AttendeeUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false)
  const [EventId, setEvent] = useState<string>('')
  const [isUploaded, setIsUploaded] = useState(false)

  useEffect(() => {
    if (isUploaded) {

      setUploadStatus('')

    }
  }, [isUploaded])

  const handleFileUpload = async () => {
    setUploadStatus('');
    if (!file) {
      setUploadStatus('Please select a file to upload');
      return;
    }
    setIsUploading(true)
    // Assuming you have an API endpoint to handle the file upload
    const formData = new FormData();
    formData.append('EventId', EventId);
    formData.append('file', file);

    try {
      const response = await fetch(`http://${window.location.hostname}:8000/attendee-data`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json()
        setUploadStatus(data.err);
        if (data.err == 'go-to-download') {
          setIsUploaded(true)
        }
      } else {
        setUploadStatus('Failed to upload file');
      }
    } catch (error: unknown) {
      setUploadStatus(`Error: ${error}`);
    }
    setIsUploading(false)
  };

  const handleDownload = async () => {
    setIsUploading(true)
    const filename = file?.name.split('.')[0];
    if (!filename) {
      return;
    }
    const formData = new FormData();
    formData.append('Username', filename);


    try {
      const response = await fetch(`http://${window.location.hostname}:8000/download-zip`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to download the file.');
      }

      const blob = await response.blob(); // Convert response to a Blob
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${filename}.zip`); // Set file name
      document.body.appendChild(link);
      link.click(); // Programmatically click the link
      link.remove(); // Clean up
      setIsUploaded(false)
      setIsUploading(false)

    } catch (error) {
      console.error('Download error:', error);
    }
  };


  return (
    <Card radius={10} className='gap-5'>
      <Title className='justify-self-center self-center' order={2}>Attendee</Title>
      {isUploaded ?
      <Button 
      onClick={handleDownload} 
      disabled={isUploading} 
      loading={isUploading} 
      size="md"
      >
        Download ZIP
      </Button>
     :
      <>
        <TextInput
          placeholder='EventID'
          value={EventId}
          onChange={(e) => setEvent(e.target.value)}
          disabled={isUploading}
          />
        <FileInput
          placeholder="Upload your Image"
          value={file}
          onChange={setFile}
          disabled={isUploading}
          accept="image/*"
          capture
          />
        <LoadingOverlay
          visible={isUploading}
          zIndex={1000}
          overlayProps={{ radius: "sm", blur: 2 }}
          />
        <Button
          onClick={handleFileUpload}
          disabled={isUploading}
          size='md'
          >
          Upload
        </Button>
        {uploadStatus && <Alert>{uploadStatus}</Alert>}
      </>
      
      }
      </Card>

  );
}
