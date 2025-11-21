import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function CampaignForm() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        name: '',
        product_description: '',
        target_industry: '',
        company_size: 'All',
        target_regions: []
    });
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            // Use full URL if proxy not set up yet, or relative if proxy exists
            // Assuming proxy will be set up to forward /api to localhost:8000
            const response = await fetch('http://localhost:8000/api/campaigns/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (!response.ok) throw new Error('Failed to create campaign');

            const campaign = await response.json();
            navigate(`/campaign/${campaign.id}`);
        } catch (error) {
            console.error(error);
            alert('Error creating campaign');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-3xl mx-auto p-8">
            <div className="bg-white rounded-lg shadow-lg p-8">
                <h1 className="text-3xl font-bold mb-2">Create Sales Campaign</h1>
                <p className="text-gray-600 mb-8">
                    Our AI agent will autonomously find and reach out to your ideal customers
                </p>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Campaign Name */}
                    <div>
                        <label className="block text-sm font-semibold mb-2">
                            Campaign Name
                        </label>
                        <input
                            type="text"
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Q1 2024 Outreach"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            required
                        />
                    </div>

                    {/* Product Description */}
                    <div>
                        <label className="block text-sm font-semibold mb-2">
                            Product Description
                        </label>
                        <textarea
                            className="w-full p-3 border border-gray-300 rounded-lg h-32 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Describe your product: what it does, who it helps, key benefits..."
                            value={formData.product_description}
                            onChange={(e) => setFormData({ ...formData, product_description: e.target.value })}
                            required
                        />
                        <p className="text-sm text-gray-500 mt-1">
                            Be specific - this helps our AI find the right leads
                        </p>
                    </div>

                    {/* Target Industry */}
                    <div>
                        <label className="block text-sm font-semibold mb-2">
                            Target Industry (Optional)
                        </label>
                        <input
                            type="text"
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="e.g., SaaS, E-commerce, Healthcare"
                            value={formData.target_industry}
                            onChange={(e) => setFormData({ ...formData, target_industry: e.target.value })}
                        />
                    </div>

                    {/* Company Size */}
                    <div>
                        <label className="block text-sm font-semibold mb-2">
                            Company Size Preference
                        </label>
                        <select
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            value={formData.company_size}
                            onChange={(e) => setFormData({ ...formData, company_size: e.target.value })}
                        >
                            <option>All</option>
                            <option>Startup (1-50)</option>
                            <option>SMB (51-500)</option>
                            <option>Enterprise (500+)</option>
                        </select>
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-blue-600 text-white py-4 rounded-lg font-semibold hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                        {loading ? (
                            <span className="flex items-center justify-center">
                                <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                </svg>
                                Creating Campaign...
                            </span>
                        ) : (
                            '🚀 Start Autonomous Campaign'
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}
