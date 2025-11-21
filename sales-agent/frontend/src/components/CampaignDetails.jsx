import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Activity, Users, Mail, MessageSquare, Star, ArrowLeft, X, Globe, Linkedin, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function CampaignDetails() {
    const { campaignId } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [ws, setWs] = useState(null);
    const [emailLogs, setEmailLogs] = useState([]);
    const [selectedLead, setSelectedLead] = useState(null);

    useEffect(() => {
        fetchDashboardData();
        const websocket = new WebSocket(`ws://localhost:8000/api/campaigns/${campaignId}/live`);

        websocket.onmessage = (event) => {
            const update = JSON.parse(event.data);
            setLogs(prev => [...prev, {
                timestamp: new Date().toLocaleTimeString(),
                message: update.message,
                type: update.type
            }]);

            // Refresh data on major updates
            const msg = update.message;
            if (
                msg.includes("complete") ||
                msg.includes("Sent") ||
                msg.includes("Saved") ||
                msg.includes("Score") ||
                msg.includes("Email sent") ||
                msg.includes("stopped")
            ) {
                fetchDashboardData();
            }
        };

        setWs(websocket);

        return () => {
            websocket.close();
        };
    }, [campaignId]);

    const fetchDashboardData = async () => {
        try {
            const response = await fetch(`http://127.0.0.1:8000/api/campaigns/${campaignId}`);
            if (response.ok) {
                const result = await response.json();
                setData(result);
                if (result.email_logs) {
                    setEmailLogs(result.email_logs);
                }
            }
            setLoading(false);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
            setLoading(false);
        }
    };

    const handleStopCampaign = async () => {
        try {
            await fetch(`http://127.0.0.1:8000/api/campaigns/${campaignId}/stop`, {
                method: 'POST'
            });
            fetchDashboardData();
        } catch (error) {
            console.error('Error stopping campaign:', error);
        }
    };

    const handleDeleteCampaign = async () => {
        if (!window.confirm('Are you sure you want to delete this campaign? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/campaigns/${campaignId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                navigate('/dashboard');
            } else {
                console.error('Failed to delete campaign');
            }
        } catch (error) {
            console.error('Error deleting campaign:', error);
        }
    };

    if (loading) return <div className="min-h-screen bg-[#030303] text-white flex items-center justify-center">Loading...</div>;
    if (!data) return <div className="min-h-screen bg-[#030303] text-white flex items-center justify-center">Campaign not found</div>;

    return (
        <div className="min-h-screen bg-[#030303] text-white p-8 relative">
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center gap-4 mb-8">
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="p-2 rounded-full bg-white/5 hover:bg-white/10 transition-colors"
                    >
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                    <div>
                        <h1 className="text-3xl font-bold">{data.campaign.name}</h1>
                        <p className="text-white/40 text-sm">ID: {campaignId}</p>
                    </div>
                    <div className="ml-auto flex items-center gap-4">
                        {data.campaign.status === 'running' && (
                            <button
                                onClick={handleStopCampaign}
                                className="px-4 py-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors font-medium text-sm"
                            >
                                Stop Campaign
                            </button>
                        )}
                        <button
                            onClick={handleDeleteCampaign}
                            className="px-4 py-2 rounded-lg bg-white/5 text-white/60 hover:bg-red-500/20 hover:text-red-400 transition-colors font-medium text-sm"
                        >
                            Delete
                        </button>
                        <div className={`px-4 py-1 rounded-full text-sm ${data.campaign.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                            data.campaign.status === 'running' ? 'bg-blue-500/20 text-blue-400' :
                                data.campaign.status === 'stopped' ? 'bg-red-500/20 text-red-400' :
                                    'bg-gray-500/20 text-gray-400'
                            }`}>
                            {data.campaign.status.toUpperCase()}
                        </div>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <StatCard icon={<Users className="w-6 h-6 text-blue-400" />} label="Leads Found" value={data.stats.leads_found} delay={0.1} />
                    <StatCard icon={<Mail className="w-6 h-6 text-purple-400" />} label="Emails Sent" value={data.stats.emails_sent} delay={0.2} />
                    <StatCard icon={<MessageSquare className="w-6 h-6 text-yellow-400" />} label="Replies" value={data.stats.replies} delay={0.3} />
                    <StatCard icon={<Star className="w-6 h-6 text-green-400" />} label="Positive Interest" value={data.stats.positive_interest} delay={0.4} />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Live Feed */}
                    <div className="lg:col-span-2 space-y-8">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6"
                        >
                            <div className="flex items-center gap-2 mb-4">
                                <Activity className="w-5 h-5 text-rose-400" />
                                <h2 className="text-xl font-semibold">Live Agent Activity</h2>
                            </div>
                            <div className="h-64 overflow-y-auto space-y-2 font-mono text-sm custom-scrollbar">
                                {logs.map((log, i) => (
                                    <div key={i} className="flex gap-3 text-white/80">
                                        <span className="text-white/30 shrink-0">{log.timestamp}</span>
                                        <span>{log.message}</span>
                                    </div>
                                ))}
                                {logs.length === 0 && <p className="text-white/30 italic">Waiting for agent activity...</p>}
                            </div>
                        </motion.div>

                        {/* Email Logs */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6"
                        >
                            <div className="flex items-center gap-2 mb-4">
                                <Mail className="w-5 h-5 text-purple-400" />
                                <h2 className="text-xl font-semibold">Email Logs</h2>
                            </div>
                            <div className="space-y-4">
                                {emailLogs.length > 0 ? (
                                    emailLogs.map((log, i) => (
                                        <div key={i} className="bg-white/5 rounded-lg p-4 border border-white/5">
                                            <div className="flex justify-between items-start mb-2">
                                                <h3 className="font-medium text-white">{log.subject}</h3>
                                                <span className={`text-xs px-2 py-1 rounded ${log.success ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                                                    }`}>
                                                    {log.success ? 'Sent' : 'Failed'}
                                                </span>
                                            </div>
                                            <p className="text-sm text-white/60 mb-2">To: {log.company_name}</p>
                                            <div className="text-xs text-white/40 bg-black/20 p-2 rounded">
                                                {log.body.substring(0, 150)}...
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <p className="text-white/30 italic">No emails sent yet.</p>
                                )}
                            </div>
                        </motion.div>
                    </div>

                    {/* Top Leads */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 }}
                        className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6 h-fit"
                    >
                        <div className="flex items-center gap-2 mb-4">
                            <Star className="w-5 h-5 text-yellow-400" />
                            <h2 className="text-xl font-semibold">Top Leads</h2>
                        </div>
                        <div className="space-y-4">
                            {data.leads && data.leads.length > 0 ? (
                                data.leads.map((lead, i) => (
                                    <div
                                        key={i}
                                        onClick={() => setSelectedLead(lead)}
                                        className="p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors cursor-pointer"
                                    >
                                        <div className="flex justify-between items-start">
                                            <h3 className="font-medium text-white/90">{lead.company_name}</h3>
                                            <span className="text-xs font-bold text-green-400">
                                                {Math.round((lead.ml_score || 0) * 100)}%
                                            </span>
                                        </div>
                                        <p className="text-xs text-white/50 mt-1 truncate">{lead.industry}</p>
                                    </div>
                                ))
                            ) : (
                                <p className="text-white/30 italic">No leads found yet.</p>
                            )}
                        </div>
                    </motion.div>
                </div>
            </div>

            {/* Lead Details Modal */}
            <AnimatePresence>
                {selectedLead && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4"
                        onClick={() => setSelectedLead(null)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="bg-[#0A0A0A] border border-white/10 rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl"
                            onClick={e => e.stopPropagation()}
                        >
                            <div className="flex justify-between items-start mb-6">
                                <div>
                                    <h2 className="text-2xl font-bold text-white mb-2">{selectedLead.company_name}</h2>
                                    <div className="flex flex-wrap gap-2 text-sm text-white/60">
                                        {selectedLead.industry && <span className="bg-white/5 px-2 py-1 rounded">{selectedLead.industry}</span>}
                                        {selectedLead.location && <span className="bg-white/5 px-2 py-1 rounded">{selectedLead.location}</span>}
                                        {selectedLead.company_size && <span className="bg-white/5 px-2 py-1 rounded">{selectedLead.company_size} employees</span>}
                                    </div>
                                </div>
                                <button
                                    onClick={() => setSelectedLead(null)}
                                    className="p-2 rounded-full bg-white/5 hover:bg-white/10 transition-colors"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                                <div className="space-y-4">
                                    <div className="bg-white/5 rounded-xl p-4">
                                        <h3 className="text-sm font-medium text-white/40 mb-3 uppercase tracking-wider">Contact Info</h3>
                                        <div className="space-y-3">
                                            {selectedLead.website && (
                                                <a href={selectedLead.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-blue-400 hover:underline">
                                                    <Globe className="w-4 h-4" /> Website
                                                </a>
                                            )}
                                            {selectedLead.linkedin_url && (
                                                <a href={selectedLead.linkedin_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-blue-400 hover:underline">
                                                    <Linkedin className="w-4 h-4" /> LinkedIn
                                                </a>
                                            )}
                                            {selectedLead.email && (
                                                <div className="flex items-center gap-2 text-white/80">
                                                    <Mail className="w-4 h-4 text-white/40" /> {selectedLead.email}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="bg-white/5 rounded-xl p-4">
                                        <h3 className="text-sm font-medium text-white/40 mb-3 uppercase tracking-wider">Decision Maker</h3>
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 rounded-full bg-white/10">
                                                <User className="w-5 h-5 text-white/60" />
                                            </div>
                                            <div>
                                                <p className="font-medium text-white">{selectedLead.decision_maker_name || "Unknown"}</p>
                                                <p className="text-sm text-white/40">{selectedLead.decision_maker_title || "N/A"}</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-white/5 rounded-xl p-4">
                                    <h3 className="text-sm font-medium text-white/40 mb-3 uppercase tracking-wider">AI Analysis</h3>
                                    <div className="mb-4">
                                        <div className="flex justify-between items-end mb-2">
                                            <span className="text-sm text-white/60">Match Score</span>
                                            <span className="text-2xl font-bold text-green-400">{Math.round((selectedLead.ml_score || 0) * 100)}%</span>
                                        </div>
                                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-green-500"
                                                style={{ width: `${(selectedLead.ml_score || 0) * 100}%` }}
                                            />
                                        </div>
                                    </div>

                                    {selectedLead.score_explanation && (
                                        <div>
                                            <p className="text-xs text-white/40 mb-2">Key Factors:</p>
                                            <ul className="space-y-1">
                                                {Array.isArray(selectedLead.score_explanation) ? (
                                                    selectedLead.score_explanation.map((factor, i) => (
                                                        <li key={i} className="text-sm text-white/80 flex items-start gap-2">
                                                            <span className="text-green-400 mt-1">•</span>
                                                            {typeof factor === 'object' ? (
                                                                <span>
                                                                    <span className="font-medium text-white/90">{factor.name || factor.factor}</span>
                                                                    {factor.value && <span className="text-white/50 mx-1">- {factor.value}</span>}
                                                                    {factor.impact && <span className={`text-xs px-1 rounded ${factor.impact === 'High' ? 'bg-green-500/20 text-green-400' : 'bg-white/10 text-white/60'}`}>{factor.impact}</span>}
                                                                </span>
                                                            ) : (
                                                                factor
                                                            )}
                                                        </li>
                                                    ))
                                                ) : (
                                                    <li className="text-sm text-white/80">{selectedLead.score_explanation}</li>
                                                )}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {selectedLead.description && (
                                <div className="bg-white/5 rounded-xl p-4">
                                    <h3 className="text-sm font-medium text-white/40 mb-2 uppercase tracking-wider">Company Description</h3>
                                    <p className="text-white/70 text-sm leading-relaxed">{selectedLead.description}</p>
                                </div>
                            )}
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

function StatCard({ icon, label, value, delay }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay }}
            className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6 flex items-center gap-4"
        >
            <div className="p-3 rounded-full bg-white/5">
                {icon}
            </div>
            <div>
                <p className="text-white/40 text-sm">{label}</p>
                <p className="text-2xl font-bold text-white">{value}</p>
            </div>
        </motion.div>
    );
}
