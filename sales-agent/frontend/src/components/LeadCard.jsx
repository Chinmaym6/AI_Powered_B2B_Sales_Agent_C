import React, { useState } from 'react';
import MLScoreExplanation from './MLScoreExplanation';

export default function LeadCard({ lead }) {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className="bg-white rounded-lg shadow p-6 transition hover:shadow-md">
            <div className="flex justify-between items-start">
                <div>
                    <h3 className="text-xl font-bold text-gray-900">{lead.company_name}</h3>
                    <p className="text-gray-600">{lead.industry} • {lead.location || 'Unknown Location'}</p>
                    <a
                        href={lead.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline text-sm mt-1 block"
                    >
                        {lead.website}
                    </a>
                </div>
                <div className="text-right">
                    <div className="text-2xl font-bold text-blue-600">
                        {(lead.ml_score * 100).toFixed(0)}
                    </div>
                    <div className="text-xs text-gray-500">Score</div>
                </div>
            </div>

            <div className="mt-4">
                <p className="text-gray-700 line-clamp-2">{lead.description}</p>
            </div>

            <div className="mt-4 flex items-center justify-between">
                <div className="flex space-x-4 text-sm text-gray-500">
                    {lead.email && (
                        <span className="flex items-center">
                            ✉️ {lead.email}
                        </span>
                    )}
                    {lead.linkedin_url && (
                        <a href={lead.linkedin_url} target="_blank" rel="noopener noreferrer" className="flex items-center hover:text-blue-600">
                            🔗 LinkedIn
                        </a>
                    )}
                </div>

                <button
                    onClick={() => setExpanded(!expanded)}
                    className="text-blue-600 text-sm font-semibold hover:text-blue-800"
                >
                    {expanded ? 'Hide Analysis' : 'View Analysis'}
                </button>
            </div>

            {expanded && (
                <div className="mt-6 border-t pt-4">
                    <MLScoreExplanation lead={lead} />
                </div>
            )}
        </div>
    );
}
