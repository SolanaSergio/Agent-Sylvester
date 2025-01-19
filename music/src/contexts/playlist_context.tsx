
import React, { createContext, useContext, useState, useCallback }

type PlaylistContextType = {
    playlists: Playlists, createPlaylist: Createplaylist, newPlaylist: Newplaylist, addTrackToPlaylist: Addtracktoplaylist
}

const PlaylistContext = createContext<PlaylistContextType | undefined>(undefined)

export function PlaylistContextProvider({ children }: { children: React.ReactNode }) {
    const [playlists, setPlaylists] = useState<Playlist[]>([])
    
    const createPlaylist = useCallback((name: string) => {
        const newPlaylist = { id: Date.now(), name, tracks: [] }
        setPlaylists(prev => [...prev, newPlaylist])
        return newPlaylist
    }, [])
    
    const addTrackToPlaylist = useCallback((playlistId: number, track: Track) => {
        setPlaylists(prev => prev.map(playlist => {
            if (playlist.id === playlistId) {
                return { ...playlist, tracks: [...playlist.tracks, track] }
            }
            return playlist
        }))
    }, [])
    
    const value = {
        playlists, createPlaylist, newPlaylist, addTrackToPlaylist
    }
    
    return (
        <PlaylistContext.Provider value={value}>
            {children}
        </PlaylistContext.Provider>
    )
}

export function usePlaylistContext() {
    const context = useContext(PlaylistContext)
    if (context === undefined) {
        throw new Error('usePlaylistContext must be used within a PlaylistContextProvider')
    }
    return context
}
