"use client";

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { RouteErrorBoundary } from './route-error-boundary';

function ErrorTrigger({ level }: { level: 'component' | 'page' | 'critical' }) {
  const [shouldError, setShouldError] = useState(false);

  if (shouldError) {
    throw new Error(`Test error at ${level} level`);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Error Test - {level} Level</CardTitle>
        <CardDescription>
          Click the button to trigger a {level}-level error and test the error boundary.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button 
          onClick={() => setShouldError(true)}
          variant="destructive"
        >
          Trigger {level} Error
        </Button>
      </CardContent>
    </Card>
  );
}

export function ErrorBoundaryTest() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <RouteErrorBoundary level="component">
        <ErrorTrigger level="component" />
      </RouteErrorBoundary>
      
      <RouteErrorBoundary level="page">
        <ErrorTrigger level="page" />
      </RouteErrorBoundary>
      
      <RouteErrorBoundary level="critical">
        <ErrorTrigger level="critical" />
      </RouteErrorBoundary>
    </div>
  );
}
