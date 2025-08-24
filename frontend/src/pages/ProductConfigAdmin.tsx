import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Eye, ToggleLeft, ToggleRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { productConfigService } from '../services/productConfigService';
import { ProductConfig } from '../types/productConfig';
import { ProductConfigForm, ProductConfigDetail } from '../components';
import toast from 'react-hot-toast';

export const ProductConfigAdmin: React.FC = () => {
  const [productConfigs, setProductConfigs] = useState<ProductConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedConfig, setSelectedConfig] = useState<ProductConfig | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<ProductConfig | null>(null);

  useEffect(() => {
    loadProductConfigs();
  }, []);

  const loadProductConfigs = async () => {
    try {
      setLoading(true);
      const configs = await productConfigService.getAll();
      setProductConfigs(configs);
    } catch (error) {
      console.error('Error loading product configurations:', error);
      toast.error('Failed to load product configurations');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingConfig(null);
    setIsFormOpen(true);
  };

  const handleEdit = (config: ProductConfig) => {
    setEditingConfig(config);
    setIsFormOpen(true);
  };

  const handleView = (config: ProductConfig) => {
    setSelectedConfig(config);
    setIsDetailOpen(true);
  };

  const handleDelete = async (config: ProductConfig) => {
    if (!window.confirm(`Are you sure you want to delete "${config.displayName}"?`)) {
      return;
    }

    try {
      await productConfigService.delete(config._id!);
      toast.success('Product configuration deleted successfully');
      loadProductConfigs();
    } catch (error) {
      console.error('Error deleting product configuration:', error);
      toast.error('Failed to delete product configuration');
    }
  };

  const handleToggleActive = async (config: ProductConfig) => {
    try {
      await productConfigService.toggleActive(config._id!);
      toast.success(`Product configuration ${config.isActive ? 'deactivated' : 'activated'} successfully`);
      loadProductConfigs();
    } catch (error) {
      console.error('Error toggling product configuration status:', error);
      toast.error('Failed to update product configuration status');
    }
  };

  const handleFormSuccess = () => {
    setIsFormOpen(false);
    setEditingConfig(null);
    loadProductConfigs();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Product Configuration Admin</h1>
          <p className="text-gray-600 mt-2">Manage product configurations and test combinations</p>
        </div>
        <Button onClick={handleCreate} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Create New Configuration
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Product Configurations</CardTitle>
          <CardDescription>
            Configure test combinations and static content for different products
          </CardDescription>
        </CardHeader>
        <CardContent>
          {productConfigs.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">No product configurations found</p>
              <Button onClick={handleCreate} variant="outline">
                Create your first configuration
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Product Name</TableHead>
                  <TableHead>Display Name</TableHead>
                  <TableHead>Tests</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {productConfigs.map((config) => (
                  <TableRow key={config.id || config._id}>
                    <TableCell className="font-medium">{config.productName}</TableCell>
                    <TableCell>{config.displayName || config.productName}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">
                        {(config.testCombinations || config.tests || []).length} test{(config.testCombinations || config.tests || []).length !== 1 ? 's' : ''}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={config.isActive ? 'default' : 'secondary'}>
                        {config.isActive ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {config.createdAt ? new Date(config.createdAt).toLocaleDateString() : 'N/A'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleView(config)}
                          title="View details"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(config)}
                          title="Edit configuration"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleActive(config)}
                          title={config.isActive ? 'Deactivate' : 'Activate'}
                        >
                          {config.isActive ? (
                            <ToggleRight className="h-4 w-4 text-green-600" />
                          ) : (
                            <ToggleLeft className="h-4 w-4 text-gray-400" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(config)}
                          title="Delete configuration"
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Form Dialog */}
      <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingConfig ? 'Edit Product Configuration' : 'Create Product Configuration'}
            </DialogTitle>
            <DialogDescription>
              {editingConfig
                ? 'Update the product configuration settings'
                : 'Create a new product configuration with test combinations and static content'}
            </DialogDescription>
          </DialogHeader>
          <ProductConfigForm
            config={editingConfig}
            onSuccess={handleFormSuccess}
            onCancel={() => setIsFormOpen(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Detail View Dialog */}
      <Dialog open={isDetailOpen} onOpenChange={setIsDetailOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Product Configuration Details</DialogTitle>
            <DialogDescription>
              View the complete configuration for {selectedConfig?.displayName}
            </DialogDescription>
          </DialogHeader>
          {selectedConfig && (
            <ProductConfigDetail
              config={selectedConfig}
              onEdit={() => {
                setIsDetailOpen(false);
                handleEdit(selectedConfig);
              }}
              onDelete={() => handleDelete(selectedConfig)}
              onToggleActive={() => handleToggleActive(selectedConfig)}
              onClose={() => setIsDetailOpen(false)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ProductConfigAdmin;