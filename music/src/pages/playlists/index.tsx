
import React from 'react'
import { PlaylistGrid } from '@/components/playlist/PlaylistGrid'
import { CreatePlaylistButton } from '@/components/playlist/CreatePlaylistButton'

export default function PlaylistsPage() {
    return (
        <div className="container mx-auto px-4 py-8">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-bold">Your Playlists</h1>
                <CreatePlaylistButton />
            </div>
            <PlaylistGrid />
        </div>
    )
}
