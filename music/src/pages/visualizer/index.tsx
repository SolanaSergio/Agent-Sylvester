
import React from 'react'
import { AudioVisualizer } from '@/components/visualizer/AudioVisualizer'
import { VisualizerControls } from '@/components/visualizer/VisualizerControls'
import { useAudioContext } from '@/hooks/useAudioContext'

export default function VisualizerPage() {
    const { audioContext, analyser } = useAudioContext()
    
    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold mb-8">Audio Visualizer</h1>
            <div className="grid grid-cols-1 gap-8">
                <AudioVisualizer analyser={analyser} />
                <VisualizerControls audioContext={audioContext} />
            </div>
        </div>
    )
}
