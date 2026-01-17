import React, { useRef, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF, useAnimations } from '@react-three/drei';
import { Group } from 'three';
import { SystemState } from '../types';

// Fix for missing JSX Intrinsic Elements definitions in the current environment
declare global {
  namespace JSX {
    interface IntrinsicElements {
      group: any;
      primitive: any;
    }
  }
}

// Augment React.JSX for newer React type definitions
declare module 'react' {
  namespace JSX {
    interface IntrinsicElements {
      group: any;
      primitive: any;
    }
  }
}

interface AgentProps {
  state: SystemState;
}

export const Agent = ({ state }: AgentProps) => {
  const groupRef = useRef<Group>(null);
  
  // Load model and extract animations
  const { scene, animations } = useGLTF('/RLM.glb');
  const { actions } = useAnimations(animations, groupRef);
  
  const isActive = state === SystemState.ANALYZING;

  // 1. ANIMATION MIXER LOGIC (For baked animations)
  useEffect(() => {
    if (animations.length > 0) {
      // Play all clips found in the file
      Object.keys(actions).forEach((key) => {
        const action = actions[key];
        if (action) {
          action.reset().fadeIn(0.5).play();
          action.timeScale = 0.25; // Slow down baked animations for research aesthetic
        }
      });
    }
  }, [actions, animations]);

  // 2. PROCEDURAL MOTION LOOP (Guarantees motion)
  useFrame((stateContext, delta) => {
    if (groupRef.current) {
      const t = stateContext.clock.elapsedTime;

      // A) Continuous Slow Rotation (Y-axis)
      // "The system is always running."
// A) Micro idle sway (SAFE — never flips)
const swaySpeed = isActive ? 0.8 : 0.4;
groupRef.current.rotation.y = Math.sin(t * swaySpeed) * 0.03; // ±1.7°


      // B) Gentle Scale Breathing (Simulate "Computing")
      // Very subtle +/- 1% oscillation
      const breathFreq = isActive ? 1.5 : 0.8;
      const scaleDev = 0.01; 
      const scaleBase = 1.0;
      const currentScale = scaleBase + Math.sin(t * breathFreq) * scaleDev;
      groupRef.current.scale.setScalar(currentScale);

      // C) Micro-drift on Z (Depth)
      // Adds a feeling of floating in a fluid medium
      groupRef.current.position.z = Math.sin(t * 0.2) * 0.1;
    }
  });

  return (
    // @ts-ignore
    <group position={[0, -0.5, 0]}>
      {/* 
         No <Float> wrapper used here to maintain precise control 
         over the close-up framing. Movement is handled in useFrame.
      */}
      {/* @ts-ignore */}
      <primitive 
        ref={groupRef}
        object={scene} 
        rotation={[0.1, 0, 0]} // Slight tilt towards camera to show top geometry
      />
    </group>
  );
};

// Preload to prevent layout shift/pop-in
useGLTF.preload('/RLM.glb');