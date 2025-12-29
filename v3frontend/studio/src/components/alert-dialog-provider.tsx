"use client";

import React, { createContext, useContext, useState, ReactNode } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

type AlertDialogOptions = {
  title: string;
  description: string;
  onConfirm: () => void;
  onCancel?: () => void;
  confirmText?: string;
  cancelText?: string;
};

type AlertDialogContextType = {
  showAlertDialog: (options: AlertDialogOptions) => void;
};

const AlertDialogContext = createContext<AlertDialogContextType | undefined>(undefined);

export const AlertDialogProvider = ({ children }: { children: ReactNode }) => {
  const [options, setOptions] = useState<AlertDialogOptions | null>(null);

  const showAlertDialog = (newOptions: AlertDialogOptions) => {
    setOptions(newOptions);
  };

  const handleClose = () => {
    setOptions(null);
  };

  const handleCancel = () => {
    options?.onCancel?.();
    handleClose();
  };

  const handleConfirm = () => {
    options?.onConfirm();
    handleClose();
  };

  return (
    <AlertDialogContext.Provider value={{ showAlertDialog }}>
      {children}
      {options && (
        <AlertDialog open={!!options} onOpenChange={handleClose}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>{options.title}</AlertDialogTitle>
              <AlertDialogDescription>{options.description}</AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={handleCancel}>
                {options.cancelText || 'Cancel'}
              </AlertDialogCancel>
              <AlertDialogAction onClick={handleConfirm}>
                {options.confirmText || 'Confirm'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </AlertDialogContext.Provider>
  );
};

export const useAlertDialog = () => {
  const context = useContext(AlertDialogContext);
  if (context === undefined) {
    throw new Error('useAlertDialog must be used within an AlertDialogProvider');
  }
  return context;
};
