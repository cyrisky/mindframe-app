import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Chip,
  Avatar,
  LinearProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  ListItemSecondaryAction
} from '@mui/material';
import {
  Add,
  Description,
  Assessment,
  Schedule,
  TrendingUp,
  Download,
  Share,
  MoreVert,
  Refresh
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { templateService } from '../services/templateService';
import { reportService } from '../services/reportService';
import { Template } from '../types/template';
import { Report, ReportStatus } from '../types/report';

interface DashboardStats {
  totalTemplates: number;
  totalReports: number;
  reportsToday: number;
  processingReports: number;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats>({
    totalTemplates: 0,
    totalReports: 0,
    reportsToday: 0,
    processingReports: 0
  });
  const [recentTemplates, setRecentTemplates] = useState<Template[]>([]);
  const [recentReports, setRecentReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load dashboard data in parallel
      const [templatesResult, reportsResult, recentTemplatesData, recentReportsData] = await Promise.all([
        templateService.getTemplates({ limit: 1 }),
        reportService.getReports({ limit: 1 }),
        templateService.getRecentTemplates(5),
        reportService.getRecentReports(5)
      ]);

      console.log('Templates result:', templatesResult);
      console.log('Reports result:', reportsResult);
      console.log('Recent templates:', recentTemplatesData);
      console.log('Recent reports:', recentReportsData);

      // Get processing reports count
      const processingReportsResult = await reportService.getReportsByStatus(ReportStatus.PROCESSING);
      console.log('Processing reports:', processingReportsResult);
      
      // Get today's reports count
      const today = new Date().toISOString().split('T')[0];
      const todayReportsResult = await reportService.getReports({
        dateFrom: today,
        limit: 1000
      });
      console.log('Today reports:', todayReportsResult);

      setStats({
        totalTemplates: templatesResult?.total || 0,
        totalReports: reportsResult?.total || 0,
        reportsToday: todayReportsResult?.total || 0,
        processingReports: processingReportsResult?.length || 0
      });

      setRecentTemplates(recentTemplatesData || []);
      setRecentReports(recentReportsData || []);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: ReportStatus): string => {
    switch (status) {
      case ReportStatus.COMPLETED:
        return 'success';
      case ReportStatus.PROCESSING:
        return 'info';
      case ReportStatus.FAILED:
        return 'error';
      case ReportStatus.PENDING:
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const StatCard: React.FC<{
    title: string;
    value: number;
    icon: React.ReactNode;
    color: string;
    trend?: string;
  }> = ({ title, value, icon, color, trend }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
              {value.toLocaleString()}
            </Typography>
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingUp sx={{ fontSize: 16, color: 'success.main', mr: 0.5 }} />
                <Typography variant="body2" color="success.main">
                  {trend}
                </Typography>
              </Box>
            )}
          </Box>
          <Avatar sx={{ bgcolor: color, width: 56, height: 56 }}>
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <LinearProgress sx={{ mt: 2 }} />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold' }}>
          Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadDashboardData}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => navigate('/templates/new')}
          >
            New Template
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Templates"
            value={stats.totalTemplates}
            icon={<Description />}
            color="primary.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Reports"
            value={stats.totalReports}
            icon={<Assessment />}
            color="secondary.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Reports Today"
            value={stats.reportsToday}
            icon={<Schedule />}
            color="success.main"
            trend="+12% from yesterday"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Processing"
            value={stats.processingReports}
            icon={<TrendingUp />}
            color="warning.main"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Recent Templates */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" component="h2">
                  Recent Templates
                </Typography>
                <Button
                  size="small"
                  onClick={() => navigate('/templates')}
                >
                  View All
                </Button>
              </Box>
              <Divider sx={{ mb: 2 }} />
              {recentTemplates.length > 0 ? (
                <List disablePadding>
                  {recentTemplates.map((template, index) => (
                    <ListItem
                      key={template.id}
                      divider={index < recentTemplates.length - 1}
                      sx={{ px: 0 }}
                    >
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'primary.main' }}>
                          <Description />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={template.name}
                        secondary={
                          <Box>
                            <Typography variant="body2" color="textSecondary">
                              {template.category} • {formatDate(template.updatedAt)}
                            </Typography>
                            <Box sx={{ mt: 0.5 }}>
                              {template.tags.slice(0, 2).map(tag => (
                                <Chip
                                  key={tag}
                                  label={tag}
                                  size="small"
                                  sx={{ mr: 0.5, fontSize: '0.7rem' }}
                                />
                              ))}
                            </Box>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          onClick={() => navigate(`/templates/${template.id}`)}
                        >
                          <MoreVert />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography color="textSecondary" sx={{ textAlign: 'center', py: 3 }}>
                  No templates yet. Create your first template to get started.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Reports */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" component="h2">
                  Recent Reports
                </Typography>
                <Button
                  size="small"
                  onClick={() => navigate('/reports')}
                >
                  View All
                </Button>
              </Box>
              <Divider sx={{ mb: 2 }} />
              {recentReports.length > 0 ? (
                <List disablePadding>
                  {recentReports.map((report, index) => (
                    <ListItem
                      key={report.id}
                      divider={index < recentReports.length - 1}
                      sx={{ px: 0 }}
                    >
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'secondary.main' }}>
                          <Assessment />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={report.name}
                        secondary={
                          <Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                              <Chip
                                label={report.status}
                                size="small"
                                color={getStatusColor(report.status) as any}
                                sx={{ fontSize: '0.7rem' }}
                              />
                              <Typography variant="body2" color="textSecondary">
                                {formatDate(report.updatedAt)}
                              </Typography>
                            </Box>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          {report.status === ReportStatus.COMPLETED && (
                            <>
                              <IconButton
                                size="small"
                                onClick={() => reportService.downloadReport(report.id)}
                              >
                                <Download fontSize="small" />
                              </IconButton>
                              <IconButton
                                size="small"
                                onClick={() => navigate(`/reports/${report.id}/share`)}
                              >
                                <Share fontSize="small" />
                              </IconButton>
                            </>
                          )}
                          <IconButton
                            size="small"
                            onClick={() => navigate(`/reports/${report.id}`)}
                          >
                            <MoreVert fontSize="small" />
                          </IconButton>
                        </Box>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography color="textSecondary" sx={{ textAlign: 'center', py: 3 }}>
                  No reports yet. Generate your first report from a template.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;