import React, { useEffect, useState, useRef } from 'react';

export default function LiveFeed({ campaignId }) {
    const [messages, setMessages] = useState([]);
    const [status, setStatus] = useState('connecting');
    const wsRef = useRef(null);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        const ws = new WebSocket(
            `ws://localhost:8000/api/campaigns/${campaignId}/live`
        );

        ws.onopen = () => {
            console.log('WebSocket connected');
            setStatus('running');
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('WebSocket message:', data);

            if (data.type === 'update') {
                setMessages(prev => [...prev, {
                    text: data.message,
                    timestamp: data.timestamp,
                    id: `${Date.now()}-${Math.random()}`
                }]);
            } else if (data.type === 'complete') {
                setStatus('complete');
                setMessages(prev => [...prev, {
                    text: '🎉 Campaign complete!',
                    timestamp: new Date().toISOString(),
                    id: `${Date.now()}-${Math.random()}`
                }]);
            } else if (data.type === 'error') {
                setStatus('error');
                setMessages(prev => [...prev, {
                    text: `❌ Error: ${data.message}`,
                    timestamp: new Date().toISOString(),
                    id: `${Date.now()}-${Math.random()}`
                }]);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setStatus('error');
        };

        ws.onclose = () => {
            console.log('WebSocket closed');
            if (status === 'running') {
                setStatus('disconnected');
            }
        };

        wsRef.current = ws;

        return () => ws.close();
    }, [campaignId]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="bg-gray-900 rounded-lg p-6 h-96 overflow-hidden flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-bold text-lg flex items-center">
                    <span className="mr-2">📡</span>
                    Live Agent Activity
                </h3>
                <StatusBadge status={status} />
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto font-mono text-sm space-y-2">
                {messages.map((msg) => (
                    <div key={msg.id} className="text-green-400 flex items-start">
                        <span className="text-gray-500 text-xs mr-2">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                        </span>
                        <span>{msg.text}</span>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>
        </div>
    );
}

function StatusBadge({ status }) {
    const statusConfig = {
        connecting: { color: 'bg-yellow-500', text: 'Connecting...' },
        running: { color: 'bg-green-500 animate-pulse', text: 'Running' },
        complete: { color: 'bg-blue-500', text: 'Complete' },
        error: { color: 'bg-red-500', text: 'Error' },
        disconnected: { color: 'bg-gray-500', text: 'Disconnected' }
    };

    const config = statusConfig[status] || statusConfig.connecting;

    return (
        <div className="flex items-center">
            <div className={`w-2 h-2 rounded-full ${config.color} mr-2`} />
            <span className="text-gray-400 text-sm">{config.text}</span>
        </div>
    );
}
