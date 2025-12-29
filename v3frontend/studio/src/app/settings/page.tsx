"use client";

import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { useTheme } from "next-themes";
import { useToast } from "@/hooks/use-toast";

// Force dynamic rendering to prevent static generation issues with themes
export const dynamic = 'force-dynamic'


export default function SettingsPage() {
    const { toast } = useToast();
    const { theme, setTheme } = useTheme();

    const handleSaveChanges = () => {
        toast({
            title: "Success!",
            description: "Your settings have been saved.",
        });
    };
    
    return (
        <div className="flex flex-col gap-8">
            <PageHeader title="Settings" description="Manage system configuration and appearance." />

            <div className="grid gap-8">
                <Card>
                    <CardHeader>
                        <CardTitle>AI Provider</CardTitle>
                        <CardDescription>Configure your AI provider credentials.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="apiKey">API Key</Label>
                            <Input id="apiKey" type="password" defaultValue="••••••••••••••••••••" />
                        </div>
                    </CardContent>
                    <CardFooter>
                        <Button onClick={handleSaveChanges}>Save AI Settings</Button>
                    </CardFooter>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Appearance</CardTitle>
                        <CardDescription>Customize the look and feel of the application.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="flex items-center justify-between">
                            <Label htmlFor="darkMode" className="flex flex-col space-y-1">
                                <span>Dark Mode</span>
                                <span className="font-normal leading-snug text-muted-foreground">
                                    Enable or disable dark mode.
                                </span>
                            </Label>
                             <Switch
                                id="darkMode"
                                checked={theme === 'dark'}
                                onCheckedChange={(checked) => setTheme(checked ? 'dark' : 'light')}
                            />
                        </div>
                        <Separator />
                        <div className="space-y-2">
                            <Label htmlFor="logo">Logo Upload</Label>
                            <Input id="logo" type="file" />
                            <p className="text-sm text-muted-foreground">Upload a new logo for your organization. (PNG, JPG, SVG)</p>
                        </div>
                    </CardContent>
                    <CardFooter>
                        <Button onClick={handleSaveChanges}>Save Appearance</Button>
                    </CardFooter>
                </Card>

                 <Card>
                    <CardHeader>
                        <CardTitle>Webhooks</CardTitle>
                        <CardDescription>Manage webhook integrations for external services.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="razorpayWebhook">Razorpay Webhook URL</Label>
                            <Input id="razorpayWebhook" placeholder="https://api.example.com/webhooks/razorpay" />
                        </div>
                         <div className="space-y-2">
                            <Label htmlFor="supabaseWebhook">Supabase Sync Webhook URL</Label>
                            <Input id="supabaseWebhook" placeholder="https://api.example.com/webhooks/supabase" />
                        </div>
                    </CardContent>
                    <CardFooter>
                        <Button onClick={handleSaveChanges}>Save Webhooks</Button>
                    </CardFooter>
                </Card>
            </div>
        </div>
    )
}
