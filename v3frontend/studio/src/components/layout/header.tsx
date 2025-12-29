
"use client";

import Link from "next/link";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { UserCircle, LogOut, Search, Settings, Menu } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Input } from "@/components/ui/input";
import { CreditBalance } from "@/components/payment/credit-balance";
import GlareHover from "@/Animations/GlareHover/GlareHover";

interface HeaderProps {
  isAdmin?: boolean;
  onMenuClick?: () => void;
}

export function Header({ isAdmin = false, onMenuClick }: HeaderProps) {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase();
  };

  const profileHref = isAdmin ? "/admin/settings" : "/user/profile";

  return (
    <header className="sticky top-0 z-50 flex h-16 items-center gap-2 md:gap-4 border-b border-border/40 bg-background/30 px-3 md:px-6 backdrop-blur-xl backdrop-saturate-150 supports-[backdrop-filter]:bg-background/20">
      <div className="md:hidden">
        <GlareHover
          width="40px"
          height="40px"
          background="transparent"
          borderRadius="8px"
          borderColor="transparent"
          glareColor="#3b82f6"
          glareOpacity={0.3}
          transitionDuration={500}
          className="border-0"
        >
          <Button
            variant="ghost"
            size="sm"
            onClick={onMenuClick}
            className="p-2 hover:bg-primary/10 transition-all duration-300"
          >
            <Menu className="h-5 w-5" />
            <span className="sr-only">Toggle menu</span>
          </Button>
        </GlareHover>
      </div>
      
      {/* Global Search - Only for admin */}
      {isAdmin && (
        <div className="hidden sm:flex w-full max-w-sm items-center space-x-2">
          <div className="relative group">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors duration-300" />
            <Input
              placeholder="Search..."
              className="pl-8 w-full bg-background/50 border-border/50 hover:border-primary/50 focus:border-primary transition-all duration-300 backdrop-blur-sm"
            />
          </div>
        </div>
      )}
      
      <div className="flex-1" />
      
      {/* Mobile Search Icon - Only for admin */}
      {isAdmin && (
        <GlareHover
          width="40px"
          height="40px"
          background="transparent"
          borderRadius="50%"
          borderColor="transparent"
          glareColor="#3b82f6"
          glareOpacity={0.2}
          transitionDuration={400}
          className="sm:hidden border-0"
        >
          <Button variant="ghost" size="icon" className="rounded-full hover:bg-primary/10 transition-all duration-300">
            <Search className="h-4 w-4" />
            <span className="sr-only">Search</span>
          </Button>
        </GlareHover>
      )}
      
      {/* Credit Balance - Only for regular users - Temporarily Hidden */}
      {/* {!isAdmin && (
        <div className="hidden md:block">
          <CreditBalance 
            compact={true} 
            onTopUpAction={() => window.location.href = '/user/billing'}
            showTopUpButton={true}
          />
        </div>
      )} */}
      
      {/* User Menu */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <GlareHover
            width="40px"
            height="40px"
            background="transparent"
            borderRadius="50%"
            borderColor="transparent"
            glareColor="#3b82f6"
            glareOpacity={0.15}
            transitionDuration={600}
            className="border-0"
          >
            <Button variant="ghost" size="icon" className="rounded-full hover:bg-primary/10 transition-all duration-300">
              <Avatar className="ring-2 ring-transparent hover:ring-primary/20 transition-all duration-300">
                <AvatarFallback className="bg-gradient-to-br from-primary/20 to-accent/20 text-foreground font-medium">
                  {user ? getInitials(user.name) : 'U'}
                </AvatarFallback>
              </Avatar>
            </Button>
          </GlareHover>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>
            <div className="flex flex-col space-y-1">
              <p className="text-sm font-medium">{user?.name || 'User'}</p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
              {user?.access_type && (
                <p className="text-xs text-primary font-medium capitalize">
                  {user.access_type}
                </p>
              )}
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem asChild>
            <Link href={profileHref} className="flex items-center gap-2">
              {isAdmin ? (
                <Settings className="h-4 w-4" />
              ) : (
                <UserCircle className="h-4 w-4" />
              )}
              <span>{isAdmin ? 'Settings' : 'Profile'}</span>
            </Link>
          </DropdownMenuItem>
          {/* Temporarily hidden billing menu
          {!isAdmin && (
            <DropdownMenuItem asChild>
              <Link href="/user/billing" className="flex items-center gap-2">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
                <span>Billing & Credits</span>
              </Link>
            </DropdownMenuItem>
          )} */}
          <DropdownMenuSeparator />
          <DropdownMenuItem 
            className="flex items-center gap-2 text-destructive focus:text-destructive"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4" />
            <span>Logout</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
