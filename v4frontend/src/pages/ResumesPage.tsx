import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { 
  FileText, 
  Download, 
  Eye, 
  Star, 
  Calendar, 
  User, 
  Building,
  Search,
  Filter,
  MoreHorizontal
} from 'lucide-react'
import { useResumeStore } from '../store/resume'
import { resumeService } from '../services/resume'
import { Resume } from '../types'
import toast from 'react-hot-toast'

export const ResumesPage: React.FC = () => {
  const { resumes, setResumes } = useResumeStore()
  const [filteredResumes, setFilteredResumes] = useState<Resume[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadResumes()
  }, [])

  useEffect(() => {
    filterResumes()
  }, [resumes, searchTerm, statusFilter])

  const loadResumes = async () => {
    try {
      setIsLoading(true)
      const data = await resumeService.getAll()
      setResumes(data.resumes)
    } catch (error) {
      toast.error('Failed to load resumes')
    } finally {
      setIsLoading(false)
    }
  }

  const filterResumes = () => {
    let filtered = resumes

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(resume => 
        resume.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
        resume.batch_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        resume.analysis?.candidate_name?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(resume => resume.processing_status === statusFilter)
    }

    setFilteredResumes(filtered)
  }

  const handleDownload = async (resumeId: string, filename: string) => {
    try {
      await resumeService.download(resumeId)
      toast.success(`Downloaded ${filename}`)
    } catch (error) {
      toast.error('Failed to download resume')
    }
  }

  const handleView = (resumeId: string) => {
    // Open resume in new tab or modal
    window.open(`/api/resumes/${resumeId}/view`, '_blank')
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'processing':
        return 'bg-blue-100 text-blue-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getMatchScore = (analysis: any) => {
    if (!analysis?.overall_score) return null
    const score = Math.round(analysis.overall_score * 100)
    return score
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Resumes</h1>
          <p className="mt-2 text-gray-600">
            Manage and view all uploaded resumes and their analysis results
          </p>
        </div>
        <Button onClick={loadResumes}>
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search by filename, batch, or candidate name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md bg-white"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Resume Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <FileText className="h-4 w-4 text-blue-600" />
              <div className="ml-2">
                <p className="text-sm font-medium text-gray-600">Total Resumes</p>
                <p className="text-2xl font-bold">{resumes.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <div className="h-4 w-4 bg-green-500 rounded-full" />
              <div className="ml-2">
                <p className="text-sm font-medium text-gray-600">Completed</p>
                <p className="text-2xl font-bold">
                  {resumes.filter(r => r.processing_status === 'completed').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <div className="h-4 w-4 bg-blue-500 rounded-full" />
              <div className="ml-2">
                <p className="text-sm font-medium text-gray-600">Processing</p>
                <p className="text-2xl font-bold">
                  {resumes.filter(r => r.processing_status === 'processing').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <div className="h-4 w-4 bg-red-500 rounded-full" />
              <div className="ml-2">
                <p className="text-sm font-medium text-gray-600">Failed</p>
                <p className="text-2xl font-bold">
                  {resumes.filter(r => r.processing_status === 'failed').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Resume List */}
      <div className="grid gap-4">
        {filteredResumes.length === 0 ? (
          <Card>
            <CardContent className="pt-6 text-center">
              <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No resumes found</h3>
              <p className="text-gray-600">
                {searchTerm || statusFilter !== 'all' 
                  ? 'Try adjusting your search or filter criteria'
                  : 'Upload your first resume to get started'
                }
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredResumes.map((resume) => (
            <Card key={resume.id}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-2">
                      <FileText className="h-5 w-5 text-gray-400" />
                      <h3 className="text-lg font-medium text-gray-900 truncate">
                        {resume.filename}
                      </h3>
                      <Badge className={getStatusColor(resume.processing_status)}>
                        {resume.processing_status}
                      </Badge>
                      {getMatchScore(resume.analysis) && (
                        <Badge variant="outline">
                          <Star className="h-3 w-3 mr-1" />
                          {getMatchScore(resume.analysis)}% Match
                        </Badge>
                      )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                      {resume.analysis?.candidate_name && (
                        <div className="flex items-center text-sm text-gray-600">
                          <User className="h-4 w-4 mr-2" />
                          {resume.analysis.candidate_name}
                        </div>
                      )}
                      
                      {resume.analysis?.current_company && (
                        <div className="flex items-center text-sm text-gray-600">
                          <Building className="h-4 w-4 mr-2" />
                          {resume.analysis.current_company}
                        </div>
                      )}

                      {resume.batch_name && (
                        <div className="flex items-center text-sm text-gray-600">
                          <div className="h-4 w-4 bg-blue-100 rounded mr-2" />
                          Batch: {resume.batch_name}
                        </div>
                      )}

                      <div className="flex items-center text-sm text-gray-600">
                        <Calendar className="h-4 w-4 mr-2" />
                        {formatDate(resume.created_at)}
                      </div>
                    </div>

                    {resume.analysis?.key_skills && resume.analysis.key_skills.length > 0 && (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-gray-700 mb-2">Key Skills:</p>
                        <div className="flex flex-wrap gap-1">
                          {resume.analysis.key_skills.slice(0, 6).map((skill, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {skill}
                            </Badge>
                          ))}
                          {resume.analysis.key_skills.length > 6 && (
                            <Badge variant="outline" className="text-xs">
                              +{resume.analysis.key_skills.length - 6} more
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handleView(resume.id)}
                      title="View Resume"
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handleDownload(resume.id, resume.filename)}
                      title="Download Resume"
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="icon" title="More actions">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
