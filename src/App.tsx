import { useEffect, useState } from 'react';
import { Bird, RefreshCw, AlertCircle } from 'lucide-react';

interface Visit {
  id: string;
  timestamp: string;
  species_raw: string;
  species_norm: string;
  summary: string;
  report_rel: string;
  image_rel: string;
  closest_guess: string;
  needs_review: boolean;
}

interface Metrics {
  total_visits: number;
  visits: Visit[];
  species_counts: Record<string, number>;
}

function App() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [imageErrors, setImageErrors] = useState<Set<string>>(new Set());

  const loadMetrics = async () => {
    try {
      const response = await fetch('/metrics.json');
      if (!response.ok) throw new Error('Failed to load metrics');
      const data = await response.json();
      setMetrics(data);
      setError(null);
      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetrics();
    const interval = setInterval(loadMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleImageError = (imageId: string) => {
    setImageErrors(prev => new Set(prev).add(imageId));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600">Loading bird data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 text-center mb-2">Error Loading Data</h2>
          <p className="text-gray-600 text-center mb-4">{error}</p>
          <button
            onClick={loadMetrics}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  const sortedSpecies = Object.entries(metrics.species_counts)
    .sort(([, a], [, b]) => b - a);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden mb-6">
          <div className="bg-gradient-to-r from-green-600 to-blue-600 px-6 py-8">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <Bird className="w-10 h-10 text-white" />
                  <h1 className="text-3xl font-bold text-white">Bird Visit Dashboard</h1>
                </div>
                <p className="text-green-100">Real-time backyard bird monitoring</p>
              </div>
              <div className="text-right">
                <div className="text-4xl font-bold text-white">{metrics.total_visits}</div>
                <div className="text-green-100 text-sm">Total Visits</div>
              </div>
            </div>
          </div>

          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>Last updated: {lastUpdate.toLocaleTimeString()}</span>
              <button
                onClick={loadMetrics}
                className="flex items-center gap-2 text-blue-600 hover:text-blue-700 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Species Counts</h2>
              <div className="space-y-3">
                {sortedSpecies.map(([species, count]) => (
                  <div key={species} className="flex items-center justify-between">
                    <span className="text-gray-700 capitalize">{species}</span>
                    <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-semibold">
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Visits</h2>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {metrics.visits.slice().reverse().map((visit) => {
                  const hasImageError = imageErrors.has(visit.id);
                  return (
                    <div
                      key={visit.id}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex gap-4">
                        <div className="flex-shrink-0 w-24 h-24 bg-gray-100 rounded-lg overflow-hidden">
                          {!hasImageError ? (
                            <img
                              src={`/${visit.image_rel}`}
                              alt={visit.species_norm}
                              className="w-full h-full object-cover"
                              onError={() => handleImageError(visit.id)}
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <Bird className="w-8 h-8 text-gray-400" />
                            </div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h3 className="text-lg font-semibold text-gray-900 capitalize">
                                {visit.species_norm}
                              </h3>
                              <p className="text-sm text-gray-500">{visit.timestamp}</p>
                            </div>
                          </div>
                          <p className="text-gray-700 text-sm mb-2 line-clamp-2">{visit.summary}</p>
                          <a
                            href={`/${visit.report_rel}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                          >
                            View Full Report
                          </a>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">All Visits</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Species
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Summary
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {metrics.visits.slice().reverse().map((visit) => (
                  <tr key={visit.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {visit.timestamp}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900 capitalize">
                        {visit.species_norm}
                      </span>
                      {visit.species_raw !== visit.species_norm && (
                        <span className="text-xs text-gray-500 block">
                          ({visit.species_raw})
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700 max-w-md truncate">
                      {visit.summary}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex gap-2">
                        <a
                          href={`/${visit.report_rel}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-700"
                        >
                          Report
                        </a>
                        <span className="text-gray-300">|</span>
                        <a
                          href={`/${visit.image_rel}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-700"
                        >
                          Photo
                        </a>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
