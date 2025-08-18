import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Plus, 
  Eye, 
  Search
} from 'lucide-react';

import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Badge } from "../components/ui/badge";
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle 
} from "../components/ui/dialog";

import { Skeleton } from "../components/ui/skeleton";
import { Alert, AlertDescription } from "../components/ui/alert";
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from "../components/ui/tooltip";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from "../components/ui/pagination";

import { Interpretation } from '../types/interpretation';
import interpretationService from '../services/interpretationService';

const Interpretations: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [duplicateDialogOpen, setDuplicateDialogOpen] = useState(false);
  const [selectedInterpretation, setSelectedInterpretation] = useState<Interpretation | null>(null);
  const [newTestName, setNewTestName] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Fetch interpretations
  const {
    data: interpretations = [],
    isLoading,
    error
  } = useQuery('interpretations', () => interpretationService.getAll(), {
    onError: (error: any) => {
      toast.error('Failed to load interpretations');
      console.error('Error loading interpretations:', error);
    }
  });

  // Delete mutation
  const deleteMutation = useMutation((id: string) => interpretationService.delete(id), {
    onSuccess: () => {
      queryClient.invalidateQueries('interpretations');
      toast.success('Interpretation deleted successfully');
      setDeleteDialogOpen(false);
      setSelectedInterpretation(null);
    },
    onError: (error: any) => {
      toast.error('Failed to delete interpretation');
      console.error('Error deleting interpretation:', error);
    }
  });

  // Duplicate mutation
  const duplicateMutation = useMutation(
    ({ id, testName }: { id: string; testName: string }) =>
      interpretationService.duplicate(id, testName),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('interpretations');
        toast.success('Interpretation duplicated successfully');
        setDuplicateDialogOpen(false);
        setSelectedInterpretation(null);
        setNewTestName('');
      },
      onError: (error: any) => {
        toast.error('Failed to duplicate interpretation');
        console.error('Error duplicating interpretation:', error);
      }
    }
  );

  // Filter interpretations based on search term
  const filteredInterpretations = interpretations.filter(interpretation =>
    interpretation.testName.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Pagination calculations
  const totalPages = Math.ceil(filteredInterpretations.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedInterpretations = filteredInterpretations.slice(startIndex, endIndex);

  // Reset to first page when search term changes
  React.useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm]);

  const handleView = (interpretation: Interpretation) => {
    navigate(`/interpretations/${interpretation._id}`);
  };

  const handleEdit = (interpretation: Interpretation) => {
    navigate(`/interpretations/${interpretation._id}/edit`);
  };

  const handleDelete = (interpretation: Interpretation) => {
    setSelectedInterpretation(interpretation);
    setDeleteDialogOpen(true);
  };

  const handleDuplicate = (interpretation: Interpretation) => {
    setSelectedInterpretation(interpretation);
    setDuplicateDialogOpen(true);
    setNewTestName(`${interpretation.testName}_copy`);
  };

  const confirmDelete = () => {
    if (selectedInterpretation?._id) {
      deleteMutation.mutate(selectedInterpretation._id);
    }
  };

  const confirmDuplicate = () => {
    if (selectedInterpretation?._id && newTestName.trim()) {
      duplicateMutation.mutate({
        id: selectedInterpretation._id,
        testName: newTestName.trim()
      });
    }
  };

  if (error) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load interpretations. Please try again later.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const tableVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: {
        staggerChildren: 0.05
      }
    }
  };

  const rowVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <TooltipProvider>
      <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <motion.h1 
          className="text-3xl font-bold tracking-tight"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          Interpretations Management
        </motion.h1>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Button 
            onClick={() => navigate('/interpretations/new')}
            className="gap-2 cursor-pointer bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2 shadow-lg"
          >
            <Plus size={16} />
            Add New Interpretation
          </Button>
        </motion.div>
      </div>

      {/* Search */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <Card>
          <CardContent className="pt-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search interpretations by test name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Interpretations Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <Card>
          <CardHeader className="pb-0">
            <CardTitle>Interpretations</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Test Name</TableHead>
                  <TableHead>Test Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <AnimatePresence>
                  {isLoading ? (
                    // Loading skeleton
                    Array.from({ length: 5 }).map((_, index) => (
                      <TableRow key={index}>
                        <TableCell><Skeleton className="h-5 w-full" /></TableCell>
                        <TableCell><Skeleton className="h-5 w-24" /></TableCell>
                        <TableCell><Skeleton className="h-5 w-16" /></TableCell>
                        <TableCell><Skeleton className="h-5 w-24" /></TableCell>
                        <TableCell><Skeleton className="h-5 w-28" /></TableCell>
                      </TableRow>
                    ))
                  ) : filteredInterpretations.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="h-24 text-center">
                        <p className="text-muted-foreground">
                          {searchTerm ? 'No interpretations found matching your search.' : 'No interpretations found. Create your first interpretation!'}
                        </p>
                      </TableCell>
                    </TableRow>
                  ) : (
                    paginatedInterpretations.map((interpretation) => {
                      // Get dimension count based on test type
                      const getDimensionCount = () => {
                        if (interpretation.results?.dimensions) {
                          return Object.keys(interpretation.results.dimensions).length;
                        }
                        return 0;
                      };
                      
                      const dimensionCount = getDimensionCount();
                      
                      return (
                        <motion.tr 
                          key={interpretation._id}
                          variants={rowVariants}
                          initial="hidden"
                          animate="visible"
                          className="group hover:bg-muted/50"
                          whileHover={{ backgroundColor: "rgba(0,0,0,0.03)" }}
                        >
                          <TableCell>
                            <div className="font-medium flex flex-col">
                              <span className="text-primary group-hover:text-primary/80 transition-colors">
                                {interpretation.testName}
                              </span>
                              {dimensionCount > 0 && (
                                <span className="text-xs text-muted-foreground">
                                  {dimensionCount} dimension{dimensionCount !== 1 ? 's' : ''}
                                </span>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="bg-primary/10 hover:bg-primary/20">
                              {interpretation.testType}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant={interpretation.isActive ? "default" : "secondary"}>
                              {interpretation.isActive ? 'Active' : 'Inactive'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <span className="text-muted-foreground text-sm">
                              {interpretation.createdAt
                                ? new Date(interpretation.createdAt).toLocaleDateString()
                                : 'N/A'
                              }
                            </span>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-2">
                              <div className="border border-blue-200 rounded-md bg-blue-50/50 p-1">
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      onClick={() => handleView(interpretation)}
                                      className="text-blue-500 hover:text-blue-700 hover:bg-blue-100 cursor-pointer h-8 w-8"
                                    >
                                      <Eye size={16} />
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p>View interpretation details</p>
                                  </TooltipContent>
                                </Tooltip>
                              </div>
                            </div>
                          </TableCell>
                        </motion.tr>
                      );
                    })
                  )}
                </AnimatePresence>
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </motion.div>

      {/* Pagination */}
      {totalPages > 1 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-6 flex justify-center"
        >
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious 
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  className={currentPage === 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
                />
              </PaginationItem>
              
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                if (
                  page === 1 ||
                  page === totalPages ||
                  (page >= currentPage - 1 && page <= currentPage + 1)
                ) {
                  return (
                    <PaginationItem key={page}>
                      <PaginationLink
                        onClick={() => setCurrentPage(page)}
                        isActive={currentPage === page}
                        className="cursor-pointer"
                      >
                        {page}
                      </PaginationLink>
                    </PaginationItem>
                  );
                } else if (
                  page === currentPage - 2 ||
                  page === currentPage + 2
                ) {
                  return (
                    <PaginationItem key={page}>
                      <PaginationEllipsis />
                    </PaginationItem>
                  );
                }
                return null;
              })}
              
              <PaginationItem>
                <PaginationNext 
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  className={currentPage === totalPages ? "pointer-events-none opacity-50" : "cursor-pointer"}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </motion.div>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Delete</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete the interpretation for "{selectedInterpretation?.testName}"?
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={confirmDelete}
              disabled={deleteMutation.isLoading}
            >
              {deleteMutation.isLoading ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Duplicate Dialog */}
      <Dialog open={duplicateDialogOpen} onOpenChange={setDuplicateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Duplicate Interpretation</DialogTitle>
            <DialogDescription>
              Create a copy of "{selectedInterpretation?.testName}" with a new test name:
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Input
              placeholder="New Test Name"
              value={newTestName}
              onChange={(e) => setNewTestName(e.target.value)}
              className={!newTestName.trim() ? "border-destructive" : ""}
            />
            {!newTestName.trim() && (
              <p className="text-destructive text-sm mt-2">Test name is required</p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDuplicateDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={confirmDuplicate}
              disabled={!newTestName.trim() || duplicateMutation.isLoading}
            >
              {duplicateMutation.isLoading ? 'Duplicating...' : 'Duplicate'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      </div>
    </TooltipProvider>
  );
};

export default Interpretations;