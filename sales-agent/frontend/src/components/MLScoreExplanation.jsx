import React from 'react';

export default function MLScoreExplanation({ lead }) {
    const { ml_score, ml_confidence, score_explanation } = lead;

    const getScoreColor = (score) => {
        if (score >= 0.7) return 'text-green-600';
        if (score >= 0.4) return 'text-yellow-600';
        return 'text-red-600';
    };

    const getImpactColor = (impact) => {
        if (impact > 0) return 'text-green-600';
        if (impact < 0) return 'text-red-600';
        return 'text-gray-600';
    };

    return (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
            {/* Score Header */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h4 className="text-lg font-bold mb-1">ML Lead Score</h4>
                    <p className="text-sm text-gray-600">
                        Powered by XGBoost + SHAP
                    </p>
                </div>
                <div className="text-right">
                    <div className={`text-4xl font-bold ${getScoreColor(ml_score)}`}>
                        {(ml_score * 100).toFixed(0)}
                    </div>
                    <div className="text-sm text-gray-500">
                        {(ml_confidence * 100).toFixed(0)}% confident
                    </div>
                </div>
            </div>

            {/* Confidence Bar */}
            <div className="mb-6">
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>Confidence Level</span>
                    <span>{(ml_confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                        className="bg-blue-600 h-2 rounded-full transition-all"
                        style={{ width: `${ml_confidence * 100}%` }}
                    />
                </div>
            </div>

            {/* Top Factors */}
            <div>
                <h5 className="font-semibold mb-3">Top Contributing Factors</h5>
                <div className="space-y-3">
                    {score_explanation?.map((factor, i) => (
                        <div key={i} className="flex items-center justify-between">
                            <div className="flex-1">
                                <div className="font-medium text-sm">{factor.name}</div>
                                <div className="text-xs text-gray-500">
                                    Value: {factor.value.toFixed(2)}
                                </div>
                            </div>
                            <div className={`font-mono text-sm ${getImpactColor(factor.impact)}`}>
                                {factor.impact > 0 ? '+' : ''}{factor.impact.toFixed(3)}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Warning for low confidence */}
            {ml_confidence < 0.7 && (
                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                    <p className="text-sm text-yellow-800">
                        ⚠️ Low confidence score - consider manual review to improve model
                    </p>
                </div>
            )}
        </div>
    );
}
