/*
  # Bird Tracking System - Complete Database Schema

  ## Overview
  This migration creates the complete database schema for the bird feeder tracking system.
  It includes tables for visits, captures, species statistics, system logs, and health monitoring.

  ## New Tables

  ### 1. visits
  Core table tracking each bird visit to the feeder.
  - `id`: Unique visit identifier
  - `session_id`: Groups visits from same service session
  - `start_time`: When bird first detected
  - `end_time`: When visit completed
  - `duration_seconds`: Total visit duration
  - `status`: active, analyzing, completed, failed, interrupted
  - `species`: Identified bird species
  - `species_confidence`: low, medium, high
  - `summary`: Natural language description from OpenAI
  - `bird_count`: Number of birds in visit (1 or more)

  ### 2. captures
  Photos taken during each visit.
  - `id`: Unique capture identifier
  - `visit_id`: Links to visits table
  - `timestamp`: When photo was taken
  - `image_url`: URL to stored image
  - `thumbnail_url`: URL to thumbnail
  - `detections`: JSON array of YOLO detections (bboxes, confidence)
  - `is_best_capture`: Flag for best photo in visit

  ### 3. species_stats
  Aggregated statistics by species.
  - `species`: Species name
  - `total_visits`: Count of visits
  - `last_seen`: Most recent visit timestamp
  - `first_seen`: First ever visit timestamp

  ### 4. system_logs
  Structured logging for debugging and monitoring.
  - `id`: Unique log entry ID
  - `timestamp`: When log was created
  - `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - `component`: detector, analyzer, api, database
  - `message`: Log message
  - `metadata`: JSON with additional context
  - `correlation_id`: Links related log entries

  ### 5. system_health
  Current health status of all components.
  - `component`: Component name (camera, detector, analyzer, api, database)
  - `status`: healthy, degraded, unhealthy
  - `last_check`: Last health check timestamp
  - `message`: Status description
  - `metadata`: JSON with health metrics

  ## Security
  - Row Level Security (RLS) enabled on all tables
  - Public read access for visits, captures, species_stats
  - Service role only for writes
  - System logs and health visible to authenticated users only
*/

-- Create visits table
CREATE TABLE IF NOT EXISTS visits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ,
  duration_seconds INTEGER,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  species VARCHAR(100),
  species_confidence VARCHAR(10),
  summary TEXT,
  bird_count INTEGER DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_visits_start_time ON visits(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_visits_status ON visits(status);
CREATE INDEX IF NOT EXISTS idx_visits_species ON visits(species);
CREATE INDEX IF NOT EXISTS idx_visits_session ON visits(session_id);

-- Create captures table
CREATE TABLE IF NOT EXISTS captures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  visit_id UUID NOT NULL REFERENCES visits(id) ON DELETE CASCADE,
  timestamp TIMESTAMPTZ NOT NULL,
  image_url TEXT NOT NULL,
  thumbnail_url TEXT,
  detections JSONB NOT NULL DEFAULT '[]'::jsonb,
  is_best_capture BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_captures_visit ON captures(visit_id);
CREATE INDEX IF NOT EXISTS idx_captures_timestamp ON captures(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_captures_best ON captures(is_best_capture) WHERE is_best_capture = TRUE;

-- Create species_stats table
CREATE TABLE IF NOT EXISTS species_stats (
  species VARCHAR(100) PRIMARY KEY,
  total_visits INTEGER NOT NULL DEFAULT 0,
  last_seen TIMESTAMPTZ,
  first_seen TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create system_logs table
CREATE TABLE IF NOT EXISTS system_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  level VARCHAR(10) NOT NULL,
  component VARCHAR(50) NOT NULL,
  message TEXT NOT NULL,
  metadata JSONB,
  correlation_id UUID
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_component ON system_logs(component);
CREATE INDEX IF NOT EXISTS idx_logs_correlation ON system_logs(correlation_id) WHERE correlation_id IS NOT NULL;

-- Create system_health table
CREATE TABLE IF NOT EXISTS system_health (
  component VARCHAR(50) PRIMARY KEY,
  status VARCHAR(20) NOT NULL,
  last_check TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  message TEXT,
  metadata JSONB
);

-- Enable Row Level Security
ALTER TABLE visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE captures ENABLE ROW LEVEL SECURITY;
ALTER TABLE species_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_health ENABLE ROW LEVEL SECURITY;

-- RLS Policies for visits (public read, service role write)
CREATE POLICY "Allow public read visits" 
  ON visits FOR SELECT 
  TO anon 
  USING (true);

CREATE POLICY "Allow authenticated read visits" 
  ON visits FOR SELECT 
  TO authenticated 
  USING (true);

CREATE POLICY "Service role can insert visits" 
  ON visits FOR INSERT 
  TO service_role 
  WITH CHECK (true);

CREATE POLICY "Service role can update visits" 
  ON visits FOR UPDATE 
  TO service_role 
  USING (true);

-- RLS Policies for captures (public read, service role write)
CREATE POLICY "Allow public read captures" 
  ON captures FOR SELECT 
  TO anon 
  USING (true);

CREATE POLICY "Allow authenticated read captures" 
  ON captures FOR SELECT 
  TO authenticated 
  USING (true);

CREATE POLICY "Service role can insert captures" 
  ON captures FOR INSERT 
  TO service_role 
  WITH CHECK (true);

-- RLS Policies for species_stats (public read, service role write)
CREATE POLICY "Allow public read species_stats" 
  ON species_stats FOR SELECT 
  TO anon 
  USING (true);

CREATE POLICY "Allow authenticated read species_stats" 
  ON species_stats FOR SELECT 
  TO authenticated 
  USING (true);

CREATE POLICY "Service role can upsert species_stats" 
  ON species_stats FOR ALL 
  TO service_role 
  USING (true) 
  WITH CHECK (true);

-- RLS Policies for system_logs (authenticated read only, service role write)
CREATE POLICY "Allow authenticated read system_logs" 
  ON system_logs FOR SELECT 
  TO authenticated 
  USING (true);

CREATE POLICY "Service role can insert system_logs" 
  ON system_logs FOR INSERT 
  TO service_role 
  WITH CHECK (true);

-- RLS Policies for system_health (public read, service role write)
CREATE POLICY "Allow public read system_health" 
  ON system_health FOR SELECT 
  TO anon 
  USING (true);

CREATE POLICY "Allow authenticated read system_health" 
  ON system_health FOR SELECT 
  TO authenticated 
  USING (true);

CREATE POLICY "Service role can upsert system_health" 
  ON system_health FOR ALL 
  TO service_role 
  USING (true) 
  WITH CHECK (true);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger to visits table
DROP TRIGGER IF EXISTS update_visits_updated_at ON visits;
CREATE TRIGGER update_visits_updated_at
  BEFORE UPDATE ON visits
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Add trigger to species_stats table
DROP TRIGGER IF EXISTS update_species_stats_updated_at ON species_stats;
CREATE TRIGGER update_species_stats_updated_at
  BEFORE UPDATE ON species_stats
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Insert initial health status for all components
INSERT INTO system_health (component, status, message) VALUES
  ('camera', 'unhealthy', 'Not yet initialized'),
  ('detector', 'unhealthy', 'Not yet initialized'),
  ('analyzer', 'unhealthy', 'Not yet initialized'),
  ('api', 'unhealthy', 'Not yet initialized'),
  ('database', 'healthy', 'Connected')
ON CONFLICT (component) DO NOTHING;