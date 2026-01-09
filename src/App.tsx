import { useEffect, useState } from 'react';
import { createClient } from '@supabase/supabase-js';
import { Bird, RefreshCw, AlertCircle, Activity, Camera, Database, Wifi, Clock } from 'lucide-react';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

interface Visit {
  id: string;
  session_id: string;
  start_time: string;
  end_time: string | null;
  duration_seconds: number | null;
  status: string;
  species: string | null;
  species_confidence: string | null;
  summary: string | null;
  bird_count: number;
  created_at: string;
  updated_at: string;
}

interface Capture {
  id: string;
  visit_id: string;
  timestamp: string;
  image_url: string;
  thumbnail_url: string | null;
  detections: any[];
  is_best_capture: boolean;
}

interface SpeciesStats {
  species: string;
  total_visits: number;
  last_seen: string;
  first_seen: string;
}

interface HealthStatus {
  component: string;
  status: string;
  last_check: string;
  message: string;
  metadata: any;
}

function App() {
  const [visits, setVisits] = useState<Visit[]>([]);
  const [speciesStats, setSpeciesStats] = useState<SpeciesStats[]>([]);
  const [healthStatus, setHealthStatus] = useState<Record<string, HealthStatus>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVisit, setSelectedVisit] = useState<Visit | null>(null);
  const [visitCaptures, setVisitCaptures] = useState<Capture[]>([]);
  const [todayStats, setTodayStats] = useState({ total_visits: 0, unique_species: 0 });

  const loadData = async () => {
    try {
      const [visitsRes, speciesRes, healthRes] = await Promise.all([
        supabase.from('visits').select('*').order('start_time', { ascending: false }).limit(20),
        supabase.from('species_stats').select('*').order('total_visits', { ascending: false }).limit(10),
        supabase.from('system_health').select('*')
      ]);

      if (visitsRes.error) throw visitsRes.error;
      if (speciesRes.error) throw speciesRes.error;
      if (healthRes.error) throw healthRes.error;

      setVisits(visitsRes.data || []);
      setSpeciesStats(speciesRes.data || []);

      const healthMap: Record<string, HealthStatus> = {};
      healthRes.data?.forEach((h: HealthStatus) => {
        healthMap[h.component] = h;
      });
      setHealthStatus(healthMap);

      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const todayVisits = (visitsRes.data || []).filter(
        (v: Visit) => new Date(v.start_time) >= today
      );
      const uniqueSpecies = new Set(
        todayVisits.filter((v: Visit) => v.species && v.species !== 'unknown').map((v: Visit) => v.species)
      );
      setTodayStats({
        total_visits: todayVisits.length,
        unique_species: uniqueSpecies.size
      });

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadVisitCaptures = async (visitId: string) => {
    try {
      const { data, error } = await supabase
        .from('captures')
        .select('*')
        .eq('visit_id', visitId)
        .order('timestamp');

      if (error) throw error;
      setVisitCaptures(data || []);
    } catch (err) {
      console.error('Failed to load captures:', err);
    }
  };

  useEffect(() => {
    loadData();

    const visitsSubscription = supabase
      .channel('visits_channel')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'visits' }, () => {
        loadData();
      })
      .subscribe();

    const statsSubscription = supabase
      .channel('stats_channel')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'species_stats' }, () => {
        loadData();
      })
      .subscribe();

    const healthSubscription = supabase
      .channel('health_channel')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'system_health' }, () => {
        loadData();
      })
      .subscribe();

    const interval = setInterval(loadData, 30000);

    return () => {
      visitsSubscription.unsubscribe();
      statsSubscription.unsubscribe();
      healthSubscription.unsubscribe();
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    if (selectedVisit) {
      loadVisitCaptures(selectedVisit.id);
    }
  }, [selectedVisit]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return 'text-green-600 bg-green-100';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100';
      case 'unhealthy':
      case 'disconnected':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-700 text-lg">Loading Bird Tracker...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-semibold text-gray-900 text-center mb-2">Connection Error</h2>
          <p className="text-gray-600 text-center mb-6">{error}</p>
          <button
            onClick={loadData}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-xl shadow-xl overflow-hidden mb-8">
          <div className="bg-gradient-to-r from-blue-600 to-green-600 px-8 py-10">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <div className="flex items-center gap-4 mb-3">
                  <Bird className="w-12 h-12 text-white" />
                  <h1 className="text-4xl font-bold text-white">Bird Feeder Tracker</h1>
                </div>
                <p className="text-blue-100 text-lg">Real-time AI-powered bird monitoring system</p>
              </div>
              <button
                onClick={loadData}
                className="flex items-center gap-2 bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg transition-all"
              >
                <RefreshCw className="w-5 h-5" />
                Refresh
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-gray-200">
            <div className="bg-white px-6 py-5">
              <div className="text-3xl font-bold text-gray-900">{todayStats.total_visits}</div>
              <div className="text-sm text-gray-600 mt-1">Visits Today</div>
            </div>
            <div className="bg-white px-6 py-5">
              <div className="text-3xl font-bold text-gray-900">{todayStats.unique_species}</div>
              <div className="text-sm text-gray-600 mt-1">Species Today</div>
            </div>
            <div className="bg-white px-6 py-5">
              <div className="text-3xl font-bold text-gray-900">{visits.length}</div>
              <div className="text-sm text-gray-600 mt-1">Recent Visits</div>
            </div>
            <div className="bg-white px-6 py-5">
              <div className="text-3xl font-bold text-gray-900">{speciesStats.length}</div>
              <div className="text-sm text-gray-600 mt-1">Total Species</div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {Object.entries({
            camera: { icon: Camera, label: 'Camera' },
            detector: { icon: Activity, label: 'Detector' },
            analyzer: { icon: Bird, label: 'Analyzer' },
            database: { icon: Database, label: 'Database' }
          }).map(([key, { icon: Icon, label }]) => {
            const health = healthStatus[key];
            return (
              <div key={key} className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Icon className="w-5 h-5 text-gray-600" />
                    <span className="font-medium text-gray-900">{label}</span>
                  </div>
                  {health && (
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(health.status)}`}>
                      {health.status}
                    </span>
                  )}
                </div>
                {health && (
                  <p className="text-sm text-gray-600">{health.message}</p>
                )}
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Bird className="w-5 h-5 text-blue-600" />
                Species Leaderboard
              </h2>
              <div className="space-y-3">
                {speciesStats.length > 0 ? (
                  speciesStats.map((stat, index) => (
                    <div key={stat.species} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-sm">
                          {index + 1}
                        </div>
                        <span className="text-gray-800 font-medium capitalize">{stat.species}</span>
                      </div>
                      <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-semibold">
                        {stat.total_visits}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center py-4">No species detected yet</p>
                )}
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-green-600" />
                Recent Visits
              </h2>
              <div className="space-y-4 max-h-[500px] overflow-y-auto">
                {visits.length > 0 ? (
                  visits.map((visit) => (
                    <div
                      key={visit.id}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer"
                      onClick={() => setSelectedVisit(visit)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 capitalize">
                            {visit.species || 'Analyzing...'}
                          </h3>
                          <p className="text-sm text-gray-500">{formatTime(visit.start_time)}</p>
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            visit.status === 'completed' ? 'bg-green-100 text-green-800' :
                            visit.status === 'analyzing' ? 'bg-yellow-100 text-yellow-800' :
                            visit.status === 'active' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {visit.status}
                          </span>
                          {visit.species_confidence && (
                            <span className="text-xs text-gray-500">{visit.species_confidence} confidence</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <span>Duration: {formatDuration(visit.duration_seconds)}</span>
                        <span>Birds: {visit.bird_count}</span>
                      </div>
                      {visit.summary && (
                        <p className="text-gray-700 text-sm mt-2 line-clamp-2">{visit.summary}</p>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12">
                    <Bird className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500 text-lg">No visits yet</p>
                    <p className="text-gray-400 text-sm">Birds will appear here when detected</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {selectedVisit && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedVisit(null)}>
            <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-2xl font-bold text-gray-900 capitalize">
                  {selectedVisit.species || 'Analyzing...'}
                </h2>
                <p className="text-gray-600 mt-1">{formatTime(selectedVisit.start_time)}</p>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div>
                    <span className="text-sm text-gray-600">Duration:</span>
                    <div className="text-lg font-semibold">{formatDuration(selectedVisit.duration_seconds)}</div>
                  </div>
                  <div>
                    <span className="text-sm text-gray-600">Bird Count:</span>
                    <div className="text-lg font-semibold">{selectedVisit.bird_count}</div>
                  </div>
                  <div>
                    <span className="text-sm text-gray-600">Status:</span>
                    <div className="text-lg font-semibold capitalize">{selectedVisit.status}</div>
                  </div>
                  <div>
                    <span className="text-sm text-gray-600">Confidence:</span>
                    <div className="text-lg font-semibold capitalize">{selectedVisit.species_confidence || 'N/A'}</div>
                  </div>
                </div>
                {selectedVisit.summary && (
                  <div className="mb-6">
                    <h3 className="text-sm font-medium text-gray-600 mb-2">AI Analysis Summary:</h3>
                    <p className="text-gray-800 bg-gray-50 p-4 rounded-lg">{selectedVisit.summary}</p>
                  </div>
                )}
                {visitCaptures.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Captured Photos ({visitCaptures.length})</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {visitCaptures.map((capture) => (
                        <div key={capture.id} className="relative group">
                          <img
                            src={capture.image_url}
                            alt="Bird capture"
                            className="w-full h-48 object-cover rounded-lg"
                          />
                          {capture.is_best_capture && (
                            <div className="absolute top-2 right-2 bg-yellow-500 text-white px-2 py-1 rounded text-xs font-semibold">
                              Best
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <div className="p-6 border-t border-gray-200 flex justify-end">
                <button
                  onClick={() => setSelectedVisit(null)}
                  className="px-6 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
