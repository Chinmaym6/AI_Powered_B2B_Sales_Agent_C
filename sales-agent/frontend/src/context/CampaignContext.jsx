import React, { createContext, useState, useContext } from 'react';

const CampaignContext = createContext();

export const CampaignProvider = ({ children }) => {
    const [campaignId, setCampaignId] = useState(null);

    return (
        <CampaignContext.Provider value={{ campaignId, setCampaignId }}>
            {children}
        </CampaignContext.Provider>
    );
};

export const useCampaign = () => useContext(CampaignContext);
