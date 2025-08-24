import React, { useState, useEffect } from 'react';
import { Plus, Trash2, GripVertical } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { productConfigService } from '../services/productConfigService';
import {
  ProductConfig,
  CreateProductConfigRequest,
  UpdateProductConfigRequest,
  TestCombination,
  StaticContent,
  AvailableTest
} from '../types/productConfig';
import toast from 'react-hot-toast';

interface ProductConfigFormProps {
  config?: ProductConfig | null;
  onSuccess: () => void;
  onCancel: () => void;
}

export const ProductConfigForm: React.FC<ProductConfigFormProps> = ({
  config,
  onSuccess,
  onCancel
}) => {
  const [formData, setFormData] = useState({
    productName: '',
    displayName: '',
    description: '',
    testCombinations: [] as TestCombination[],
    staticContent: {
      introduction: '',
      conclusion: '',
      coverPageTitle: '',
      coverPageSubtitle: ''
    } as StaticContent
  });
  const [availableTests, setAvailableTests] = useState<AvailableTest[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingTests, setLoadingTests] = useState(true);

  useEffect(() => {
    loadAvailableTests();
    if (config) {
      // Handle both 'testCombinations' and 'tests' field names for backward compatibility
      const tests = config.testCombinations || config.tests || [];
      setFormData({
        productName: config.productName,
        displayName: config.displayName || '',
        description: config.description || '',
        testCombinations: [...tests],
        staticContent: {
          introduction: config.staticContent?.introduction || '',
          conclusion: config.staticContent?.conclusion || '',
          coverPageTitle: config.staticContent?.coverPageTitle || '',
          coverPageSubtitle: config.staticContent?.coverPageSubtitle || ''
        }
      });
    }
  }, [config]);

  const loadAvailableTests = async () => {
    try {
      setLoadingTests(true);
      const tests = await productConfigService.getAvailableTests();
      setAvailableTests(tests);
    } catch (error) {
      console.error('Error loading available tests:', error);
      toast.error('Failed to load available tests');
    } finally {
      setLoadingTests(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleStaticContentChange = (field: keyof StaticContent, value: string) => {
    setFormData(prev => ({
      ...prev,
      staticContent: {
        ...prev.staticContent,
        [field]: value
      }
    }));
  };

  const addTestCombination = () => {
    const newTest: TestCombination = {
      testName: '',
      order: formData.testCombinations.length + 1,
      isRequired: true
    };
    setFormData(prev => ({
      ...prev,
      testCombinations: [...prev.testCombinations, newTest]
    }));
  };

  const removeTestCombination = (index: number) => {
    setFormData(prev => ({
      ...prev,
      testCombinations: prev.testCombinations
        .filter((_, i) => i !== index)
        .map((test, i) => ({ ...test, order: i + 1 }))
    }));
  };

  const updateTestCombination = (index: number, field: keyof TestCombination, value: any) => {
    setFormData(prev => ({
      ...prev,
      testCombinations: prev.testCombinations.map((test, i) => 
        i === index ? { ...test, [field]: value } : test
      )
    }));
  };

  const moveTestCombination = (index: number, direction: 'up' | 'down') => {
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= formData.testCombinations.length) return;

    const newCombinations = [...formData.testCombinations];
    [newCombinations[index], newCombinations[newIndex]] = [newCombinations[newIndex], newCombinations[index]];
    
    // Update order numbers
    newCombinations.forEach((test, i) => {
      test.order = i + 1;
    });

    setFormData(prev => ({
      ...prev,
      testCombinations: newCombinations
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.productName.trim()) {
      toast.error('Product name is required');
      return;
    }
    
    if (!formData.displayName.trim()) {
      toast.error('Display name is required');
      return;
    }
    
    if (formData.testCombinations.length === 0) {
      toast.error('At least one test combination is required');
      return;
    }
    
    // Validate test combinations
    for (const test of formData.testCombinations) {
      if (!test.testName.trim()) {
        toast.error('All test combinations must have a test name');
        return;
      }
    }

    try {
      setLoading(true);
      
      if (config) {
        const updateData: UpdateProductConfigRequest = {
          productName: formData.productName,
          displayName: formData.displayName,
          description: formData.description || undefined,
          testCombinations: formData.testCombinations,
          staticContent: formData.staticContent
        };
        await productConfigService.update(config._id!, updateData);
        toast.success('Product configuration updated successfully');
      } else {
        const createData: CreateProductConfigRequest = {
          productName: formData.productName,
          displayName: formData.displayName,
          description: formData.description || undefined,
          testCombinations: formData.testCombinations,
          staticContent: formData.staticContent
        };
        await productConfigService.create(createData);
        toast.success('Product configuration created successfully');
      }
      
      onSuccess();
    } catch (error) {
      console.error('Error saving product configuration:', error);
      toast.error('Failed to save product configuration');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
          <CardDescription>Configure the basic product details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Product Name *</label>
              <Input
                value={formData.productName}
                onChange={(e) => handleInputChange('productName', e.target.value)}
                placeholder="e.g., minatBakatUmum"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Display Name *</label>
              <Input
                value={formData.displayName}
                onChange={(e) => handleInputChange('displayName', e.target.value)}
                placeholder="e.g., Minat Bakat Umum"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Description</label>
            <Input
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder="Brief description of this product configuration"
            />
          </div>
        </CardContent>
      </Card>

      {/* Test Combinations */}
      <Card>
        <CardHeader>
          <CardTitle>Test Combinations</CardTitle>
          <CardDescription>Configure which tests are included and their order</CardDescription>
        </CardHeader>
        <CardContent>
          {formData.testCombinations.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">No test combinations added yet</p>
              <Button type="button" onClick={addTestCombination} variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Add First Test
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {formData.testCombinations.map((test, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex items-center gap-4">
                    <div className="flex flex-col gap-1">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => moveTestCombination(index, 'up')}
                        disabled={index === 0}
                      >
                        ↑
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => moveTestCombination(index, 'down')}
                        disabled={index === formData.testCombinations.length - 1}
                      >
                        ↓
                      </Button>
                    </div>
                    
                    <div className="flex-1 grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-1">Test Name *</label>
                        {loadingTests ? (
                          <Input placeholder="Loading tests..." disabled />
                        ) : (
                          <select
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={test.testName}
                            onChange={(e) => updateTestCombination(index, 'testName', e.target.value)}
                            required
                          >
                            <option value="">Select a test</option>
                            {availableTests.map((availableTest) => (
                              <option key={availableTest.testName} value={availableTest.testName}>
                                {availableTest.displayName || availableTest.testName}
                              </option>
                            ))}
                          </select>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            id={`required-${index}`}
                            checked={test.isRequired}
                            onChange={(e) => updateTestCombination(index, 'isRequired', e.target.checked)}
                          />
                          <label htmlFor={`required-${index}`} className="text-sm">Required</label>
                        </div>
                        <Badge variant="secondary">Order: {test.order}</Badge>
                      </div>
                    </div>
                    
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeTestCombination(index)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
              
              <Button type="button" onClick={addTestCombination} variant="outline" className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Add Another Test
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Static Content */}
      <Card>
        <CardHeader>
          <CardTitle>Static Content</CardTitle>
          <CardDescription>Configure introduction and conclusion content</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Cover Page Title</label>
              <Input
                value={formData.staticContent.coverPageTitle || ''}
                onChange={(e) => handleStaticContentChange('coverPageTitle', e.target.value)}
                placeholder="Report title for cover page"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Cover Page Subtitle</label>
              <Input
                value={formData.staticContent.coverPageSubtitle || ''}
                onChange={(e) => handleStaticContentChange('coverPageSubtitle', e.target.value)}
                placeholder="Report subtitle for cover page"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Introduction</label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={4}
              value={formData.staticContent.introduction}
              onChange={(e) => handleStaticContentChange('introduction', e.target.value)}
              placeholder="Introduction content for the report"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Conclusion</label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={4}
              value={formData.staticContent.conclusion}
              onChange={(e) => handleStaticContentChange('conclusion', e.target.value)}
              placeholder="Conclusion content for the report"
            />
          </div>
        </CardContent>
      </Card>

      {/* Form Actions */}
      <div className="flex justify-end gap-4">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? 'Saving...' : config ? 'Update Configuration' : 'Create Configuration'}
        </Button>
      </div>
    </form>
  );
};

export default ProductConfigForm;