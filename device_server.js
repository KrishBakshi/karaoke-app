const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = 3001;

// Enable CORS for frontend
app.use(cors());

// Parse JSON bodies
app.use(express.json());

// API endpoint to get audio devices
app.get('/api/devices', async (req, res) => {
  try {
    console.log('🎤 API request: Getting audio devices...');
    
    // Path to the Python script
    const scriptPath = path.join(__dirname, 'autotune-app', 'get_devices_json.py');
    
    // Run the Python script
    const pythonProcess = spawn('python3', [scriptPath, '--json']);
    
    let output = '';
    let errorOutput = '';
    
    // Collect stdout
    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    // Collect stderr
    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    // Handle process completion
    pythonProcess.on('close', (code) => {
      if (code === 0) {
        try {
          // Parse the JSON output
          const devices = JSON.parse(output);
          console.log('✅ Successfully retrieved devices:', {
            inputs: devices.inputs.length,
            outputs: devices.outputs.length
          });
          res.json(devices);
        } catch (parseError) {
          console.error('❌ Failed to parse JSON output:', parseError);
          console.error('Raw output:', output);
          res.status(500).json({ 
            error: 'Failed to parse device data',
            details: parseError.message 
          });
        }
      } else {
        console.error('❌ Python script failed with code:', code);
        console.error('Error output:', errorOutput);
        res.status(500).json({ 
          error: 'Failed to get devices',
          details: `Python script exited with code ${code}`,
          stderr: errorOutput
        });
      }
    });
    
    // Handle process errors
    pythonProcess.on('error', (error) => {
      console.error('❌ Failed to start Python process:', error);
      res.status(500).json({ 
        error: 'Failed to start device discovery',
        details: error.message 
      });
    });
    
  } catch (error) {
    console.error('❌ API error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      details: error.message 
    });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Start the server
app.listen(PORT, () => {
  console.log(`🎵 Device discovery server running on http://localhost:${PORT}`);
  console.log(`🎤 API endpoint: http://localhost:${PORT}/api/devices`);
  console.log(`💚 Health check: http://localhost:${PORT}/health`);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down device discovery server...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Shutting down device discovery server...');
  process.exit(0);
});
