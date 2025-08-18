import React, { useState, useMemo, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronRight, 
  ChevronDown, 
  Search, 
  Copy, 
  Edit, 
  Trash2, 
  Plus, 
  Eye,
  EyeOff,
  Filter, 
  Expand, 
  Minimize2,
  FileText,
  Code,
  Settings,
  Download,
  Upload,
  Hash,
  Type,
  ToggleLeft
} from 'lucide-react';
import toast from 'react-hot-toast';

import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { cn } from '../lib/utils';

interface JsonViewerProps {
  data: any;
  mode?: 'view' | 'edit' | 'raw';
  onDataChange?: (newData: any) => void;
  className?: string;
  defaultExpandDepth?: number;
  searchable?: boolean;
  editable?: boolean;
  title?: string;
  description?: string;
}

interface TreeNode {
  key: string;
  value: any;
  path: string;
  type: 'object' | 'array' | 'string' | 'number' | 'boolean' | 'null';
  level: number;
  expanded: boolean;
  children?: TreeNode[];
  parent?: TreeNode;
}

interface SearchResult {
  node: TreeNode;
  matchType: 'key' | 'value' | 'both';
  matchIndex: number;
}

const JsonViewer: React.FC<JsonViewerProps> = ({
  data,
  mode = 'view',
  onDataChange,
  className = '',
  defaultExpandDepth = 1,
  searchable = true,
  editable = false,
  title = 'JSON Viewer',
  description = 'Interactive JSON data viewer with search and navigation capabilities'
}) => {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchMode, setSearchMode] = useState<'keys' | 'values' | 'both'>('both');
  const [currentSearchIndex, setCurrentSearchIndex] = useState(0);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);

  const [expandedStrings, setExpandedStrings] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<'tree' | 'table' | 'raw'>('tree');
  const [expandDepth, setExpandDepth] = useState(defaultExpandDepth);
  const [isAllExpanded, setIsAllExpanded] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const treeRef = useRef<HTMLDivElement>(null);

  // Build tree structure
  const buildTree = useCallback((obj: any, path: string = '', level: number = 0, parent?: TreeNode, parentKey?: string): TreeNode[] => {
    if (obj === null) {
      return [{
        key: parentKey || 'null',
        value: null,
        path,
        type: 'null',
        level,
        expanded: false,
        parent
      }];
    }

    if (Array.isArray(obj)) {
      return [{
        key: parentKey || `array[${obj.length}]`,
        value: obj,
        path,
        type: 'array',
        level,
        expanded: level < expandDepth,
        children: obj.map((item, index) => 
          buildTree(item, `${path}[${index}]`, level + 1, parent, `[${index}]`)
        ).flat(),
        parent
      }];
    }

    if (typeof obj === 'object') {
      const children = Object.entries(obj).map(([key, value]) => 
        buildTree(value, path ? `${path}.${key}` : key, level + 1, parent, key)
      ).flat();

      return [{
        key: parentKey || 'object',
        value: obj,
        path,
        type: 'object',
        level,
        expanded: level < expandDepth,
        children,
        parent
      }];
    }

    return [{
      key: parentKey || String(obj),
      value: obj,
      path,
      type: typeof obj as 'string' | 'number' | 'boolean',
      level,
      expanded: false,
      parent
    }];
  }, [expandDepth]);

  const treeData = useMemo(() => buildTree(data), [data, buildTree]);

  // Search functionality
  const performSearch = useCallback(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setCurrentSearchIndex(0);
      return;
    }

    const results: SearchResult[] = [];
    const query = searchQuery.toLowerCase();

    const searchNode = (node: TreeNode) => {
      if (searchMode === 'keys' || searchMode === 'both') {
        if (node.key.toLowerCase().includes(query)) {
          results.push({
            node,
            matchType: 'key',
            matchIndex: node.key.toLowerCase().indexOf(query)
          });
        }
      }

      if (searchMode === 'values' || searchMode === 'both') {
        if (typeof node.value === 'string' && node.value.toLowerCase().includes(query)) {
          results.push({
            node,
            matchType: 'value',
            matchIndex: node.value.toLowerCase().indexOf(query)
          });
        }
      }

      if (node.children) {
        node.children.forEach(searchNode);
      }
    };

    treeData.forEach(searchNode);
    setSearchResults(results);
    setCurrentSearchIndex(0);
  }, [searchQuery, searchMode, treeData]);

  useMemo(() => performSearch(), [performSearch]);

  // Expand/collapse functionality
  const toggleNode = useCallback((node: TreeNode) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(node.path)) {
      newExpanded.delete(node.path);
    } else {
      newExpanded.add(node.path);
    }
    setExpandedNodes(newExpanded);
  }, [expandedNodes]);

  const expandToDepth = useCallback((depth: number) => {
    const newExpanded = new Set<string>();
    
    const expandNode = (node: TreeNode, currentDepth: number) => {
      if (currentDepth < depth) {
        newExpanded.add(node.path);
        if (node.children) {
          node.children.forEach(child => expandNode(child, currentDepth + 1));
        }
      }
    };

    treeData.forEach(node => expandNode(node, 0));
    setExpandedNodes(newExpanded);
  }, [treeData]);

  // Copy functionality
  const copyToClipboard = useCallback(async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(type);
      setTimeout(() => setCopied(null), 2000);
      toast.success('Copied to clipboard');
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      toast.error('Failed to copy to clipboard');
    }
  }, []);

  const copyValue = useCallback((node: TreeNode) => {
    copyToClipboard(JSON.stringify(node.value, null, 2), 'value');
  }, [copyToClipboard]);

  const copyPath = useCallback((node: TreeNode) => {
    copyToClipboard(node.path, 'path');
  }, [copyToClipboard]);

  const copyAll = useCallback(() => {
    copyToClipboard(JSON.stringify(data, null, 2), 'all');
  }, [data, copyToClipboard]);

  // Get type badge with enhanced color coding
  const getTypeBadge = (node: TreeNode) => {
    const typeConfig = {
      object: {
        variant: 'default' as const,
        className: 'bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-200',
        icon: Hash,
        label: 'object'
      },
      array: {
        variant: 'secondary' as const,
        className: 'bg-purple-100 text-purple-800 border-purple-200 hover:bg-purple-200',
        icon: Filter,
        label: `array[${node.value?.length || 0}]`
      },
      string: {
        variant: 'outline' as const,
        className: 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100',
        icon: Type,
        label: 'string'
      },
      number: {
        variant: 'destructive' as const,
        className: 'bg-orange-100 text-orange-800 border-orange-200 hover:bg-orange-200',
        icon: Hash,
        label: 'number'
      },
      boolean: {
        variant: 'secondary' as const,
        className: 'bg-indigo-100 text-indigo-800 border-indigo-200 hover:bg-indigo-200',
        icon: ToggleLeft,
        label: 'bool'
      },
      null: {
        variant: 'outline' as const,
        className: 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100',
        icon: Minimize2,
        label: 'null'
      }
    };

    const config = typeConfig[node.type];
    const IconComponent = config.icon;

    return (
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.2 }}
      >
        <Badge 
          variant={config.variant} 
          className={cn('text-xs flex items-center gap-1 transition-all duration-200', config.className)}
        >
          <IconComponent size={10} />
          {config.label}
        </Badge>
      </motion.div>
    );
  };

  // Render node value with enhanced styling and animations
  const renderValue = (node: TreeNode) => {
    if (node.type === 'null') {
      return (
        <motion.span 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-muted-foreground italic font-mono px-2 py-1 bg-gray-50 rounded-md border"
        >
          null
        </motion.span>
      );
    }

    if (node.type === 'boolean') {
      return (
        <motion.span 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.2 }}
          className={cn(
            "font-mono px-3 py-1 rounded-full text-sm font-medium transition-all duration-200",
            node.value 
              ? "bg-emerald-100 text-emerald-800 border border-emerald-200" 
              : "bg-red-100 text-red-800 border border-red-200"
          )}
        >
          {String(node.value)}
        </motion.span>
      );
    }

    if (node.type === 'number') {
      return (
        <motion.span 
          initial={{ x: -10, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.2 }}
          className="font-mono text-orange-700 bg-orange-50 px-3 py-1 rounded-md border border-orange-200 font-semibold"
        >
          {node.value}
        </motion.span>
      );
    }

    if (node.type === 'string') {
      const isLongText = node.value.length > 80;
      
      
      return (
        <motion.div 
          initial={{ y: 10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="flex flex-col gap-3"
        >
          <div className="flex items-center gap-3">
            <span className="text-foreground break-words bg-green-50 px-3 py-2 rounded-lg border border-green-200 font-medium text-green-800">
              {isLongText && !expandedStrings.has(node.path) ? `${node.value.substring(0, 80)}...` : node.value}
            </span>
            {isLongText && (
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-8 px-3 text-xs hover:bg-green-100"
                onClick={(e) => {
                  e.stopPropagation();
                  const newExpanded = new Set(expandedStrings);
                  if (newExpanded.has(node.path)) {
                    newExpanded.delete(node.path);
                  } else {
                    newExpanded.add(node.path);
                  }
                  setExpandedStrings(newExpanded);
                }}
              >
                {expandedStrings.has(node.path) ? (
                  <>
                    <EyeOff size={12} className="mr-1" />
                    Show less
                  </>
                ) : (
                  <>
                    <Eye size={12} className="mr-1" />
                    Show more
                  </>
                )}
              </Button>
            )}

          </div>

        </motion.div>
      );
    }

    return null;
  };

  // Render tree node with enhanced animations and visual hierarchy
  const renderTreeNode = (node: TreeNode, isHighlighted = false) => {
    const isExpanded = expandedNodes.has(node.path);
    const hasChildren = node.children && node.children.length > 0;
    const isSelected = selectedNode?.path === node.path;
    const isLeafNode = !hasChildren && (node.type === 'string' || node.type === 'number' || node.type === 'boolean' || node.type === 'null');

    return (
      <motion.div 
        key={node.path}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3, delay: node.level * 0.05 }}
        className={cn(
          "tree-node border-l-2 transition-all duration-300 rounded-r-lg mb-1",
          "hover:bg-gradient-to-r hover:from-muted/30 hover:to-transparent",
          isHighlighted && "bg-gradient-to-r from-yellow-100/80 to-yellow-50/40 border-yellow-400 shadow-sm",
          isSelected && "bg-gradient-to-r from-blue-100/80 to-blue-50/40 border-blue-400 shadow-md",
          !isHighlighted && !isSelected && "border-gray-200 hover:border-gray-300"
        )}
        style={{ marginLeft: `${node.level * 16}px` }}
      >
        <motion.div 
          className="flex items-center gap-3 p-3 cursor-pointer group"
          onClick={() => {
            setSelectedNode(node);
            if (hasChildren) {
              toggleNode(node);
            }
          }}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
        >
          <div className="flex items-center gap-3 min-w-0 flex-1">
            {hasChildren && (
              <motion.div
                className="flex items-center justify-center w-7 h-7 rounded transition-colors duration-200"
              >
                <motion.div
                  animate={{ rotate: isExpanded ? 90 : 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <ChevronRight size={14} />
                </motion.div>
              </motion.div>
            )}
            
            <span className="font-mono text-sm font-medium text-foreground truncate px-2 py-1 bg-gray-50 rounded-md border">
              {node.key}
            </span>
            
            {getTypeBadge(node)}
            
            {node.type === 'string' && node.value.length > 80 && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.1 }}
              >
                <Badge variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-200">
                  {node.value.length} chars
                </Badge>
              </motion.div>
            )}
          </div>

          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 hover:bg-green-100 transition-colors duration-200"
                onClick={(e) => {
                  e.stopPropagation();
                  copyValue(node);
                }}
                title="Copy value"
              >
                <Copy size={12} />
              </Button>
            </motion.div>
            
            <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 hover:bg-purple-100 transition-colors duration-200"
                onClick={(e) => {
                  e.stopPropagation();
                  copyPath(node);
                }}
                title="Copy path"
              >
                <Hash size={12} />
              </Button>
            </motion.div>

            {editable && (
              <>
                <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 hover:bg-blue-100 transition-colors duration-200"
                    onClick={(e) => {
                      e.stopPropagation();
                      // Edit functionality would go here
                    }}
                    title="Edit"
                  >
                    <Edit size={12} />
                  </Button>
                </motion.div>
                
                <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 text-destructive hover:text-destructive hover:bg-red-100 transition-colors duration-200"
                    onClick={(e) => {
                      e.stopPropagation();
                      // Delete functionality would go here
                    }}
                    title="Delete"
                  >
                    <Trash2 size={12} />
                  </Button>
                </motion.div>
              </>
            )}
          </div>
        </motion.div>

        {isLeafNode && (
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, delay: 0.1 }}
            className="ml-8 mb-3 mr-4"
          >
            {renderValue(node)}
          </motion.div>
        )}

        <AnimatePresence>
          {isExpanded && hasChildren && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="ml-4 space-y-1">
                {node.children!.map((child, index) => (
                  <motion.div
                    key={child.path}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.2, delay: index * 0.05 }}
                  >
                    {renderTreeNode(child, isHighlighted)}
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    );
  };

  // Breadcrumb component
  const Breadcrumb = ({ path }: { path: string }) => (
    <div className="flex items-center gap-1 text-sm text-muted-foreground font-mono">
      <span>$</span>
      {path.split('.').map((segment, index) => (
        <React.Fragment key={index}>
          <span className="text-muted-foreground">.</span>
          <span className="hover:text-foreground cursor-pointer">[{segment}]</span>
        </React.Fragment>
      ))}
    </div>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="json-viewer h-full flex flex-col"
    >
      <Card className={cn("shadow-lg rounded-lg overflow-hidden", className)}>
        <CardHeader className="bg-gradient-to-r from-slate-50 to-gray-50 backdrop-blur-sm">
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="flex items-center justify-between"
          >
            <div>
              <CardTitle className="flex items-center gap-3">
                <motion.div
                  whileHover={{ scale: 1.1, rotate: 5 }}
                  transition={{ duration: 0.2 }}
                >
                  <FileText size={24} className="text-blue-600" />
                </motion.div>
                <motion.span
                  className="text-xl font-bold text-gray-800"
                  whileHover={{ scale: 1.02 }}
                >
                  {title}
                </motion.span>
              </CardTitle>
              <CardDescription className="text-gray-600 mt-1">{description}</CardDescription>
            </div>
            <div className="flex items-center gap-3">
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyAll}
                  className={cn(
                    "transition-all duration-200 hover:bg-green-50",
                    copied === 'all' && "bg-green-100 text-green-800 border-green-300"
                  )}
                >
                  <Copy size={14} className="mr-2" />
                  {copied === 'all' ? 'Copied!' : 'Copy All'}
                </Button>
              </motion.div>

            </div>
          </motion.div>
        </CardHeader>

        <CardContent className="p-0 bg-gradient-to-br from-white to-gray-50/30">
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="border-b border-gray-200 bg-gradient-to-r from-gray-50/50 to-slate-50/50"
          >
            <div className="flex flex-col lg:flex-row lg:items-center justify-between p-4 md:p-6 gap-4">
              <div className="flex items-center gap-2 flex-wrap">
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      if (isAllExpanded) {
                        expandToDepth(0);
                        setIsAllExpanded(false);
                      } else {
                        expandToDepth(999);
                        setIsAllExpanded(true);
                      }
                    }}
                    className={cn(
                      "transition-colors duration-200",
                      isAllExpanded ? "hover:bg-orange-50" : "hover:bg-green-50"
                    )}
                  >
                    {isAllExpanded ? (
                      <>
                        <Minimize2 size={14} className="mr-1" />
                        <span className="hidden sm:inline">Collapse All</span>
                      </>
                    ) : (
                      <>
                        <Expand size={14} className="mr-1" />
                        <span className="hidden sm:inline">Expand All</span>
                      </>
                    )}
                  </Button>
                </motion.div>
                
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => expandToDepth(1)}
                    className="hover:bg-blue-50 transition-colors duration-200"
                  >
                    Depth 1
                  </Button>
                </motion.div>
                
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => expandToDepth(2)}
                    className="hover:bg-blue-50 transition-colors duration-200"
                  >
                    Depth 2
                  </Button>
                </motion.div>
              </div>
            </div>
          </motion.div>
            {/* Search and controls */}
            {searchable && (
              <motion.div 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.3 }}
                className="p-4 md:p-6 border-b border-gray-200 bg-gradient-to-r from-gray-50/30 to-slate-50/30"
              >
                <div className="flex flex-col lg:flex-row items-start lg:items-center gap-4">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 flex-1 w-full">
                    <div className="relative flex-1 w-full max-w-md">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={16} />
                      <Input
                        type="text"
                        placeholder="Search keys and values..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10 bg-white/80 backdrop-blur-sm border-gray-200 focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition-all duration-200"
                      />
                    </div>
                    
                    <select
                      value={searchMode}
                      onChange={(e) => setSearchMode(e.target.value as 'keys' | 'values' | 'both')}
                      className="px-3 py-2 border border-gray-200 rounded-md focus:ring-2 focus:ring-blue-100 focus:border-blue-400 bg-white/80 backdrop-blur-sm transition-all duration-200 min-w-[140px]"
                    >
                      <option value="both">Keys & Values</option>
                      <option value="keys">Keys Only</option>
                      <option value="values">Values Only</option>
                    </select>

                    <AnimatePresence>
                      {searchResults.length > 0 && (
                        <motion.div 
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.9 }}
                          className="flex items-center gap-2 text-sm text-muted-foreground bg-blue-50 px-3 py-2 rounded-md border border-blue-200"
                        >
                          <span className="font-medium">{currentSearchIndex + 1} of {searchResults.length}</span>
                          <div className="flex gap-1">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setCurrentSearchIndex(Math.max(0, currentSearchIndex - 1))}
                              className="h-7 w-7 p-0 hover:bg-blue-100"
                            >
                              ↑
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setCurrentSearchIndex(Math.min(searchResults.length - 1, currentSearchIndex + 1))}
                              className="h-7 w-7 p-0 hover:bg-blue-100"
                            >
                              ↓
                            </Button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>

                {/* Breadcrumb */}
                <AnimatePresence>
                  {selectedNode && (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                      className="mt-4 bg-white/60 p-3 rounded-lg border border-gray-200"
                    >
                      <Breadcrumb path={selectedNode.path} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )}

            {/* Main content */}
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4, delay: 0.4 }}
              className="flex flex-col lg:flex-row min-h-[500px] lg:h-96"
            >
              {/* Left pane - Dimensions Index */}
              <motion.div 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: 0.5 }}
                className="w-full lg:w-1/4 border-b lg:border-b-0 lg:border-r border-gray-200 p-3 md:p-4 overflow-y-auto bg-gradient-to-br from-gray-50/30 to-white/50"
              >
                <motion.h3 
                  className="font-medium text-gray-600 mb-3 text-sm uppercase tracking-wide"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                >
                  Index
                </motion.h3>
                <div className="space-y-3">
                  {treeData.map((node, index) => (
                    <motion.div
                      key={node.path}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: 0.7 + index * 0.1 }}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Card
                        className={cn(
                          "cursor-pointer transition-all duration-200 hover:shadow-md",
                          selectedNode?.path === node.path 
                            ? "bg-blue-50 border-blue-300 shadow-md" 
                            : "hover:bg-gray-50 border-gray-200"
                        )}
                        onClick={() => setSelectedNode(node)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-center gap-3 mb-3">
                            <span className="font-semibold text-gray-800 truncate">{node.key}</span>
                            {getTypeBadge(node)}
                          </div>
                          {node.type === 'object' && node.value && (
                            <div className="text-sm text-gray-600 bg-blue-50 px-2 py-1 rounded-md">
                              {Object.keys(node.value).length} properties
                            </div>
                          )}
                          {node.type === 'array' && node.value && (
                            <div className="text-sm text-gray-600 bg-purple-50 px-2 py-1 rounded-md">
                              {node.value.length} items
                            </div>
                          )}
                          {node.type === 'string' && (
                            <div className="text-sm text-gray-600 bg-green-50 px-2 py-1 rounded-md truncate">
                              {node.value.substring(0, 60)}
                              {node.value.length > 60 && '...'}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              </motion.div>

              {/* Right pane - Tree Inspector */}
              <motion.div 
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: 0.5 }}
                className="w-full lg:w-3/4 p-4 md:p-6 overflow-y-auto bg-gradient-to-br from-white to-gray-50/30" 
                ref={treeRef}
              >
                <div className="space-y-2">
                  {treeData.map((node, index) => (
                    <motion.div
                      key={node.path}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: 0.6 + index * 0.1 }}
                    >
                      {renderTreeNode(node)}
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            </motion.div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default JsonViewer;
