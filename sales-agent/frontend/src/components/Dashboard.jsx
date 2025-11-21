import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Plus, ArrowRight, Calendar, BarChart2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
    const [campaigns, setCampaigns] = useState([]);
    const navigate = useNavigate();
    const user = JSON.parse(localStorage.getItem('user') || '{}');

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
        <div className="min-h-screen bg-[#030303] text-white">
            {/* Navbar */}
            <nav className="border-b border-white/10 bg-black/20 backdrop-blur-xl sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16 items-center">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-rose-500 flex items-center justify-center font-bold">
                                AI
                            </div>
                            <span className="font-bold text-lg tracking-tight">SalesAgent.ai</span>
                        </div>
                        <div className="flex items-center gap-4">
                            <span className="text-white/60 text-sm">Welcome, {user.full_name || 'User'}</span>
                            <button
                                onClick={() => {
                                    localStorage.removeItem('token');
                                    localStorage.removeItem('user');
                                    navigate('/login');
                                }}
                                className="text-sm text-white/40 hover:text-white transition-colors"
                            >
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="flex justify-between items-end mb-12">
                    <div>
                        <h1 className="text-4xl font-bold mb-2">Dashboard</h1>
                        <p className="text-white/40">Overview of your sales campaigns</p>
                    </div>
                    <button
                        onClick={() => navigate('/campaigns/new')}
                        className="flex items-center gap-2 bg-white text-black px-6 py-3 rounded-full font-semibold hover:bg-gray-200 transition-colors"
                    >
                        <Plus className="w-5 h-5" />
                        New Campaign
                    </button>
                </div>

                {/* Recent Campaigns */}
                <div className="mb-8">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-semibold">Recent Campaigns</h2>
                        <button
                            onClick={() => navigate('/campaigns/all')}
                            className="text-indigo-400 text-sm hover:text-indigo-300 flex items-center gap-1"
                        >
                            View All <ArrowRight className="w-4 h-4" />
                        </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {campaigns.length > 0 ? (
                            campaigns.slice(0, 3).map((campaign, i) => (
                                <motion.div
                                    key={campaign.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.1 }}
                                    onClick={() => navigate(`/campaign/${campaign.id}`)}
                                    className="group bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6 hover:border-indigo-500/30 transition-all cursor-pointer"
                                >
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                                            <BarChart2 className="w-6 h-6" />
                                        </div>
                                        <span className={`px-3 py-1 rounded-full text-xs border ${campaign.status === 'completed' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                                            campaign.status === 'running' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
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
                                <p>No campaigns yet. Create your first one!</p>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
