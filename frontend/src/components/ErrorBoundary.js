import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to console
    console.error('Error Boundary caught an error:', error, errorInfo);
    
    // Log to backend error tracking
    this.logErrorToService(error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
      errorCount: this.state.errorCount + 1
    });
  }

  logErrorToService = async (error, errorInfo) => {
    try {
      // Send error to backend for tracking
      const errorData = {
        message: error.toString(),
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      };

      // In production, send to error tracking service
      console.log('Error logged:', errorData);
      
      // You can also send to backend:
      // await fetch('/api/errors/log', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(errorData)
      // });
    } catch (e) {
      console.error('Failed to log error:', e);
    }
  };

  handleReset = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null 
    });
    
    // Reload the page if error persists
    if (this.state.errorCount > 2) {
      window.location.reload();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <Card className="max-w-2xl w-full border-red-200 bg-red-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-3 text-red-800">
                <AlertCircle className="w-8 h-8" />
                Something went wrong
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-white rounded-lg p-4 border border-red-200">
                <p className="text-sm font-medium text-gray-900 mb-2">Error Details:</p>
                <p className="text-sm text-red-700 font-mono bg-red-50 p-3 rounded">
                  {this.state.error && this.state.error.toString()}
                </p>
              </div>

              {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
                <details className="bg-white rounded-lg p-4 border border-red-200">
                  <summary className="text-sm font-medium text-gray-900 cursor-pointer mb-2">
                    Technical Details (Development Mode)
                  </summary>
                  <pre className="text-xs text-gray-700 overflow-auto max-h-64 bg-gray-50 p-3 rounded">
                    {this.state.errorInfo.componentStack}
                  </pre>
                </details>
              )}

              <div className="flex gap-3">
                <Button 
                  onClick={this.handleReset}
                  className="flex-1 bg-red-600 hover:bg-red-700"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Try Again
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => window.location.href = '/'}
                  className="flex-1"
                >
                  Go to Home
                </Button>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <p className="text-sm text-amber-800">
                  <strong>Note:</strong> This error has been logged and our team will investigate. 
                  If the problem persists, please contact support.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
