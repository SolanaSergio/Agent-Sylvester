
import React from 'react'
import { useRouter } from 'next/router'
import { usePlaylist } from '@/hooks/usePlaylist'
import { PlaylistDetails } from '@/components/playlist/PlaylistDetails'
import { TrackList } from '@/components/playlist/TrackList'

export default function PlaylistPage() {
    const router = useRouter()
    const { id } = router.query
    const { playlist, loading, error } = usePlaylist(id as string)
    
    if (loading) return <div>Loading...</div>
    if (error) return <div>Error: {error}</div>
    if (!playlist) return <div>Playlist not found</div>
    
    return (
        <div className="container mx-auto px-4 py-8">
            <PlaylistDetails playlist={playlist} />
            <TrackList tracks={playlist.tracks} />
        </div>
    )
}
