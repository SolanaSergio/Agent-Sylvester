
import React, { createContext, useContext, useState, useCallback }

type AudioContextType = {
    
}

const AudioContext = createContext<AudioContextType | undefined>(undefined)

export function AudioContextProvider({ children }: { children: React.ReactNode }) {
    
    
    
    
    const value = {
        
    }
    
    return (
        <AudioContext.Provider value={value}>
            {children}
        </AudioContext.Provider>
    )
}

export function useAudioContext() {
    const context = useContext(AudioContext)
    if (context === undefined) {
        throw new Error('useAudioContext must be used within a AudioContextProvider')
    }
    return context
}
