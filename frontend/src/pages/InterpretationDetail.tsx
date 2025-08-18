import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Alert,
  Skeleton,
  Breadcrumbs,
  Link,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import {
  ArrowBack,
  Edit,
  ContentCopy,
  Delete
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import interpretationService from '../services/interpretationService';
import InterpretationDisplay from '../components/InterpretationDisplay';

const InterpretationDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [duplicateDialogOpen, setDuplicateDialogOpen] = useState(false);
  const [duplicateName, setDuplicateName] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const {
    data: interpretation,
    isLoading,
    error
  } = useQuery(
    ['interpretation', id],
    () => interpretationService.getById(id!),
    {
      enabled: !!id,
      onError: (error: any) => {
        toast.error('Failed to load interpretation details');
        console.error('Error loading interpretation:', error);
      }
    }
  );

  const duplicateMutation = useMutation(
    (data: { id: string; name: string }) => interpretationService.duplicate(data.id, data.name),
    {
      onSuccess: () => {
        toast.success('Interpretation duplicated successfully');
        queryClient.invalidateQueries(['interpretations']);
        setDuplicateDialogOpen(false);
        setDuplicateName('');
      },
      onError: (error: any) => {
        toast.error('Failed to duplicate interpretation');
        console.error('Error duplicating interpretation:', error);
      }
    }
  );

  const deleteMutation = useMutation(
    (id: string) => interpretationService.delete(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['interpretations']);
        toast.success('Interpretation deleted successfully');
        navigate('/interpretations');
      },
      onError: (error: any) => {
        toast.error('Failed to delete interpretation');
        console.error('Error deleting interpretation:', error);
      }
    }
  );

  const handleDuplicate = () => {
    if (!interpretation) return;
    setDuplicateName(`${interpretation.testName} (Copy)`);
    setDuplicateDialogOpen(true);
  };

  const checkDuplicateTestName = async (testName: string): Promise<boolean> => {
    try {
      return await interpretationService.checkTestNameExists(testName);
    } catch (error: any) {
      console.error('Error checking duplicate test name:', error);
      toast.error('Error checking for duplicate test name');
      return false; // Assume no duplicate on error to allow proceeding
    }
  };

  const handleDuplicateConfirm = async () => {
     if (!interpretation?._id || !duplicateName.trim()) return;
     
     const isDuplicate = await checkDuplicateTestName(duplicateName.trim());
     if (isDuplicate) {
       toast.error(`Test name "${duplicateName.trim()}" already exists. Please choose a different name.`);
       return;
     }
     duplicateMutation.mutate({ id: interpretation._id, name: duplicateName.trim() });
   };

  const handleDelete = () => {
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (!interpretation?._id) return;
    deleteMutation.mutate(interpretation._id);
  };

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load interpretation details. Please try again later.
        </Alert>
      </Box>
    );
  }

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Skeleton variant="text" width={300} height={40} />
        <Skeleton variant="rectangular" width="100%" height={200} sx={{ mt: 2 }} />
        <Skeleton variant="rectangular" width="100%" height={400} sx={{ mt: 2 }} />
      </Box>
    );
  }

  if (!interpretation) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">
          Interpretation not found.
        </Alert>
      </Box>
    );
  }

  const renderResults = () => {
    if (!interpretation.results) return null;
    
    return <InterpretationDisplay 
      interpretation={interpretation} 
      onUpdate={() => {
          // Invalidate and refetch the interpretation data
          queryClient.invalidateQueries({ queryKey: ['interpretation', id] });
        }}
    />;
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link component={RouterLink} to="/interpretations" underline="hover">
          Interpretations
        </Link>
        <Typography color="text.primary">{interpretation.testName}</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Button
            startIcon={<ArrowBack />}
            onClick={() => navigate('/interpretations')}
            sx={{ mb: 2 }}
          >
            Back to Interpretations
          </Button>
          <Typography variant="h4" component="h1" gutterBottom>
            {interpretation.testName}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip 
              label={interpretation.testType} 
              color="primary" 
              variant="outlined"
            />
            <Chip 
              label={interpretation.isActive ? 'Active' : 'Inactive'} 
              color={interpretation.isActive ? 'success' : 'default'} 
              variant="outlined"
            />
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<ContentCopy />}
            onClick={handleDuplicate}
          >
            Duplicate
          </Button>
          <Button
            variant="contained"
            startIcon={<Edit />}
            onClick={() => navigate(`/interpretations/${interpretation._id}/edit`)}
          >
            Edit
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<Delete />}
            onClick={handleDelete}
            sx={{ cursor: 'pointer' }}
          >
            Delete
          </Button>
        </Box>
      </Box>

      {/* Overview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Overview
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Test Name
              </Typography>
              <Typography variant="h6">
                {interpretation.testName}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Test Type
              </Typography>
              <Typography variant="h6">
                {interpretation.testType}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Status
              </Typography>
              <Typography variant="h6">
                {interpretation.isActive ? 'Active' : 'Inactive'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Created
              </Typography>
              <Typography variant="h6">
                {interpretation.createdAt
                  ? new Date(interpretation.createdAt).toLocaleDateString()
                  : 'N/A'
                }
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Results */}
      {renderResults()}

      {!interpretation.results && (
        <Card>
          <CardContent>
            <Typography variant="body1" color="text.secondary" align="center">
              No results available for this interpretation.
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Duplicate Dialog */}
      <Dialog open={duplicateDialogOpen} onClose={() => setDuplicateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Duplicate Interpretation</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="New Interpretation Name"
            fullWidth
            variant="outlined"
            value={duplicateName}
            onChange={(e) => setDuplicateName(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDuplicateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleDuplicateConfirm} 
            variant="contained"
            disabled={!duplicateName.trim() || duplicateMutation.isLoading}
          >
            {duplicateMutation.isLoading ? 'Duplicating...' : 'Duplicate'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the interpretation for "{interpretation?.testName}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleDeleteConfirm} 
            variant="contained"
            color="error"
            disabled={deleteMutation.isLoading}
          >
            {deleteMutation.isLoading ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default InterpretationDetail;