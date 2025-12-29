import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function ProfilePage() {
    return (
        <div className="flex flex-col gap-8">
            <PageHeader title="My Profile" description="Manage your personal information and account settings." />

            <div className="grid gap-8 md:grid-cols-3">
                <Card className="md:col-span-2">
                    <CardHeader>
                        <CardTitle>Personal Information</CardTitle>
                        <CardDescription>Update your name and email address.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Full Name</Label>
                            <Input id="name" defaultValue="Olivia Martin" />
                        </div>
                         <div className="space-y-2">
                            <Label htmlFor="email">Email Address</Label>
                            <Input id="email" type="email" defaultValue="olivia.martin@email.com" />
                        </div>
                    </CardContent>
                    <CardFooter>
                        <Button>Save Changes</Button>
                    </CardFooter>
                </Card>

                <div className="space-y-8">
                    <Card>
                        <CardHeader>
                            <CardTitle>Subscription Plan</CardTitle>
                            <CardDescription>You are currently on the Enterprise plan.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm">Access to all features, priority support, and unlimited resume analyses.</p>
                        </CardContent>
                        <CardFooter>
                            <Button variant="outline">Manage Subscription</Button>
                        </CardFooter>
                    </Card>

                     <Card>
                        <CardHeader>
                            <CardTitle>Delete Account</CardTitle>
                            <CardDescription>Permanently delete your account and all associated data.</CardDescription>
                        </CardHeader>
                        <CardContent>
                           <Button variant="destructive">Delete My Account</Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}
