"use client";

import React, { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────

type GradientWavesDetail = "low" | "medium" | "high";

interface GradientWavesProps {
  horizonColor?: string;
  waveColor?: string;
  crestColor?: string;
  speed?: number;
  amplitude?: number;
  waveScale?: number;
  waveRatio?: number;
  swell?: number;
  turbulence?: number;
  tilt?: number;
  zoom?: number;
  height?: number;
  fogDepth?: number;
  detail?: GradientWavesDetail;
  brightness?: number;
  opacity?: number;
  mouseInteraction?: boolean;
  parallaxStrength?: number;
  grain?: boolean;
  grainIntensity?: number;
  className?: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function hexToVec3(hex: string): [number, number, number] {
  const c = hex.replace("#", "");
  return [
    parseInt(c.substring(0, 2), 16) / 255,
    parseInt(c.substring(2, 4), 16) / 255,
    parseInt(c.substring(4, 6), 16) / 255,
  ];
}

const DETAIL_STEPS: Record<GradientWavesDetail, number> = {
  low: 40,
  medium: 70,
  high: 110,
};

// ─── GLSL 1.00 (Universal WebGL1 + WebGL2) ───────────────────────────────────

const VERT_SRC = `
attribute vec2 position;
void main() {
  gl_Position = vec4(position, 0.0, 1.0);
}
`;

const FRAG_SRC = `
precision highp float;

uniform float iTime;
uniform vec2  iResolution;
uniform float uSpeed;
uniform float uAmplitude;
uniform float uWaveScale;
uniform float uWaveRatio;
uniform float uSwell;
uniform float uTurbulence;
uniform float uTilt;
uniform float uZoom;
uniform float uHeight;
uniform float uFogDepth;
uniform int   uSteps;
uniform float uBrightness;
uniform float uOpacity;
uniform int   uGrain;
uniform float uGrainIntensity;
uniform vec2  uMouse;
uniform float uParallax;
uniform int   uEnableMouse;
uniform vec3  uHorizonColor;
uniform vec3  uWaveColor;
uniform vec3  uCrestColor;

#define MAX_DIST 20000.0
#define EPS 0.1

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float sceneDist(vec3 pos) {
  vec2 freq = vec2(uWaveScale / 7.0, (uWaveScale * uWaveRatio) / 3.0);
  float T = iTime * uSpeed;
  vec4 tc = vec4(T / 0.130, T / 0.810, T / 0.200, T / 0.710);

  vec3 r = pos;
  float mx = r.x + tc.x;
  mx += uSwell * sin((r.y + mx) / 20.0 + tc.y);

  float my = r.y - tc.z;
  my += uTurbulence * cos(r.x / 23.0 + tc.w);

  float surface = r.z - (
    sin(mx * freq.x) * uAmplitude
    + sin(my * freq.y) * uAmplitude
    + uHeight
  );

  return surface;
}

vec3 buildRay(vec2 fragCoord) {
  vec2 uv = (fragCoord / iResolution) * 2.0 - 1.0;
  uv.x *= iResolution.x / iResolution.y;
  float fov = 1.0;
  vec3 ray = normalize(vec3(uv, -fov));

  // tilt
  float ct = cos(uTilt);
  float st = sin(uTilt);
  ray = vec3(ray.x, ct * ray.y - st * ray.z, st * ray.y + ct * ray.z);

  // mouse parallax
  if (uEnableMouse != 0) {
    float yaw   = (uMouse.x - 0.5) * uParallax * 0.4;
    float pitch = (uMouse.y - 0.5) * uParallax * 0.4;
    float cy = cos(yaw),   sy = sin(yaw);
    float cp = cos(pitch), sp = sin(pitch);
    ray = vec3(
      cy * ray.x + sy * ray.z,
      sp * sy * ray.x + cp * ray.y - sp * cy * ray.z,
      -sy * cp * ray.x + sp * ray.y + cp * cy * ray.z
    );
  }

  return normalize(ray);
}

void main() {
  vec3 cam = vec3(0.0, 0.0, 30.0);
  vec3 ray = buildRay(gl_FragCoord.xy);

  float dist = 0.0;
  vec3 pos = cam;
  bool hit = false;

  for (int i = 0; i < 128; i++) {
    if (i >= uSteps) break;
    float sd = sceneDist(pos);
    if (abs(sd) < EPS) { hit = true; break; }
    if (dist > MAX_DIST) break;
    dist += 0.9 * sd;
    pos = cam + ray * dist;
  }

  vec3 col;
  float alpha;

  if (hit) {
    float t = clamp(uFogDepth / max(dist, 0.001), 0.0, 1.0);
    vec3 body = mix(uWaveColor, uCrestColor, clamp(pos.z * 0.08 + 0.5, 0.0, 1.0));
    col = mix(uHorizonColor, body, t);
    col *= uBrightness;
    col = clamp(col, 0.0, 1.0);
    alpha = clamp(t, 0.0, 1.0) * uOpacity;
  } else {
    col = uHorizonColor * uBrightness;
    col = clamp(col, 0.0, 1.0);
    alpha = uOpacity * 0.4;
  }

  // grain
  if (uGrain != 0) {
    float g = hash(gl_FragCoord.xy + fract(iTime * 0.01)) - 0.5;
    alpha += g * uGrainIntensity;
  }

  gl_FragColor = vec4(clamp(col, 0.0, 1.0), clamp(alpha, 0.0, 1.0));
}
`;

// ─── Component ────────────────────────────────────────────────────────────────

export function GradientWaves({
  horizonColor = "#5227FF",
  waveColor = "#FF9FFC",
  crestColor = "#FFFFFF",
  speed = 0.4,
  amplitude = 2.5,
  waveScale = 0.6,
  waveRatio = 0.9,
  swell = 35,
  turbulence = 20,
  tilt = 1.11,
  zoom = 1.0,
  height = 5.5,
  fogDepth = 15,
  detail = "medium",
  brightness = 1.0,
  opacity = 1.0,
  mouseInteraction = true,
  parallaxStrength = 0.5,
  grain = true,
  grainIntensity = 0.05,
  className,
}: GradientWavesProps) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>(0);
  const startRef = useRef<number>(0);
  const mouseRef = useRef<[number, number]>([0.5, 0.5]);
  const targetMouseRef = useRef<[number, number]>([0.5, 0.5]);
  const glRef = useRef<WebGLRenderingContext | null>(null);
  const progRef = useRef<WebGLProgram | null>(null);
  const isVisibleRef = useRef(false);
  const isPageVisibleRef = useRef(true);
  const [webglFailed, setWebGLFailed] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    const wrapper = wrapperRef.current;
    if (!canvas || !wrapper || webglFailed) return;

    // WebGL context — supports both WebGL2 and WebGL1 fallback
    let gl: WebGLRenderingContext | null = null;
    try {
      gl = (canvas.getContext("webgl2", {
        alpha: true,
        premultipliedAlpha: true,
        antialias: false,
      }) ||
        canvas.getContext("webgl", {
          alpha: true,
          premultipliedAlpha: true,
          antialias: false,
        })) as WebGLRenderingContext | null;
    } catch {
      setWebGLFailed(true);
      return;
    }
    if (!gl) {
      setWebGLFailed(true);
      return;
    }
    glRef.current = gl;

    // Compile shaders
    function compileShader(type: number, src: string): WebGLShader | null {
      const s = gl!.createShader(type);
      if (!s) return null;
      gl!.shaderSource(s, src);
      gl!.compileShader(s);
      if (!gl!.getShaderParameter(s, gl!.COMPILE_STATUS)) {
        const log = gl!.getShaderInfoLog(s);
        if (log) {
          console.warn("GradientWaves shader warning:", log);
        }
        return null;
      }
      return s;
    }

    const vert = compileShader(gl.VERTEX_SHADER, VERT_SRC);
    const frag = compileShader(gl.FRAGMENT_SHADER, FRAG_SRC);
    if (!vert || !frag) {
      setWebGLFailed(true);
      return;
    }

    const prog = gl.createProgram();
    if (!prog) {
      setWebGLFailed(true);
      return;
    }
    gl.attachShader(prog, vert);
    gl.attachShader(prog, frag);
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      setWebGLFailed(true);
      return;
    }
    progRef.current = prog;
    gl.useProgram(prog);

    // Full-screen triangle
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 3, -1, -1, 3]),
      gl.STATIC_DRAW
    );
    const posLoc = gl.getAttribLocation(prog, "position");
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

    gl.deleteShader(vert);
    gl.deleteShader(frag);

    // Resize helper
    function resize() {
      if (!canvas || !wrapper || !gl) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = wrapper.clientWidth * dpr;
      canvas.height = wrapper.clientHeight * dpr;
      gl.viewport(0, 0, canvas.width, canvas.height);
    }
    resize();

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(wrapper);

    // Mouse
    function onPointerMove(e: PointerEvent) {
      if (!wrapper) return;
      const rect = wrapper.getBoundingClientRect();
      targetMouseRef.current = [
        (e.clientX - rect.left) / rect.width,
        (e.clientY - rect.top) / rect.height,
      ];
    }
    function onPointerLeave() {
      targetMouseRef.current = [0.5, 0.5];
    }
    wrapper.addEventListener("pointermove", onPointerMove);
    wrapper.addEventListener("pointerleave", onPointerLeave);

    // Visibility
    function onVisibilityChange() {
      isPageVisibleRef.current = !document.hidden;
    }
    document.addEventListener("visibilitychange", onVisibilityChange);

    const intersectionObserver = new IntersectionObserver(
      (entries) => {
        isVisibleRef.current = entries[0].isIntersecting;
      },
      { threshold: 0.05 }
    );
    intersectionObserver.observe(wrapper);

    // Render loop
    const uLoc = (name: string) => gl!.getUniformLocation(prog, name);
    const steps = DETAIL_STEPS[detail];
    const [hr, hg, hb] = hexToVec3(horizonColor);
    const [wr, wg, wb] = hexToVec3(waveColor);
    const [cr, cg, cb] = hexToVec3(crestColor);

    function render(now: number) {
      if (!gl || !canvas) return;
      rafRef.current = requestAnimationFrame(render);

      if (!isVisibleRef.current || !isPageVisibleRef.current) return;

      if (startRef.current === 0) startRef.current = now;
      const elapsed = (now - startRef.current) / 1000;

      // Smooth mouse
      const [mx, my] = mouseRef.current;
      const [tx, ty] = targetMouseRef.current;
      mouseRef.current = [mx + (tx - mx) * 0.05, my + (ty - my) * 0.05];

      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);

      gl.uniform1f(uLoc("iTime"), elapsed);
      gl.uniform2f(uLoc("iResolution"), canvas.width, canvas.height);
      gl.uniform1f(uLoc("uSpeed"), speed);
      gl.uniform1f(uLoc("uAmplitude"), amplitude);
      gl.uniform1f(uLoc("uWaveScale"), waveScale);
      gl.uniform1f(uLoc("uWaveRatio"), waveRatio);
      gl.uniform1f(uLoc("uSwell"), swell);
      gl.uniform1f(uLoc("uTurbulence"), turbulence);
      gl.uniform1f(uLoc("uTilt"), tilt);
      gl.uniform1f(uLoc("uZoom"), zoom);
      gl.uniform1f(uLoc("uHeight"), height);
      gl.uniform1f(uLoc("uFogDepth"), fogDepth);
      gl.uniform1i(uLoc("uSteps"), steps);
      gl.uniform1f(uLoc("uBrightness"), brightness);
      gl.uniform1f(uLoc("uOpacity"), opacity);
      gl.uniform1i(uLoc("uGrain"), grain ? 1 : 0);
      gl.uniform1f(uLoc("uGrainIntensity"), grainIntensity);
      gl.uniform2f(uLoc("uMouse"), mouseRef.current[0], mouseRef.current[1]);
      gl.uniform1f(uLoc("uParallax"), parallaxStrength);
      gl.uniform1i(uLoc("uEnableMouse"), mouseInteraction ? 1 : 0);
      gl.uniform3f(uLoc("uHorizonColor"), hr, hg, hb);
      gl.uniform3f(uLoc("uWaveColor"), wr, wg, wb);
      gl.uniform3f(uLoc("uCrestColor"), cr, cg, cb);

      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }

    rafRef.current = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(rafRef.current);
      resizeObserver.disconnect();
      intersectionObserver.disconnect();
      document.removeEventListener("visibilitychange", onVisibilityChange);
      wrapper.removeEventListener("pointermove", onPointerMove);
      wrapper.removeEventListener("pointerleave", onPointerLeave);

      if (gl && prog) {
        gl.deleteProgram(prog);
        gl.deleteBuffer(buf);
        const ext = gl.getExtension("WEBGL_lose_context");
        ext?.loseContext();
      }
    };
  }, [
    horizonColor, waveColor, crestColor,
    speed, amplitude, waveScale, waveRatio,
    swell, turbulence, tilt, zoom, height, fogDepth, detail,
    brightness, opacity, mouseInteraction, parallaxStrength,
    grain, grainIntensity, webglFailed
  ]);

  return (
    <div
      ref={wrapperRef}
      className={cn("relative w-full overflow-hidden", className)}
    >
      {!webglFailed ? (
        <canvas
          ref={canvasRef}
          aria-hidden
          className="pointer-events-none absolute inset-0 h-full w-full"
        />
      ) : (
        <div
          className="absolute inset-0"
          style={{
            background: `radial-gradient(ellipse at center, ${waveColor}33 0%, ${horizonColor} 80%)`,
          }}
        />
      )}
    </div>
  );
}
