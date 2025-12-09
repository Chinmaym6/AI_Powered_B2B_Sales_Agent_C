import React from 'react';

export default function MLScoreExplanation({ lead }) {
    const { ml_score, ml_confidence, score_explanation } = lead;

    // Factor descriptions and interpretations
    const factorDetails = {
        'Keyword Match': {
            icon: '🔑',
            description: 'How well the company description matches your product keywords',
            interpret: (value) => value >= 0.5 ? 'Strong keyword alignment' : value > 0 ? 'Some keywords found' : 'No matching keywords detected'
        },
        'Industry Fit': {
            icon: '🏢',
            description: 'Whether the company operates in your target industry',
            interpret: (value) => value >= 1 ? 'Perfect industry match' : value > 0 ? 'Related industry' : 'Different industry'
        },
        'Contact Info': {
            icon: '📧',
            description: 'Availability of contact details (email, decision maker, title, LinkedIn)',
            interpret: (value) => value >= 0.75 ? 'Complete contact info' : value >= 0.5 ? 'Partial contact info' : value > 0 ? 'Limited contact info' : 'No contact info found'
        },
        'Email Found': {
            icon: '✉️',
            description: 'Whether a valid email address was found',
            interpret: (value) => value >= 1 ? 'Email address available' : 'No email found'
        },
        'Pain Point Match': {
            icon: '🎯',
            description: 'How many of your product\'s pain points match the company',
            interpret: (value) => value >= 0.5 ? 'Multiple pain points match' : value > 0 ? 'Some pain points align' : 'No pain point signals detected'
        },
        'Tech Stack Match': {
            icon: '💻',
            description: 'Number of relevant tech keywords found (API, cloud, SaaS, AI, etc.)',
            interpret: (value) => value >= 4 ? 'Tech-savvy company' : value >= 2 ? 'Uses modern tech' : value > 0 ? 'Some tech signals' : 'No tech indicators found'
        },
        'Description Quality': {
            icon: '📝',
            description: 'Amount of information available about the company',
            interpret: (value) => value >= 5 ? 'Rich company data' : value >= 3 ? 'Good amount of info' : value > 0 ? 'Basic info only' : 'Very limited data'
        },
        'Company Size': {
            icon: '👥',
            description: 'Estimated company employee count',
            interpret: (value) => value >= 5 ? 'Enterprise company' : value >= 3 ? 'Mid-size company' : value > 0 ? 'Small company' : 'Size unknown'
        },
        'LinkedIn Profile': {
            icon: '💼',
            description: 'Whether a LinkedIn company profile was found',
            interpret: (value) => value >= 1 ? 'LinkedIn profile found' : 'No LinkedIn profile'
        },
        'Secure Website': {
            icon: '🔒',
            description: 'Whether the website uses HTTPS (security indicator)',
            interpret: (value) => value >= 1 ? 'Secure website (HTTPS)' : 'Non-secure website'
        },
        'Funding History': {
            icon: '💰',
            description: 'Mentions of funding rounds (Series A, B, Seed, etc.)',
            interpret: (value) => value >= 1 ? 'Funding signals found' : 'No funding mentions'
        }
    };

    const getScoreColor = (score) => {
        if (score >= 0.7) return 'text-green-500';
        if (score >= 0.4) return 'text-yellow-500';
        return 'text-red-500';
    };

    const getScoreBgColor = (score) => {
        if (score >= 0.7) return 'bg-green-500';
        if (score >= 0.4) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    const getImpactColor = (impact) => {
        if (impact > 0.5) return 'text-green-400';
        if (impact > 0) return 'text-green-500';
        if (impact < -0.5) return 'text-red-400';
        if (impact < 0) return 'text-red-500';
        return 'text-gray-400';
    };

    const getImpactBg = (impact) => {
        if (impact > 0) return 'bg-green-500/20';
        if (impact < 0) return 'bg-red-500/20';
        return 'bg-gray-500/20';
    };

    const getScoreLabel = (score) => {
        if (score >= 0.8) return { label: 'HOT LEAD 🔥', color: 'text-green-400' };
        if (score >= 0.6) return { label: 'WARM LEAD 🌡️', color: 'text-yellow-400' };
        if (score >= 0.4) return { label: 'COOL LEAD ❄️', color: 'text-blue-400' };
        return { label: 'COLD LEAD', color: 'text-gray-400' };
    };

    const scoreLabel = getScoreLabel(ml_score);

    return (
        <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-white/10 rounded-xl p-6">
            {/* Score Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h4 className="text-lg font-bold text-white mb-1">ML Lead Score</h4>
                    <p className="text-sm text-white/50">
                        Powered by XGBoost + SHAP Explainability
                    </p>
                </div>
                <div className="text-right">
                    <div className={`text-5xl font-bold ${getScoreColor(ml_score)}`}>
                        {(ml_score * 100).toFixed(0)}
                    </div>
                    <div className={`text-sm font-semibold ${scoreLabel.color}`}>
                        {scoreLabel.label}
                    </div>
                </div>
            </div>

            {/* Confidence Bar */}
            <div className="mb-6 p-4 bg-white/5 rounded-lg">
                <div className="flex justify-between text-sm text-white/70 mb-2">
                    <span>Model Confidence</span>
                    <span className="font-semibold">{(ml_confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                    <div
                        className={`h-2 rounded-full transition-all ${getScoreBgColor(ml_confidence)}`}
                        style={{ width: `${ml_confidence * 100}%` }}
                    />
                </div>
                <p className="text-xs text-white/40 mt-2">
                    {ml_confidence >= 0.8 ? '✅ High confidence - prediction is reliable' :
                        ml_confidence >= 0.5 ? '⚠️ Moderate confidence - review recommended' :
                            '❌ Low confidence - limited data available'}
                </p>
            </div>

            {/* Top Factors */}
            <div>
                <h5 className="font-semibold text-white mb-4 flex items-center gap-2">
                    <span>📊</span> Why This Score?
                </h5>
                <div className="space-y-3">
                    {score_explanation?.map((factor, i) => {
                        const details = factorDetails[factor.name] || {
                            icon: '📌',
                            description: 'Scoring factor',
                            interpret: () => 'Value: ' + factor.value.toFixed(2)
                        };
                        const isPositive = factor.impact > 0;

                        return (
                            <div
                                key={i}
                                className={`p-3 rounded-lg border ${isPositive ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'}`}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-lg">{details.icon}</span>
                                            <span className="font-medium text-white">{factor.name}</span>
                                        </div>
                                        <p className="text-xs text-white/50 mb-2">
                                            {details.description}
                                        </p>
                                        <p className={`text-sm font-medium ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                                            → {details.interpret(factor.value)}
                                        </p>
                                    </div>
                                    <div className="text-right ml-4">
                                        <div className={`text-lg font-bold ${getImpactColor(factor.impact)}`}>
                                            {factor.impact > 0 ? '+' : ''}{(factor.impact * 100).toFixed(0)}%
                                        </div>
                                        <div className="text-xs text-white/40">
                                            impact
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Summary */}
            <div className="mt-6 p-4 bg-white/5 rounded-lg border border-white/10">
                <p className="text-sm text-white/60">
                    <span className="font-semibold text-white">💡 Summary:</span>{' '}
                    This lead scored <span className={getScoreColor(ml_score)}>{(ml_score * 100).toFixed(0)}%</span> based
                    on {score_explanation?.filter(f => f.impact > 0).length || 0} positive factors
                    and {score_explanation?.filter(f => f.impact < 0).length || 0} negative factors
                    from {score_explanation?.length || 0} analyzed metrics.
                </p>
            </div>

            {/* Warning for low confidence */}
            {ml_confidence < 0.5 && (
                <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                    <p className="text-sm text-yellow-400">
                        ⚠️ Low confidence score - the model had limited data to work with.
                        Consider manually verifying this lead.
                    </p>
                </div>
            )}
        </div>
    );
}

