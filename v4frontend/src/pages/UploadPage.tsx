import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Progress } from '../components/ui/progress'
import { Upload, FileText, X, CheckCircle, AlertCircle } from 'lucide-react'
import { useResumeStore } from '../store/resume'
import { resumeService } from '../services/resume'
import toast from 'react-hot-toast'

interface UploadFile extends File {
  id: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
}

export const UploadPage: React.FC = () => {
  const [files, setFiles] = useState<UploadFile[]>([])
  const [batchName, setBatchName] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const { addResume } = useResumeStore()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadFile[] = acceptedFiles.map(file => ({
      ...file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'pending',
      progress: 0
    }))
    setFiles(prev => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    multiple: true
  })

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(file => file.id !== id))
  }

  const uploadSingle = async (file: UploadFile) => {
    setFiles(prev => prev.map(f => 
      f.id === file.id ? { ...f, status: 'uploading', progress: 0 } : f
    ))

    try {
      const result = await resumeService.uploadSingle(file, (progress) => {
        setFiles(prev => prev.map(f => 
          f.id === file.id ? { ...f, progress } : f
        ))
      })

      setFiles(prev => prev.map(f => 
        f.id === file.id ? { ...f, status: 'success', progress: 100 } : f
      ))

      addResume(result)
      toast.success(`${file.name} uploaded successfully!`)
    } catch (error) {
      setFiles(prev => prev.map(f => 
        f.id === file.id ? { 
          ...f, 
          status: 'error', 
          error: error instanceof Error ? error.message : 'Upload failed'
        } : f
      ))
      toast.error(`Failed to upload ${file.name}`)
    }
  }

  const uploadBatch = async () => {
    if (!batchName.trim()) {
      toast.error('Please enter a batch name')
      return
    }

    if (files.length === 0) {
      toast.error('Please select files to upload')
      return
    }

    setIsUploading(true)

    try {
      const result = await resumeService.uploadBatch(files, batchName, (progress) => {
        // Update overall progress
        setFiles(prev => prev.map(f => ({ ...f, progress })))
      })

      setFiles([])
      setBatchName('')
      result.resumes.forEach(resume => addResume(resume))
      toast.success(`Batch "${batchName}" uploaded successfully!`)
    } catch (error) {
      toast.error(`Batch upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsUploading(false)
    }
  }

  const handleSingleUploads = async () => {
    setIsUploading(true)
    const pendingFiles = files.filter(f => f.status === 'pending')
    
    for (const file of pendingFiles) {
      await uploadSingle(file)
    }
    
    setIsUploading(false)
  }

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      case 'uploading':
        return <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      default:
        return <FileText className="h-5 w-5 text-gray-400" />
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Upload Resumes</h1>
        <p className="mt-2 text-gray-600">
          Upload individual resumes or create a batch upload for bulk processing
        </p>
      </div>

      {/* Upload Area */}
      <Card>
        <CardHeader>
          <CardTitle>Select Files</CardTitle>
          <CardDescription>
            Drag and drop PDF, DOC, or DOCX files here, or click to browse
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
              ${isDragActive 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
              }
            `}
          >
            <input {...getInputProps()} />
            <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            {isDragActive ? (
              <p className="text-blue-600">Drop the files here...</p>
            ) : (
              <div>
                <p className="text-gray-600 mb-2">
                  Drag & drop resume files here, or <span className="text-blue-600 underline">browse</span>
                </p>
                <p className="text-sm text-gray-500">
                  Supports PDF, DOC, DOCX files
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* File List */}
      {files.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Selected Files ({files.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {files.map((file) => (
                <div key={file.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  {getStatusIcon(file.status)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                    {file.status === 'uploading' && (
                      <Progress value={file.progress} className="mt-2" />
                    )}
                    {file.status === 'error' && file.error && (
                      <p className="text-sm text-red-500 mt-1">{file.error}</p>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeFile(file.id)}
                    disabled={file.status === 'uploading'}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upload Actions */}
      {files.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Individual Upload */}
          <Card>
            <CardHeader>
              <CardTitle>Individual Upload</CardTitle>
              <CardDescription>
                Upload files individually for immediate processing
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                onClick={handleSingleUploads}
                disabled={isUploading || files.every(f => f.status !== 'pending')}
                className="w-full"
              >
                Upload Files Individually
              </Button>
            </CardContent>
          </Card>

          {/* Batch Upload */}
          <Card>
            <CardHeader>
              <CardTitle>Batch Upload</CardTitle>
              <CardDescription>
                Group files into a batch for organized processing
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                placeholder="Enter batch name..."
                value={batchName}
                onChange={(e) => setBatchName(e.target.value)}
              />
              <Button 
                onClick={uploadBatch}
                disabled={isUploading || !batchName.trim()}
                className="w-full"
              >
                Create Batch Upload
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
