import React from 'react';
import { Calendar, CheckCircle, XCircle, Edit, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { ProductConfig } from '../types/productConfig';

interface ProductConfigDetailProps {
  config: ProductConfig;
  onEdit: () => void;
  onDelete: () => void;
  onToggleActive: () => void;
  onClose: () => void;
}

export const ProductConfigDetail: React.FC<ProductConfigDetailProps> = ({
  config,
  onEdit,
  onDelete,
  onToggleActive,
  onClose
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{config.displayName}</h2>
          <p className="text-gray-600">{config.productName}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={config.isActive ? "default" : "secondary"}>
            {config.isActive ? (
              <>
                <CheckCircle className="h-3 w-3 mr-1" />
                Active
              </>
            ) : (
              <>
                <XCircle className="h-3 w-3 mr-1" />
                Inactive
              </>
            )}
          </Badge>
        </div>
      </div>

      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Product Name</label>
              <p className="text-sm bg-gray-50 p-2 rounded">{config.productName}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
              <p className="text-sm bg-gray-50 p-2 rounded">{config.displayName}</p>
            </div>
          </div>
          
          {config.description && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <p className="text-sm bg-gray-50 p-2 rounded">{config.description}</p>
            </div>
          )}
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Created</label>
              <p className="text-sm bg-gray-50 p-2 rounded flex items-center">
                <Calendar className="h-4 w-4 mr-2" />
                {config.createdAt ? formatDate(config.createdAt) : 'Not available'}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Last Updated</label>
              <p className="text-sm bg-gray-50 p-2 rounded flex items-center">
                <Calendar className="h-4 w-4 mr-2" />
                {config.updatedAt ? formatDate(config.updatedAt) : 'Not available'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Test Combinations */}
      <Card>
        <CardHeader>
          <CardTitle>Test Combinations</CardTitle>
          <CardDescription>
            {config.testCombinations.length} test{config.testCombinations.length !== 1 ? 's' : ''} configured
          </CardDescription>
        </CardHeader>
        <CardContent>
          {config.testCombinations.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No test combinations configured</p>
          ) : (
            <div className="space-y-3">
              {config.testCombinations
                .sort((a, b) => a.order - b.order)
                .map((test, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <Badge variant="outline">#{test.order}</Badge>
                        <div>
                          <h4 className="font-medium">
                            {test.testName}
                          </h4>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {test.isRequired ? (
                          <Badge variant="default">Required</Badge>
                        ) : (
                          <Badge variant="secondary">Optional</Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              }
            </div>
          )}
        </CardContent>
      </Card>

      {/* Static Content */}
      <Card>
        <CardHeader>
          <CardTitle>Static Content</CardTitle>
          <CardDescription>Introduction and conclusion content for reports</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cover Page Title</label>
              <p className="text-sm bg-gray-50 p-2 rounded min-h-[2.5rem]">
                {config.staticContent.coverPageTitle || 'Not set'}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cover Page Subtitle</label>
              <p className="text-sm bg-gray-50 p-2 rounded min-h-[2.5rem]">
                {config.staticContent.coverPageSubtitle || 'Not set'}
              </p>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Introduction</label>
            <div className="text-sm bg-gray-50 p-3 rounded min-h-[4rem] whitespace-pre-wrap">
              {config.staticContent.introduction || 'No introduction content set'}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Conclusion</label>
            <div className="text-sm bg-gray-50 p-3 rounded min-h-[4rem] whitespace-pre-wrap">
              {config.staticContent.conclusion || 'No conclusion content set'}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
          <CardDescription>Manage this product configuration</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button onClick={onEdit} variant="default">
              <Edit className="h-4 w-4 mr-2" />
              Edit Configuration
            </Button>
            
            <Button 
              onClick={onToggleActive} 
              variant={config.isActive ? "secondary" : "default"}
            >
              {config.isActive ? (
                <>
                  <ToggleLeft className="h-4 w-4 mr-2" />
                  Deactivate
                </>
              ) : (
                <>
                  <ToggleRight className="h-4 w-4 mr-2" />
                  Activate
                </>
              )}
            </Button>
            
            <Button onClick={onDelete} variant="destructive">
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Configuration
            </Button>
            
            <Button onClick={onClose} variant="outline">
              Close
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ProductConfigDetail;