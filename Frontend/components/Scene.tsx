import React from 'react';
import { Canvas } from '@react-three/fiber';
import { Agent } from './Agent';
import { SystemState } from '../types';
import { PerspectiveCamera, Environment } from '@react-three/drei';

// Fix for missing JSX Intrinsic Elements definitions in the current environment
declare global {
  namespace JSX {
    interface IntrinsicElements {
      ambientLight: any;
      spotLight: any;
      fog: any;
    }
  }
}

// Augment React.JSX for newer React type definitions
declare module 'react' {
  namespace JSX {
    interface IntrinsicElements {
      ambientLight: any;
      spotLight: any;
      fog: any;
    }
  }
}

interface SceneProps {
  state: SystemState;
}

export const Scene = ({ state }: SceneProps) => {
  return (
    <div className="absolute inset-0 z-0 bg-[#050505]">
      <Canvas shadows dpr={[1, 2]}>
        {/* 
           CAMERA CONFIGURATION: EXTREME CLOSE-UP
           - Narrow FOV (22) compresses depth and feels more "cinematic/macro".
           - Positioned very close to the subject to fill the frame with abstract geometry.
           - User feels "inside" the system.
        */}
<PerspectiveCamera
  makeDefault
  position={[0, 0.95, 2.0]}   // ← +0.15 zoom out
  fov={28}                    // ← +1 degree only
  onUpdate={(c) => c.lookAt(0, 0.85, 0)}
/>

        
        {/* 
           ATMOSPHERE & DEPTH
           - Fog starts very close to blend the background geometry into void.
        */}
        {/* @ts-ignore */}
        <fog attach="fog" args={['#050505', 1.5, 5.5]} />

        {/* 
            LIGHTING SETUP: MACRO PHOTOGRAPHY STYLE
            - Soft, non-directional ambient.
            - Gentle key light to reveal texture.
            - No harsh hotspots.
        */}
        
        {/* @ts-ignore */}
        <ambientLight intensity={0.3} color="#cfd8dc" />

        {/* Key Light: Soft, upper right */}
        {/* @ts-ignore */}
        <spotLight 
          position={[2, 3, 4]} 
          angle={0.6} 
          penumbra={1} 
          intensity={0.8} 
          color="#ffffff" 
          castShadow 
          shadow-bias={-0.0001}
        />

        {/* Rim/Fill Light: Cool tone from left/back */}
        {/* @ts-ignore */}
        <spotLight 
          position={[-3, 0, -2]} 
          intensity={1.0} 
          color="#90caf9" 
          angle={1}
          penumbra={1}
        />

        {/* 
           Reflections:
           City preset provides complex reflections for metallic/smooth surfaces
           even at low intensity.
        */}
        <Environment preset="city" environmentIntensity={0.15} />

        {/* THE RECURSIVE MODEL */}
        <Agent state={state} />

        {/* Note: ContactShadows removed as we are floating in void/macro space */}

      </Canvas>
    </div>
  );
};