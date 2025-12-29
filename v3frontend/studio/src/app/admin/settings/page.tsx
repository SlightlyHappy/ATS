"use client";

import { useEffect, useState } from "react";
import { AdminService } from "@/services/admin.service";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Save, RefreshCw, Shield, Globe, Mail, Database } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";

interface SystemSettings {
  general: {
    site_name: string;
    site_description: string;
    contact_email: string;
    support_url: string;
    maintenance_mode: boolean;
  };
  trial_limits: {
    resume_upload_limit: number;
    legal_query_limit: number;
    trial_duration_days: number;
  };
  email: {
    smtp_enabled: boolean;
    smtp_host: string;
    smtp_port: number;
    smtp_username: string;
    smtp_password: string;
    from_email: string;
    from_name: string;
  };
  security: {
    session_timeout_minutes: number;
    max_login_attempts: number;
    password_min_length: number;
    require_email_verification: boolean;
    enable_two_factor: boolean;
  };
  features: {
    enable_ai_analysis: boolean;
    enable_legal_queries: boolean;
    enable_bulk_operations: boolean;
    enable_api_access: boolean;
  };
}

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setSaving] = useState(false);
  const { toast } = useToast();

  const loadSettings = async () => {
    try {
      setIsLoading(true);
      const response = await AdminService.getSystemSettings();
      setSettings(response.data);
    } catch (error) {
      console.error('Failed to load settings:', error);
      // Use mock settings when backend is not available
      const mockSettings: SystemSettings = {
        general: {
          site_name: "HR Tools ATS",
          site_description: "Advanced Applicant Tracking System with AI-powered resume analysis",
          contact_email: "support@hrtools.com",
          support_url: "https://support.hrtools.com",
          maintenance_mode: false,
        },
        trial_limits: {
          resume_upload_limit: 5,
          legal_query_limit: 3,
          trial_duration_days: 14,
        },
        email: {
          smtp_enabled: true,
          smtp_host: "smtp.sendgrid.net",
          smtp_port: 587,
          smtp_username: "apikey",
          smtp_password: "************",
          from_email: "noreply@hrtools.com",
          from_name: "HR Tools",
        },
        security: {
          session_timeout_minutes: 60,
          max_login_attempts: 5,
          password_min_length: 8,
          require_email_verification: true,
          enable_two_factor: false,
        },
        features: {
          enable_ai_analysis: true,
          enable_legal_queries: true,
          enable_bulk_operations: true,
          enable_api_access: false,
        },
      };
      setSettings(mockSettings);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;
    
    try {
      setSaving(true);
      await AdminService.updateSystemSettings(settings);
      toast({
        title: "Settings saved",
        description: "System settings have been updated successfully.",
      });
    } catch (error) {
      toast({
        title: "Error saving settings",
        description: error instanceof Error ? error.message : "Could not save settings.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (section: keyof SystemSettings, key: string, value: any) => {
    if (!settings) return;
    
    setSettings({
      ...settings,
      [section]: {
        ...settings[section],
        [key]: value,
      },
    });
  };

  useEffect(() => {
    loadSettings();
  }, []);

  if (isLoading || !settings) {
    return (
      <div className="flex flex-col gap-8">
        <PageHeader
          title="System Settings"
          description="Configure system-wide settings and preferences."
        />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="System Settings"
        description="Configure system-wide settings, security, and feature toggles."
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={loadSettings}
              className="gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Reset
            </Button>
            <Button
              onClick={handleSave}
              disabled={isSaving}
              className="gap-2"
            >
              <Save className={`h-4 w-4 ${isSaving ? 'animate-spin' : ''}`} />
              Save Changes
            </Button>
          </div>
        }
      />

      <Tabs defaultValue="general" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="general" className="gap-2">
            <Globe className="h-4 w-4" />
            General
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-2">
            <Shield className="h-4 w-4" />
            Security
          </TabsTrigger>
          <TabsTrigger value="email" className="gap-2">
            <Mail className="h-4 w-4" />
            Email
          </TabsTrigger>
          <TabsTrigger value="features" className="gap-2">
            <Database className="h-4 w-4" />
            Features
          </TabsTrigger>
          <TabsTrigger value="limits" className="gap-2">
            Trial Limits
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>General Settings</CardTitle>
              <CardDescription>
                Basic site configuration and contact information.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="site_name">Site Name</Label>
                  <Input
                    id="site_name"
                    value={settings.general.site_name}
                    onChange={(e) => updateSetting('general', 'site_name', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="contact_email">Contact Email</Label>
                  <Input
                    id="contact_email"
                    type="email"
                    value={settings.general.contact_email}
                    onChange={(e) => updateSetting('general', 'contact_email', e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="site_description">Site Description</Label>
                <Textarea
                  id="site_description"
                  value={settings.general.site_description}
                  onChange={(e) => updateSetting('general', 'site_description', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="support_url">Support URL</Label>
                <Input
                  id="support_url"
                  value={settings.general.support_url}
                  onChange={(e) => updateSetting('general', 'support_url', e.target.value)}
                />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Maintenance Mode</Label>
                  <p className="text-sm text-muted-foreground">
                    Temporarily disable user access for maintenance
                  </p>
                </div>
                <Switch
                  checked={settings.general.maintenance_mode}
                  onCheckedChange={(checked) => updateSetting('general', 'maintenance_mode', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Security Settings</CardTitle>
              <CardDescription>
                Configure authentication and security policies.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="session_timeout">Session Timeout (minutes)</Label>
                  <Input
                    id="session_timeout"
                    type="number"
                    value={settings.security.session_timeout_minutes}
                    onChange={(e) => updateSetting('security', 'session_timeout_minutes', parseInt(e.target.value))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="max_login_attempts">Max Login Attempts</Label>
                  <Input
                    id="max_login_attempts"
                    type="number"
                    value={settings.security.max_login_attempts}
                    onChange={(e) => updateSetting('security', 'max_login_attempts', parseInt(e.target.value))}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password_min_length">Minimum Password Length</Label>
                <Input
                  id="password_min_length"
                  type="number"
                  value={settings.security.password_min_length}
                  onChange={(e) => updateSetting('security', 'password_min_length', parseInt(e.target.value))}
                />
              </div>
              <Separator />
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Require Email Verification</Label>
                    <p className="text-sm text-muted-foreground">
                      Users must verify their email before accessing the system
                    </p>
                  </div>
                  <Switch
                    checked={settings.security.require_email_verification}
                    onCheckedChange={(checked) => updateSetting('security', 'require_email_verification', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Two-Factor Authentication</Label>
                    <p className="text-sm text-muted-foreground">
                      Enable 2FA requirement for all users
                    </p>
                  </div>
                  <Switch
                    checked={settings.security.enable_two_factor}
                    onCheckedChange={(checked) => updateSetting('security', 'enable_two_factor', checked)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="email" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Email Configuration</CardTitle>
              <CardDescription>
                Configure SMTP settings for system emails.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable SMTP</Label>
                  <p className="text-sm text-muted-foreground">
                    Enable email sending via SMTP
                  </p>
                </div>
                <Switch
                  checked={settings.email.smtp_enabled}
                  onCheckedChange={(checked) => updateSetting('email', 'smtp_enabled', checked)}
                />
              </div>
              {settings.email.smtp_enabled && (
                <>
                  <Separator />
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="smtp_host">SMTP Host</Label>
                      <Input
                        id="smtp_host"
                        value={settings.email.smtp_host}
                        onChange={(e) => updateSetting('email', 'smtp_host', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="smtp_port">SMTP Port</Label>
                      <Input
                        id="smtp_port"
                        type="number"
                        value={settings.email.smtp_port}
                        onChange={(e) => updateSetting('email', 'smtp_port', parseInt(e.target.value))}
                      />
                    </div>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="smtp_username">SMTP Username</Label>
                      <Input
                        id="smtp_username"
                        value={settings.email.smtp_username}
                        onChange={(e) => updateSetting('email', 'smtp_username', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="smtp_password">SMTP Password</Label>
                      <Input
                        id="smtp_password"
                        type="password"
                        value={settings.email.smtp_password}
                        onChange={(e) => updateSetting('email', 'smtp_password', e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="from_email">From Email</Label>
                      <Input
                        id="from_email"
                        type="email"
                        value={settings.email.from_email}
                        onChange={(e) => updateSetting('email', 'from_email', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="from_name">From Name</Label>
                      <Input
                        id="from_name"
                        value={settings.email.from_name}
                        onChange={(e) => updateSetting('email', 'from_name', e.target.value)}
                      />
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="features" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Feature Toggles</CardTitle>
              <CardDescription>
                Enable or disable platform features.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>AI Resume Analysis</Label>
                  <p className="text-sm text-muted-foreground">
                    Enable AI-powered resume analysis and scoring
                  </p>
                </div>
                <Switch
                  checked={settings.features.enable_ai_analysis}
                  onCheckedChange={(checked) => updateSetting('features', 'enable_ai_analysis', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Legal Queries</Label>
                  <p className="text-sm text-muted-foreground">
                    Allow users to submit legal consultation requests
                  </p>
                </div>
                <Switch
                  checked={settings.features.enable_legal_queries}
                  onCheckedChange={(checked) => updateSetting('features', 'enable_legal_queries', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Bulk Operations</Label>
                  <p className="text-sm text-muted-foreground">
                    Enable bulk resume uploads and batch processing
                  </p>
                </div>
                <Switch
                  checked={settings.features.enable_bulk_operations}
                  onCheckedChange={(checked) => updateSetting('features', 'enable_bulk_operations', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>API Access</Label>
                  <p className="text-sm text-muted-foreground">
                    Enable REST API access for integrations
                  </p>
                </div>
                <Switch
                  checked={settings.features.enable_api_access}
                  onCheckedChange={(checked) => updateSetting('features', 'enable_api_access', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="limits" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Trial Account Limits</CardTitle>
              <CardDescription>
                Configure usage limits for trial accounts.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="resume_limit">Resume Upload Limit</Label>
                  <Input
                    id="resume_limit"
                    type="number"
                    value={settings.trial_limits.resume_upload_limit}
                    onChange={(e) => updateSetting('trial_limits', 'resume_upload_limit', parseInt(e.target.value))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="legal_limit">Legal Query Limit</Label>
                  <Input
                    id="legal_limit"
                    type="number"
                    value={settings.trial_limits.legal_query_limit}
                    onChange={(e) => updateSetting('trial_limits', 'legal_query_limit', parseInt(e.target.value))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="trial_duration">Trial Duration (days)</Label>
                  <Input
                    id="trial_duration"
                    type="number"
                    value={settings.trial_limits.trial_duration_days}
                    onChange={(e) => updateSetting('trial_limits', 'trial_duration_days', parseInt(e.target.value))}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
