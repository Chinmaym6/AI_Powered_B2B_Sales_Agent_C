import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, BarChart2, Calendar } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Campaign {
    id: string;
    name: string;
    status: string;
    created_at: string;
    leads_count: number;
}

export default function AllCampaignsPage() {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
        fetchCampaigns();
    }, []);

    const fetchCampaigns = async () => {
        try {
            const response = await fetch('http://127.0.0.1:8000/api/campaigns/');
            if (response.ok) {
                const data = await response.json();
                setCampaigns(data);
            }
        } catch (error) {
            console.error('Error fetching campaigns:', error);
        }
    };

    return (
        <div className="min-h-screen bg-[#030303] text-white p-8">
            <div className="max-w-7xl mx-auto">
                <button
                    onClick={() => navigate('/dashboard')}
                    className="flex items-center gap-2 text-white/40 hover:text-white mb-8 transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" /> Back to Dashboard
                </button>

                <h1 className="text-3xl font-bold mb-8">All Campaigns</h1>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {campaigns.length > 0 ? (
                        campaigns.map((campaign, i) => (
                            <motion.div
                                key={campaign.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.05 }}
                                onClick={() => navigate(`/campaign/${campaign.id}`)}
                                className="group bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6 hover:border-indigo-500/30 transition-all cursor-pointer"
                            >
                                <div className="flex justify-between items-start mb-4">
                                    <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                                        <BarChart2 className="w-6 h-6" />
                                    </div>
                                    <span className={`px-3 py-1 rounded-full text-xs border ${campaign.status === 'completed' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                                            campaign.status === 'running' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                                                campaign.status === 'stopped' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                                    'bg-gray-500/10 text-gray-400 border-gray-500/20'
                                        }`}>
                                        {campaign.status.toUpperCase()}
                                    </span>
                                </div>
                                <h3 className="text-lg font-semibold mb-2 group-hover:text-indigo-400 transition-colors truncate">
                                    {campaign.name}
                                </h3>
                                <div className="flex items-center gap-4 text-sm text-white/40 border-t border-white/5 pt-4">
                                    <div className="flex items-center gap-1">
                                        <Calendar className="w-4 h-4" />
                                        <span>{new Date(campaign.created_at).toLocaleDateString()}</span>
                                    </div>
                                    <div className="ml-auto">
                                        {campaign.leads_count} Leads Found
                                    </div>
                                </div>
                            </motion.div>
                        ))
                    ) : (
                        <div className="col-span-3 text-center py-12 text-white/30">
                            <p>No campaigns found.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
