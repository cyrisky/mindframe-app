import React, { useMemo, useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  IconButton,
  Alert,
  Breadcrumbs,
  Link,
  Tabs,
  Tab,
  Chip,
  Menu,
  MenuItem,
  Divider,
  Grid,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  ArrowBack,
  Save,
  Add,
  Delete,
  ExpandMore,
  Edit as EditIcon
} from '@mui/icons-material';
import { useNavigate, useParams, Link as RouterLink } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { toast } from 'react-hot-toast';
import Editor from '@monaco-editor/react';
import interpretationService from '../services/interpretationService';
import {
  CreateInterpretationRequest,
  Interpretation,
  InterpretationResults,
  PersonalValuesDimension,
  PersonalValuesResults,
  PersonalityDimensionLevel,
  PersonalityResults
} from '../types/interpretation';

interface InterpretationEditorProps {
  mode: 'create' | 'edit';
}

type EditorTab = 'guided' | 'json';

type SupportedTestName = 'personalValues' | 'kepribadian' | 'custom';

const PERSONAL_VALUES_KEYS: Array<keyof PersonalValuesResults['dimensions']> = [
  'achievement',
  'benevolence',
  'conformity',
  'hedonism',
  'power',
  'security',
  'selfDirection',
  'stimulation',
  'tradition',
  'universalism'
];

const BIG_FIVE_KEYS: Array<keyof PersonalityResults['dimensions']> = [
  'agreeableness',
  'conscientiousness',
  'extraversion',
  'neuroticism',
  'openness'
];

function createEmptyPersonalValue(): PersonalValuesDimension {
  return {
    title: '',
    description: '',
    manifestation: '',
    strengthChallenges: ''
  };
}

function createEmptyPersonalityLevel(): PersonalityDimensionLevel {
  return {
    interpretation: '',
    overview: '',
    aspekKehidupan: {
      gayaBelajar: [],
      hubunganInterpersonal: [],
      karir: [],
      kekuatan: [],
      kelemahan: [],
      kepemimpinan: []
    },
    rekomendasi: []
  };
}

function createPersonalValuesTemplate(): PersonalValuesResults {
  return {
    dimensions: {
      achievement: createEmptyPersonalValue()
    },
    topN: 3
  };
}

function createPersonalityTemplate(): PersonalityResults {
  return {
    dimensions: {
      agreeableness: {
        rendah: createEmptyPersonalityLevel(),
        sedang: createEmptyPersonalityLevel(),
        tinggi: createEmptyPersonalityLevel()
      }
    },
    overview: ''
  };
}

// Sub-components (to use hooks safely)
type ArrayEditorProps = {
  label: string;
  values: string[];
  onChange: (next: string[]) => void;
};

const ArrayEditor: React.FC<ArrayEditorProps> = ({ label, values, onChange }) => {
  const [draft, setDraft] = useState<string>('');

  const addArrayItem = (item: string) => {
    if (!item.trim()) return;
    onChange([...(values || []), item.trim()]);
  };

  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>{label}</Typography>
      <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
        <TextField
          fullWidth
          size="small"
          placeholder={`Add ${label} item...`}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              addArrayItem(draft);
              setDraft('');
            }
          }}
        />
        <Button
          variant="outlined"
          startIcon={<Add />}
          onClick={() => { addArrayItem(draft); setDraft(''); }}
        >
          Add
        </Button>
      </Box>
      {values.length === 0 ? (
        <Alert severity="info">No items added.</Alert>
      ) : (
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {values.map((item: string, index: number) => (
            <Chip
              key={`${item}-${index}`}
              label={item}
              onDelete={() => onChange(values.filter((_, i) => i !== index))}
            />
          ))}
        </Box>
      )}
    </Box>
  );
};

type RecommendationsEditorProps = {
  items: Array<{ title: string; description: string }>;
  onChange: (next: Array<{ title: string; description: string }>) => void;
};

const RecommendationsEditor: React.FC<RecommendationsEditorProps> = ({ items, onChange }) => {
  const [titleDraft, setTitleDraft] = useState<string>('');
  const [descDraft, setDescDraft] = useState<string>('');

  const addRec = () => {
    if (!titleDraft.trim() || !descDraft.trim()) return;
    onChange([...(items || []), { title: titleDraft.trim(), description: descDraft.trim() }]);
    setTitleDraft('');
    setDescDraft('');
  };

  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>Recommendations</Typography>
      <Grid container spacing={1} alignItems="center" sx={{ mb: 1 }}>
        <Grid item xs={12} md={4}>
          <TextField size="small" fullWidth label="Title" value={titleDraft} onChange={(e) => setTitleDraft(e.target.value)} />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField size="small" fullWidth label="Description" value={descDraft} onChange={(e) => setDescDraft(e.target.value)} />
        </Grid>
        <Grid item xs={12} md={2}>
          <Button fullWidth variant="outlined" startIcon={<Add />} onClick={addRec}>Add</Button>
        </Grid>
      </Grid>
      {items.length === 0 ? (
        <Alert severity="info">No recommendations added.</Alert>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {items.map((rec, index) => (
            <Card variant="outlined" key={`${rec.title}-${index}`}>
              <CardContent sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1 }}>
                <Box>
                  <Typography variant="subtitle2">{rec.title}</Typography>
                  <Typography variant="body2" color="text.secondary">{rec.description}</Typography>
                </Box>
                <IconButton color="error" onClick={() => onChange(items.filter((_, i) => i !== index))}>
                  <Delete />
                </IconButton>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );
};

const InterpretationEditor: React.FC<InterpretationEditorProps> = ({ mode }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { id } = useParams<{ id: string }>();

  const [tab, setTab] = useState<EditorTab>('guided');
  const [testName, setTestName] = useState<string>('camelCaseTest');
  const [testType, setTestType] = useState<string>('custom');
  const [isActive, setIsActive] = useState<boolean>(true);

  const [guidedResults, setGuidedResults] = useState<InterpretationResults>(createPersonalValuesTemplate());
  const [jsonValue, setJsonValue] = useState<string>(JSON.stringify(guidedResults, null, 2));

  // Load existing interpretation data when in edit mode
  const {
    data: existingInterpretation,
    isLoading: isLoadingInterpretation,
    error: loadError
  } = useQuery(
    ['interpretation', id],
    () => interpretationService.getById(id!),
    {
      enabled: mode === 'edit' && !!id,
      onError: (error: any) => {
        toast.error('Failed to load interpretation for editing');
        console.error('Error loading interpretation:', error);
      }
    }
  );

  // Populate form when existing interpretation is loaded
  useEffect(() => {
    if (mode === 'edit' && existingInterpretation) {
      setTestName(existingInterpretation.testName);
      setTestType(existingInterpretation.testType);
      setIsActive(existingInterpretation.isActive);
      setGuidedResults(existingInterpretation.results);
      setJsonValue(JSON.stringify(existingInterpretation.results, null, 2));
    }
  }, [mode, existingInterpretation]);

  const updateJsonFromGuided = (next: InterpretationResults) => {
    setGuidedResults(next);
    setJsonValue(JSON.stringify(next, null, 2));
  };

  const handleTestTypeChange = (type: string) => {
    setTestType(type);
    if (type === 'top-n-dimension') {
      const tmpl = createPersonalValuesTemplate();
      updateJsonFromGuided(tmpl);
    } else if (type === 'multiple-dimension') {
      const tmpl = createPersonalityTemplate();
      updateJsonFromGuided(tmpl);
    } else {
      const tmpl: InterpretationResults = { dimensions: {} };
      updateJsonFromGuided(tmpl);
    }
  };

  const createMutation = useMutation((data: CreateInterpretationRequest) => interpretationService.create(data), {
    onSuccess: (_created: Interpretation) => {
      queryClient.invalidateQueries('interpretations');
      toast.success('Interpretation created successfully');
      navigate('/interpretations');
    },
    onError: (error: any) => {
      toast.error('Failed to create interpretation');
      // eslint-disable-next-line no-console
      console.error('Error creating interpretation:', error);
    }
  });

  const updateMutation = useMutation(
    (data: { id: string; updateData: CreateInterpretationRequest }) => 
      interpretationService.update(data.id, data.updateData),
    {
      onSuccess: (_updated: Interpretation) => {
        queryClient.invalidateQueries('interpretations');
        queryClient.invalidateQueries(['interpretation', id]);
        toast.success('Interpretation updated successfully');
        navigate('/interpretations');
      },
      onError: (error: any) => {
        toast.error('Failed to update interpretation');
        console.error('Error updating interpretation:', error);
      }
    }
  );

  const checkDuplicateTestName = async (testName: string): Promise<boolean> => {
    try {
      return await interpretationService.checkTestNameExists(testName);
    } catch (error: any) {
      console.error('Error checking duplicate test name:', error);
      toast.error('Error checking for duplicate test name');
      return false; // Assume no duplicate on error to allow proceeding
    }
  };

  const handleSubmit = async () => {
    let resultsToSend: InterpretationResults | null = null;
    let finalTestName = testName.trim();
    let finalTestType = testType;
    
    if (tab === 'guided') {
      resultsToSend = guidedResults;
    } else {
      try {
        const parsed = JSON.parse(jsonValue);
        
        // Check if the parsed JSON is a complete interpretation object
        if (parsed.testName && parsed.testType && parsed.results) {
          // It's a complete interpretation object, extract the parts
          finalTestName = parsed.testName;
          finalTestType = parsed.testType;
          resultsToSend = parsed.results;
        } else {
          // It's just the results object
          resultsToSend = parsed;
        }
      } catch (e) {
        toast.error('Invalid JSON in Results editor');
        return;
      }
    }

    const payload: CreateInterpretationRequest = {
      testName: finalTestName,
      testType: finalTestType,
      results: resultsToSend as InterpretationResults
    };

    if (!payload.testName) {
      toast.error('Please provide a test name');
      return;
    }

    // Check for duplicate testName when creating new interpretation
    if (mode === 'create') {
      const isDuplicate = await checkDuplicateTestName(payload.testName);
      if (isDuplicate) {
        toast.error(`Test name "${payload.testName}" already exists. Please choose a different name.`);
        return;
      }
    }

    // Check for duplicate testName when editing (only if testName changed)
    if (mode === 'edit' && id && existingInterpretation) {
      if (payload.testName !== existingInterpretation.testName) {
        const isDuplicate = await checkDuplicateTestName(payload.testName);
        if (isDuplicate) {
          toast.error(`Test name "${payload.testName}" already exists. Please choose a different name.`);
          return;
        }
      }
    }

    if (mode === 'edit' && id) {
      updateMutation.mutate({ id, updateData: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  // Guided UI helpers
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const openAddMenu = Boolean(anchorEl);
  const handleOpenAddMenu = (event: React.MouseEvent<HTMLButtonElement>) => setAnchorEl(event.currentTarget);
  const handleCloseAddMenu = () => setAnchorEl(null);

  const availablePVKeys = useMemo(() => {
    if (testType !== 'top-n-dimension') return [] as string[];
    const existing = Object.keys((guidedResults as PersonalValuesResults).dimensions || {});
    return PERSONAL_VALUES_KEYS.filter((k) => !existing.includes(k as string)).map(String);
  }, [testType, guidedResults]);

  const addPersonalValueDimension = (key: string) => {
    const current = guidedResults as PersonalValuesResults;
    const next: PersonalValuesResults = {
      ...current,
      dimensions: {
        ...(current.dimensions || {}),
        [key]: createEmptyPersonalValue()
      }
    };
    updateJsonFromGuided(next);
    handleCloseAddMenu();
  };

  const removePersonalValueDimension = (key: string) => {
    const current = guidedResults as PersonalValuesResults;
    const nextDims = { ...(current.dimensions || {}) } as Record<string, PersonalValuesDimension>;
    delete nextDims[key];
    const next: PersonalValuesResults = {
      ...current,
      dimensions: nextDims
    };
    updateJsonFromGuided(next);
  };

  const updatePVField = (
    key: keyof PersonalValuesResults['dimensions'] | string,
    field: keyof PersonalValuesDimension,
    value: string
  ) => {
    const current = guidedResults as PersonalValuesResults;
    const currentDims = (current.dimensions || {}) as Record<string, PersonalValuesDimension>;
    const k = String(key);
    const next: PersonalValuesResults = {
      ...current,
      dimensions: {
        ...currentDims,
        [k]: {
          ...(currentDims[k] || createEmptyPersonalValue()),
          [field]: value,
        },
      },
    };
    updateJsonFromGuided(next);
  };

  const updatePVTopN = (value: number) => {
    const current = guidedResults as PersonalValuesResults;
    const next: PersonalValuesResults = { ...current, topN: value };
    updateJsonFromGuided(next);
  };

  const toggleBigFiveDimension = (key: string, enabled: boolean) => {
    const current = guidedResults as PersonalityResults;
    const nextDims = { ...(current.dimensions || {}) } as any;
    if (enabled) {
      nextDims[key] = {
        rendah: createEmptyPersonalityLevel(),
        sedang: createEmptyPersonalityLevel(),
        tinggi: createEmptyPersonalityLevel()
      };
    } else {
      delete nextDims[key];
    }
    const next: PersonalityResults = { ...current, dimensions: nextDims };
    updateJsonFromGuided(next);
  };

  const updatePersonalityOverview = (value: string) => {
    const current = guidedResults as PersonalityResults;
    const next: PersonalityResults = { ...current, overview: value };
    updateJsonFromGuided(next);
  };

  const updatePersonalityField = (
    dimKey: string,
    level: 'rendah' | 'sedang' | 'tinggi',
    field: keyof PersonalityDimensionLevel,
    value: any
  ) => {
    const current = guidedResults as PersonalityResults;
    const dim = (current.dimensions as any)[dimKey] || {};
    const lvl: PersonalityDimensionLevel = dim[level] || createEmptyPersonalityLevel();
    const nextLvl: PersonalityDimensionLevel = { ...lvl, [field]: value } as PersonalityDimensionLevel;
    const nextDim = { ...dim, [level]: nextLvl };
    const nextDims = { ...(current.dimensions as any), [dimKey]: nextDim };
    const next: PersonalityResults = { ...current, dimensions: nextDims };
    updateJsonFromGuided(next);
  };

  const addArrayItem = (arr: string[], setArr: (next: string[]) => void, item: string) => {
    if (!item.trim()) return;
    setArr([...arr, item.trim()]);
  };

  // Renderers
  const renderPersonalValuesGuided = () => {
    const current = guidedResults as PersonalValuesResults;
    const dims = current.dimensions || {};

    return (
      <Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
          <TextField
            type="number"
            label="Top N"
            size="small"
            value={current.topN ?? 3}
            onChange={(e) => updatePVTopN(Number(e.target.value))}
            sx={{ width: 140 }}
          />
          <Button
            variant="outlined"
            startIcon={<Add />}
            onClick={handleOpenAddMenu}
            disabled={availablePVKeys.length === 0}
          >
            Add Dimension
          </Button>
          {availablePVKeys.length === 0 && (
            <Chip label="All dimensions added" size="small" />
          )}
          <Menu anchorEl={anchorEl} open={openAddMenu} onClose={handleCloseAddMenu}>
            {availablePVKeys.map((k) => (
              <MenuItem key={k} onClick={() => addPersonalValueDimension(k)}>
                {k}
              </MenuItem>
            ))}
          </Menu>
        </Box>

        {Object.keys(dims).length === 0 ? (
          <Alert severity="info">No dimensions added yet.</Alert>
        ) : (
          Object.entries(dims).map(([key, value]) => (
            <Card key={key} sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ textTransform: 'capitalize' }}>{key}</Typography>
                  <IconButton color="error" onClick={() => removePersonalValueDimension(key)}>
                    <Delete />
                  </IconButton>
                </Box>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Title"
                      value={(value as PersonalValuesDimension)?.title || ''}
                      onChange={(e) => updatePVField(key, 'title', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Manifestation"
                      value={(value as PersonalValuesDimension)?.manifestation || ''}
                      onChange={(e) => updatePVField(key, 'manifestation', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      multiline
                      minRows={3}
                      label="Description"
                      value={(value as PersonalValuesDimension)?.description || ''}
                      onChange={(e) => updatePVField(key, 'description', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      multiline
                      minRows={2}
                      label="Strengths & Challenges"
                      value={(value as PersonalValuesDimension)?.strengthChallenges || ''}
                      onChange={(e) => updatePVField(key, 'strengthChallenges', e.target.value)}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          ))
        )}
      </Box>
    );
  };

  // removed inline editors; using sub-components above

  const renderPersonalityGuided = () => {
    const current = guidedResults as PersonalityResults;
    const dims = (current.dimensions || {}) as any;

    return (
      <Box>
        <TextField
          fullWidth
          multiline
          minRows={2}
          label="Overall Overview"
          value={current.overview || ''}
          onChange={(e) => updatePersonalityOverview(e.target.value)}
          sx={{ mb: 2 }}
        />

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          {BIG_FIVE_KEYS.map((k) => {
            const enabled = Boolean(dims[k as string]);
            return (
              <FormControlLabel
                key={String(k)}
                control={<Switch checked={enabled} onChange={(e) => toggleBigFiveDimension(String(k), e.target.checked)} />}
                label={String(k)}
              />
            );
          })}
        </Box>

        {Object.keys(dims).length === 0 ? (
          <Alert severity="info">No dimensions enabled. Toggle at least one Big Five dimension above.</Alert>
        ) : (
          Object.entries(dims).map(([dimKey, dimValue]: [string, any]) => (
            <Card key={dimKey} sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 1, textTransform: 'capitalize' }}>{dimKey}</Typography>
                <Divider sx={{ mb: 2 }} />

                {(['rendah', 'sedang', 'tinggi'] as const).map((level) => {
                  const lvl: PersonalityDimensionLevel = (dimValue?.[level] || createEmptyPersonalityLevel()) as PersonalityDimensionLevel;
                  return (
                    <Box key={`${dimKey}-${level}`} sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Chip label={level} color={level === 'tinggi' ? 'success' : level === 'sedang' ? 'warning' : 'error'} />
                        <Typography variant="subtitle2">{`Level: ${level}`}</Typography>
                      </Box>
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <TextField
                            fullWidth
                            label="Interpretation"
                            multiline
                            minRows={2}
                            value={lvl.interpretation}
                            onChange={(e) => updatePersonalityField(dimKey, level, 'interpretation', e.target.value)}
                          />
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <TextField
                            fullWidth
                            label="Overview"
                            multiline
                            minRows={2}
                            value={lvl.overview}
                            onChange={(e) => updatePersonalityField(dimKey, level, 'overview', e.target.value)}
                          />
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <ArrayEditor
                            label="Learning Style"
                            values={lvl.aspekKehidupan.gayaBelajar}
                            onChange={(next) => updatePersonalityField(dimKey, level, 'aspekKehidupan', { ...lvl.aspekKehidupan, gayaBelajar: next })}
                          />
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <ArrayEditor
                            label="Interpersonal"
                            values={lvl.aspekKehidupan.hubunganInterpersonal}
                            onChange={(next) => updatePersonalityField(dimKey, level, 'aspekKehidupan', { ...lvl.aspekKehidupan, hubunganInterpersonal: next })}
                          />
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <ArrayEditor
                            label="Career"
                            values={lvl.aspekKehidupan.karir}
                            onChange={(next) => updatePersonalityField(dimKey, level, 'aspekKehidupan', { ...lvl.aspekKehidupan, karir: next })}
                          />
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <ArrayEditor
                            label="Strengths"
                            values={lvl.aspekKehidupan.kekuatan}
                            onChange={(next) => updatePersonalityField(dimKey, level, 'aspekKehidupan', { ...lvl.aspekKehidupan, kekuatan: next })}
                          />
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <ArrayEditor
                            label="Areas for Growth"
                            values={lvl.aspekKehidupan.kelemahan}
                            onChange={(next) => updatePersonalityField(dimKey, level, 'aspekKehidupan', { ...lvl.aspekKehidupan, kelemahan: next })}
                          />
                        </Grid>
                        <Grid item xs={12}>
                          <RecommendationsEditor
                            items={lvl.rekomendasi}
                            onChange={(next) => updatePersonalityField(dimKey, level, 'rekomendasi', next)}
                          />
                        </Grid>
                      </Grid>
                      {level !== 'tinggi' && <Divider sx={{ mt: 2 }} />}
                    </Box>
                  );
                })}
              </CardContent>
            </Card>
          ))
        )}
      </Box>
    );
  };

  const handleTestNameChange = (value: string) => {
    setTestName(value);
  };

  const pageTitle = mode === 'edit' ? 'Edit Interpretation' : 'Create New Interpretation';

  return (
    <Box sx={{ p: 3 }}>
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link component={RouterLink} to="/interpretations" underline="hover">
          Interpretations
        </Link>
        <Typography color="text.primary">{pageTitle}</Typography>
      </Breadcrumbs>

      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h4" component="h1" gutterBottom>
            {pageTitle}
          </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button startIcon={<ArrowBack />} onClick={() => navigate('/interpretations')}>
            Back to Interpretations
          </Button>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleSubmit}
            disabled={createMutation.isLoading}
          >
            {createMutation.isLoading ? 'Saving...' : 'Save Interpretation'}
          </Button>
        </Box>
      </Box>

        <Card sx={{ mb: 3 }}>
          <CardContent>
          <Typography variant="h6" gutterBottom>Basic Information</Typography>
                    <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Test Name"
                value={testName}
                onChange={(e) => handleTestNameChange(e.target.value)}
                helperText="e.g., personalValues, kepribadian, custom-test"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                select
                fullWidth
                label="Test Type"
                value={testType}
                onChange={(e) => handleTestTypeChange(e.target.value)}
                SelectProps={{ native: false }}
              >
                <MenuItem value="top-n-dimension">top-n-dimension (Personal Values)</MenuItem>
                <MenuItem value="multiple-dimension">multiple-dimension (Personality)</MenuItem>
                <MenuItem value="custom">custom (Advanced JSON)</MenuItem>
              </TextField>
            </Grid>
          </Grid>
          </CardContent>
        </Card>

      <Card>
          <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Results</Typography>
            <Tabs value={tab} onChange={(_e, v) => setTab(v)}>
              <Tab label="Guided" value="guided" />
              <Tab label="JSON" value="json" />
            </Tabs>
            </Box>
          <Divider sx={{ my: 2 }} />

          {tab === 'guided' ? (
            testType === 'top-n-dimension' ? (
              renderPersonalValuesGuided()
            ) : testType === 'multiple-dimension' ? (
              renderPersonalityGuided()
            ) : (
              <Alert severity="info">Use the JSON tab to define a custom results structure.</Alert>
            )
          ) : (
            <Box>
              <Editor
                height="500px"
                defaultLanguage="json"
                value={jsonValue}
                onChange={(value) => setJsonValue(value || '')}
                options={{ 
                  minimap: { enabled: false },
                  wordWrap: 'on',
                  scrollBeyondLastLine: false
                }}
              />
              <Alert severity="info" sx={{ mt: 2 }}>
                This editor allows you to define the exact <b>results</b> object. Ensure it contains a top-level
                <code>dimensions</code> field. For <code>personalValues</code>, include <code>topN</code>. For
                <code>kepribadian</code>, include <code>overview</code> and Big Five dimensions with levels
                <code>rendah</code>, <code>sedang</code>, <code>tinggi</code>.
              </Alert>
              
              <Alert severity="info" sx={{ mt: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  HTML Formatting Support:
                </Typography>
                <Typography variant="body2" component="div">
                  You can use basic HTML tags for formatting inside string value:
                  <br />
                  • <code>&lt;b&gt;bold text&lt;/b&gt;</code> for <b>bold</b>
                  <br />
                  • <code>&lt;i&gt;italic text&lt;/i&gt;</code> for <i>italic</i>
                  <br />
                  • <code>&lt;ul&gt;&lt;li&gt;item&lt;/li&gt;&lt;/ul&gt;</code> for bullet lists
                  <br />
                  • <code>&lt;ol&gt;&lt;li&gt;item&lt;/li&gt;&lt;/ol&gt;</code> for numbered lists
                </Typography>
              </Alert>
                    </Box>
            )}
          </CardContent>
        </Card>
    </Box>
  );
};

export default InterpretationEditor;