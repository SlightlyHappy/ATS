"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { UserService } from "@/services/user.service";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { 
  Save, 
  Edit, 
  Eye, 
  EyeOff, 
  User, 
  Mail, 
  Shield, 
  Calendar,
  Clock,
  Settings,
  FileText,
  BarChart3,
  Briefcase,
  MapPin,
  Phone,
  Globe,
  Linkedin,
  Github,
  Twitter,
  Lock,
  Key,
  Trash2,
  Download
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";

interface UserProfile {
  name: string;
  email: string;
  access_type: 'admin' | 'user';
  is_trial: boolean;
  trial_info?: {
    resume_limit: number;
    legal_limit: number;
    used_resumes: number;
    used_legal: number;
  };
  created_at: string;
  last_login?: string;
  // Extended profile fields
  bio?: string;
  title?: string;
  company?: string;
  location?: string;
  phone?: string;
  website?: string;
  linkedin?: string;
  github?: string;
  twitter?: string;
  skills?: string[];
  preferences?: {
    notifications_email: boolean;
    notifications_updates: boolean;
    privacy_analytics: boolean;
    theme: 'light' | 'dark' | 'system';
  };
}

interface ProfileStats {
  totalResumes: number;
  averageScore: number;
  totalAnalysisTime: number;
  lastActivity: string;
  memberSince: string;
  accountType: string;
}

export default function EnhancedUserProfilePage() {
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [profileStats, setProfileStats] = useState<ProfileStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    bio: "",
    title: "",
    company: "",
    location: "",
    phone: "",
    website: "",
    linkedin: "",
    github: "",
    twitter: "",
  });
  
  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  
  const [preferences, setPreferences] = useState({
    notifications_email: true,
    notifications_updates: true,
    privacy_analytics: true,
    theme: 'system' as 'light' | 'dark' | 'system',
  });
  
  const { toast } = useToast();

  const loadProfile = async () => {
    try {
      setIsLoading(true);
      
      // In a real app, we'd have a getProfile endpoint
      // For now, simulate with user data + mock extended fields
      if (user) {
        const mockProfile: UserProfile = {
          name: user.name || user.email || "User",
          email: user.email || "",
          access_type: user.access_type || 'user',
          is_trial: user.is_trial || false,
          trial_info: user.trial_info,
          created_at: new Date().toISOString(),
          last_login: new Date().toISOString(),
          bio: "Passionate professional focused on career growth and development.",
          title: "Software Developer",
          company: "Tech Corp",
          location: "New York, NY",
          phone: "+1 (555) 123-4567",
          website: "https://example.com",
          linkedin: "linkedin.com/in/user",
          github: "github.com/user",
          twitter: "@user",
          skills: ["JavaScript", "React", "Node.js", "Python", "AI/ML"],
          preferences: {
            notifications_email: true,
            notifications_updates: true,
            privacy_analytics: true,
            theme: 'system'
          }
        };
        
        setProfile(mockProfile);
        setFormData({
          name: mockProfile.name,
          email: mockProfile.email,
          bio: mockProfile.bio || "",
          title: mockProfile.title || "",
          company: mockProfile.company || "",
          location: mockProfile.location || "",
          phone: mockProfile.phone || "",
          website: mockProfile.website || "",
          linkedin: mockProfile.linkedin || "",
          github: mockProfile.github || "",
          twitter: mockProfile.twitter || "",
        });
        setPreferences(mockProfile.preferences || preferences);
        
        // Mock profile stats
        const mockStats: ProfileStats = {
          totalResumes: 5,
          averageScore: 78,
          totalAnalysisTime: 47, // minutes
          lastActivity: new Date().toISOString(),
          memberSince: mockProfile.created_at,
          accountType: mockProfile.is_trial ? 'Trial' : 'Premium'
        };
        setProfileStats(mockStats);
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
      toast({
        title: "Error loading profile",
        description: "Could not load your profile data. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      setIsSaving(true);
      
      // In a real app, we'd call an updateProfile API
      // For now, just simulate the update
      if (profile) {
        const updatedProfile = {
          ...profile,
          ...formData,
          preferences
        };
        setProfile(updatedProfile);
      }
      
      toast({
        title: "Profile updated",
        description: "Your profile has been updated successfully.",
      });
      
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to save profile:', error);
      toast({
        title: "Error saving profile",
        description: "Could not save your profile. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleChangePassword = async () => {
    try {
      if (passwordData.newPassword !== passwordData.confirmPassword) {
        toast({
          title: "Password mismatch",
          description: "New password and confirmation do not match.",
          variant: "destructive",
        });
        return;
      }
      
      setIsSaving(true);
      
      // In a real app, we'd call a changePassword API
      // For now, just simulate
      
      toast({
        title: "Password changed",
        description: "Your password has been changed successfully.",
      });
      
      setPasswordData({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });
      setIsChangingPassword(false);
    } catch (error) {
      console.error('Failed to change password:', error);
      toast({
        title: "Error changing password",
        description: "Could not change your password. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    try {
      // In a real app, we'd call a deleteAccount API
      toast({
        title: "Account deletion requested",
        description: "Your account deletion request has been submitted. You will receive an email confirmation.",
        variant: "destructive",
      });
      
      // Logout the user
      await logout();
    } catch (error) {
      console.error('Failed to delete account:', error);
      toast({
        title: "Error deleting account",
        description: "Could not process account deletion. Please contact support.",
        variant: "destructive",
      });
    }
  };

  const handleExportData = () => {
    // In a real app, we'd call an exportData API
    toast({
      title: "Data export requested",
      description: "Your data export will be ready for download within 24 hours. You'll receive an email notification.",
    });
  };

  useEffect(() => {
    loadProfile();
  }, [user]);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-8">
        <PageHeader
          title="My Profile"
          description="Manage your account settings and preferences."
        />
        
        <div className="grid gap-6 md:grid-cols-3">
          <div className="md:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-4 w-64" />
              </CardHeader>
              <CardContent className="space-y-4">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          </div>
          
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-24" />
              </CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex flex-col gap-8">
        <PageHeader
          title="My Profile"
          description="Manage your account settings and preferences."
        />
        <Card>
          <CardContent className="text-center py-8">
            <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-muted-foreground">Profile not found</h3>
            <p className="text-sm text-muted-foreground mt-2">
              Could not load your profile data. Please try refreshing the page.
            </p>
            <Button variant="outline" onClick={loadProfile} className="mt-4">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="My Profile"
        description="Manage your account settings, preferences, and personal information."
        actions={
          <div className="flex items-center gap-2">
            {isEditing ? (
              <>
                <Button
                  variant="outline"
                  onClick={() => {
                    setIsEditing(false);
                    setFormData({
                      name: profile.name,
                      email: profile.email,
                      bio: profile.bio || "",
                      title: profile.title || "",
                      company: profile.company || "",
                      location: profile.location || "",
                      phone: profile.phone || "",
                      website: profile.website || "",
                      linkedin: profile.linkedin || "",
                      github: profile.github || "",
                      twitter: profile.twitter || "",
                    });
                  }}
                >
                  Cancel
                </Button>
                <Button onClick={handleSaveProfile} disabled={isSaving}>
                  <Save className="h-4 w-4 mr-2" />
                  {isSaving ? "Saving..." : "Save Changes"}
                </Button>
              </>
            ) : (
              <Button onClick={() => setIsEditing(true)}>
                <Edit className="h-4 w-4 mr-2" />
                Edit Profile
              </Button>
            )}
          </div>
        }
      />

      <div className="grid gap-6 md:grid-cols-3">
        {/* Main Profile Section */}
        <div className="md:col-span-2 space-y-6">
          <Tabs defaultValue="general" className="space-y-4">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="general">General</TabsTrigger>
              <TabsTrigger value="professional">Professional</TabsTrigger>
              <TabsTrigger value="security">Security</TabsTrigger>
              <TabsTrigger value="preferences">Preferences</TabsTrigger>
            </TabsList>

            <TabsContent value="general" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    Personal Information
                  </CardTitle>
                  <CardDescription>
                    Update your personal details and contact information.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-4 mb-6">
                    <Avatar className="h-20 w-20">
                      <AvatarFallback className="text-lg">
                        {profile.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <h3 className="text-lg font-semibold">{profile.name}</h3>
                      <p className="text-sm text-muted-foreground">{profile.email}</p>
                      <Badge variant={profile.is_trial ? "secondary" : "default"} className="mt-1">
                        {profile.is_trial ? "Trial Account" : "Premium Account"}
                      </Badge>
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="name">Full Name</Label>
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        disabled={!isEditing}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="email">Email Address</Label>
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                        disabled={!isEditing}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone Number</Label>
                      <Input
                        id="phone"
                        value={formData.phone}
                        onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                        disabled={!isEditing}
                        placeholder="+1 (555) 123-4567"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="location">Location</Label>
                      <Input
                        id="location"
                        value={formData.location}
                        onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                        disabled={!isEditing}
                        placeholder="City, State/Country"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="bio">Bio</Label>
                    <Textarea
                      id="bio"
                      value={formData.bio}
                      onChange={(e) => setFormData(prev => ({ ...prev, bio: e.target.value }))}
                      disabled={!isEditing}
                      placeholder="Tell us about yourself..."
                      rows={3}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="professional" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Briefcase className="h-5 w-5" />
                    Professional Information
                  </CardTitle>
                  <CardDescription>
                    Manage your professional details and social profiles.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="title">Job Title</Label>
                      <Input
                        id="title"
                        value={formData.title}
                        onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                        disabled={!isEditing}
                        placeholder="Software Developer"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="company">Company</Label>
                      <Input
                        id="company"
                        value={formData.company}
                        onChange={(e) => setFormData(prev => ({ ...prev, company: e.target.value }))}
                        disabled={!isEditing}
                        placeholder="Tech Corp"
                      />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="website">Website</Label>
                      <div className="relative">
                        <Globe className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="website"
                          value={formData.website}
                          onChange={(e) => setFormData(prev => ({ ...prev, website: e.target.value }))}
                          disabled={!isEditing}
                          placeholder="https://example.com"
                          className="pl-10"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="linkedin">LinkedIn</Label>
                      <div className="relative">
                        <Linkedin className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="linkedin"
                          value={formData.linkedin}
                          onChange={(e) => setFormData(prev => ({ ...prev, linkedin: e.target.value }))}
                          disabled={!isEditing}
                          placeholder="linkedin.com/in/username"
                          className="pl-10"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="github">GitHub</Label>
                      <div className="relative">
                        <Github className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="github"
                          value={formData.github}
                          onChange={(e) => setFormData(prev => ({ ...prev, github: e.target.value }))}
                          disabled={!isEditing}
                          placeholder="github.com/username"
                          className="pl-10"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="twitter">Twitter</Label>
                      <div className="relative">
                        <Twitter className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="twitter"
                          value={formData.twitter}
                          onChange={(e) => setFormData(prev => ({ ...prev, twitter: e.target.value }))}
                          disabled={!isEditing}
                          placeholder="@username"
                          className="pl-10"
                        />
                      </div>
                    </div>
                  </div>

                  {profile.skills && profile.skills.length > 0 && (
                    <div className="space-y-2">
                      <Label>Skills</Label>
                      <div className="flex flex-wrap gap-2">
                        {profile.skills.map((skill, index) => (
                          <Badge key={index} variant="outline">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="security" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5" />
                    Security Settings
                  </CardTitle>
                  <CardDescription>
                    Manage your password and account security.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <Collapsible open={isChangingPassword} onOpenChange={setIsChangingPassword}>
                    <CollapsibleTrigger asChild>
                      <Button variant="outline" className="w-full justify-between">
                        <span className="flex items-center gap-2">
                          <Key className="h-4 w-4" />
                          Change Password
                        </span>
                        <Lock className="h-4 w-4" />
                      </Button>
                    </CollapsibleTrigger>
                    <CollapsibleContent className="space-y-4 mt-4">
                      <div className="space-y-2">
                        <Label htmlFor="currentPassword">Current Password</Label>
                        <div className="relative">
                          <Input
                            id="currentPassword"
                            type={showPasswords.current ? "text" : "password"}
                            value={passwordData.currentPassword}
                            onChange={(e) => setPasswordData(prev => ({ ...prev, currentPassword: e.target.value }))}
                            placeholder="Enter current password"
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="absolute right-0 top-0 h-full px-3"
                            onClick={() => setShowPasswords(prev => ({ ...prev, current: !prev.current }))}
                          >
                            {showPasswords.current ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </Button>
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="newPassword">New Password</Label>
                        <div className="relative">
                          <Input
                            id="newPassword"
                            type={showPasswords.new ? "text" : "password"}
                            value={passwordData.newPassword}
                            onChange={(e) => setPasswordData(prev => ({ ...prev, newPassword: e.target.value }))}
                            placeholder="Enter new password"
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="absolute right-0 top-0 h-full px-3"
                            onClick={() => setShowPasswords(prev => ({ ...prev, new: !prev.new }))}
                          >
                            {showPasswords.new ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </Button>
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="confirmPassword">Confirm New Password</Label>
                        <div className="relative">
                          <Input
                            id="confirmPassword"
                            type={showPasswords.confirm ? "text" : "password"}
                            value={passwordData.confirmPassword}
                            onChange={(e) => setPasswordData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                            placeholder="Confirm new password"
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="absolute right-0 top-0 h-full px-3"
                            onClick={() => setShowPasswords(prev => ({ ...prev, confirm: !prev.confirm }))}
                          >
                            {showPasswords.confirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </Button>
                        </div>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button onClick={handleChangePassword} disabled={isSaving}>
                          {isSaving ? "Changing..." : "Change Password"}
                        </Button>
                        <Button 
                          variant="outline" 
                          onClick={() => {
                            setIsChangingPassword(false);
                            setPasswordData({
                              currentPassword: "",
                              newPassword: "",
                              confirmPassword: "",
                            });
                          }}
                        >
                          Cancel
                        </Button>
                      </div>
                    </CollapsibleContent>
                  </Collapsible>

                  <Separator />

                  <div className="space-y-4">
                    <h4 className="font-medium text-destructive">Danger Zone</h4>
                    
                    <div className="flex items-center justify-between p-4 border border-destructive/20 rounded-lg">
                      <div>
                        <h5 className="font-medium">Export Account Data</h5>
                        <p className="text-sm text-muted-foreground">
                          Download all your account data and resume analysis history.
                        </p>
                      </div>
                      <Button variant="outline" onClick={handleExportData}>
                        <Download className="h-4 w-4 mr-2" />
                        Export
                      </Button>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 border border-destructive/20 rounded-lg">
                      <div>
                        <h5 className="font-medium text-destructive">Delete Account</h5>
                        <p className="text-sm text-muted-foreground">
                          Permanently delete your account and all associated data.
                        </p>
                      </div>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button variant="destructive">
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete Account</AlertDialogTitle>
                            <AlertDialogDescription>
                              This action cannot be undone. This will permanently delete your account
                              and remove all your data including resumes, analysis results, and account history.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={handleDeleteAccount}
                              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            >
                              Delete Account
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="preferences" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="h-5 w-5" />
                    Account Preferences
                  </CardTitle>
                  <CardDescription>
                    Customize your experience and notification settings.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Email Notifications</Label>
                        <p className="text-sm text-muted-foreground">
                          Receive email notifications for resume analysis completion
                        </p>
                      </div>
                      <Switch
                        checked={preferences.notifications_email}
                        onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, notifications_email: checked }))}
                        disabled={!isEditing}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Product Updates</Label>
                        <p className="text-sm text-muted-foreground">
                          Get notified about new features and improvements
                        </p>
                      </div>
                      <Switch
                        checked={preferences.notifications_updates}
                        onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, notifications_updates: checked }))}
                        disabled={!isEditing}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Analytics & Performance</Label>
                        <p className="text-sm text-muted-foreground">
                          Help improve our service by sharing usage analytics
                        </p>
                      </div>
                      <Switch
                        checked={preferences.privacy_analytics}
                        onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, privacy_analytics: checked }))}
                        disabled={!isEditing}
                      />
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <Label>Theme Preference</Label>
                    <Select
                      value={preferences.theme}
                      onValueChange={(value: 'light' | 'dark' | 'system') => setPreferences(prev => ({ ...prev, theme: value }))}
                      disabled={!isEditing}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="light">Light</SelectItem>
                        <SelectItem value="dark">Dark</SelectItem>
                        <SelectItem value="system">System</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Stats Sidebar */}
        <div className="space-y-6">
          {/* Account Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Account Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-8 h-8 bg-primary/10 rounded-full">
                  <Calendar className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium">Member Since</p>
                  <p className="text-xs text-muted-foreground">
                    {profileStats ? new Date(profileStats.memberSince).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-8 h-8 bg-green-100 rounded-full">
                  <Shield className="h-4 w-4 text-green-600" />
                </div>
                <div>
                  <p className="text-sm font-medium">Account Type</p>
                  <p className="text-xs text-muted-foreground">
                    {profileStats?.accountType || 'Standard'}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-full">
                  <Clock className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm font-medium">Last Activity</p>
                  <p className="text-xs text-muted-foreground">
                    {profileStats ? new Date(profileStats.lastActivity).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Usage Statistics */}
          {profileStats && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Usage Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Total Resumes</span>
                    <span className="font-medium">{profileStats.totalResumes}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span>Average Score</span>
                    <span className="font-medium">{profileStats.averageScore}/100</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span>Analysis Time</span>
                    <span className="font-medium">{profileStats.totalAnalysisTime}m</span>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Score Progress</span>
                    <span className="text-xs text-muted-foreground">{profileStats.averageScore}%</span>
                  </div>
                  <Progress value={profileStats.averageScore} className="h-2" />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Trial Information */}
          {profile.is_trial && profile.trial_info && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Trial Usage</CardTitle>
                <CardDescription>Your current trial limits and usage</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Resume Analyses</span>
                    <span>{profile.trial_info.used_resumes}/{profile.trial_info.resume_limit}</span>
                  </div>
                  <Progress 
                    value={(profile.trial_info.used_resumes / profile.trial_info.resume_limit) * 100} 
                    className="h-2" 
                  />
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Legal Queries</span>
                    <span>{profile.trial_info.used_legal}/{profile.trial_info.legal_limit}</span>
                  </div>
                  <Progress 
                    value={(profile.trial_info.used_legal / profile.trial_info.legal_limit) * 100} 
                    className="h-2" 
                  />
                </div>
                
                <Button className="w-full" size="sm">
                  Upgrade to Premium
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
