import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

interface LoadingSpinnerProps {
  size?: number;
  message?: string;
  color?: 'primary' | 'secondary' | 'inherit';
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 40, 
  message = 'Loading...', 
  color = 'primary' 
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
        p: 3
      }}
    >
      <CircularProgress size={size} color={color} />
      {message && (
        <Typography variant="body2" color="textSecondary">
          {message}
        </Typography>
      )}
    </Box>
  );
};

export default LoadingSpinner;