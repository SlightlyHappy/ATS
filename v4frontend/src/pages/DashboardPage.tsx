import React, { useEffect, useState } from 'react'
import { useAuthStore } from '../store/auth'
import { useResumeStore } from '../store/resume'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Progress } from '../components/ui/progress'
import { websocketService } from '../services/websocket'
import {
  FileText,
  BarChart3,
  Clock,
  CreditCard,
  Upload,
  TrendingUp,
  Users,
  CheckCircle
} from 'lucide-react'
import { Link } from 'react-router-dom'

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore()
  const { resumes, analyses, fetchResumes, fetchAnalyses } = useResumeStore()
  const [stats, setStats] = useState({
    totalResumes: 0,
    completedAnalyses: 0,
    pendingAnalyses: 0,
    averageScore: 0
  })

  useEffect(() => {
    // Initialize WebSocket connection
    if (user) {
      websocketService.connect(user.id, user.is_admin ? 'admin' : 'user')
    }

    // Fetch initial data
    fetchResumes()
    fetchAnalyses()

    return () => {
      websocketService.disconnect()
    }
  }, [user, fetchResumes, fetchAnalyses])

  useEffect(() => {
    // Calculate stats
    const completedAnalyses = analyses.filter(a => a.status === 'completed')
    const averageScore = completedAnalyses.length > 0
      ? completedAnalyses.reduce((sum, analysis) => sum + analysis.overall_score, 0) / completedAnalyses.length
      : 0

    setStats({
      totalResumes: resumes.length,
      completedAnalyses: completedAnalyses.length,
      pendingAnalyses: analyses.filter(a => a.status === 'pending' || a.status === 'processing').length,
      averageScore
    })
  }, [resumes, analyses])

  const recentAnalyses = analyses
    .filter(a => a.status === 'completed')
    .sort((a, b) => new Date(b.completed_at!).getTime() - new Date(a.completed_at!).getTime())
    .slice(0, 5)

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            Welcome back, {user?.username}!
          </h1>
          <p className="text-muted-foreground">
            Here's an overview of your HR analytics platform
          </p>
        </div>
        <Link to="/upload">
          <Button size="lg" className="gap-2">
            <Upload className="h-4 w-4" />
            Upload Resume
          </Button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Resumes</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalResumes}</div>
            <p className="text-xs text-muted-foreground">
              Uploaded documents
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed Analyses</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.completedAnalyses}</div>
            <p className="text-xs text-muted-foreground">
              AI analyses completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Analyses</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pendingAnalyses}</div>
            <p className="text-xs text-muted-foreground">
              In queue or processing
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Score</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.averageScore.toFixed(1)}
            </div>
            <p className="text-xs text-muted-foreground">
              Overall analysis score
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Credits and Quick Actions */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Credit Balance
            </CardTitle>
            <CardDescription>
              Current credits available for analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-3xl font-bold text-primary">
                {user?.credits_balance || 0}
              </div>
              <Progress value={(user?.credits_balance || 0) / 100 * 100} className="w-full" />
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Credits used today</span>
                <span>1 credit = 1 analysis</span>
              </div>
              <Link to="/credits">
                <Button variant="outline" className="w-full">
                  Manage Credits
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Quick Actions
            </CardTitle>
            <CardDescription>
              Common tasks and shortcuts
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Link to="/upload" className="block">
                <Button variant="outline" className="w-full justify-start gap-2">
                  <Upload className="h-4 w-4" />
                  Upload New Resume
                </Button>
              </Link>
              <Link to="/resumes" className="block">
                <Button variant="outline" className="w-full justify-start gap-2">
                  <FileText className="h-4 w-4" />
                  View All Resumes
                </Button>
              </Link>
              <Link to="/queue" className="block">
                <Button variant="outline" className="w-full justify-start gap-2">
                  <Clock className="h-4 w-4" />
                  Check Queue Status
                </Button>
              </Link>
              <Link to="/analytics" className="block">
                <Button variant="outline" className="w-full justify-start gap-2">
                  <BarChart3 className="h-4 w-4" />
                  View Analytics
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Analyses */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Analyses</CardTitle>
          <CardDescription>
            Latest completed resume analyses
          </CardDescription>
        </CardHeader>
        <CardContent>
          {recentAnalyses.length > 0 ? (
            <div className="space-y-4">
              {recentAnalyses.map((analysis) => {
                const resume = resumes.find(r => r.id === analysis.resume_id)
                return (
                  <div
                    key={analysis.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="w-2 h-2 rounded-full bg-green-500"></div>
                      <div>
                        <p className="font-medium">
                          {resume?.original_filename || 'Unknown Resume'}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          Completed {new Date(analysis.completed_at!).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold">
                        {analysis.overall_score.toFixed(1)}
                      </div>
                      <div className="text-sm text-muted-foreground">Score</div>
                    </div>
                  </div>
                )
              })}
              <Link to="/resumes">
                <Button variant="outline" className="w-full">
                  View All Analyses
                </Button>
              </Link>
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No analyses yet</h3>
              <p className="text-muted-foreground mb-4">
                Upload your first resume to get started with AI-powered analysis
              </p>
              <Link to="/upload">
                <Button>Upload Resume</Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
