"use client";

import React, {
  useEffect,
  useRef,
  useState,
  useCallback,
} from "react";
import { cn } from "@/lib/utils";

// ─── WebGL Error Boundary ────────────────────────────────────────────────────

interface WebGLFallbackProps {
  colorDeep?: string;
  colorMid?: string;
  colorHighlight?: string;
  className?: string;
}

function WebGLFallback({
  colorDeep = "#02051C",
  colorMid = "#050A30",
  colorHighlight = "#00FFFF",
  className,
}: WebGLFallbackProps) {
  return (
    <div
      className={cn("absolute inset-0", className)}
      style={{
        background: `radial-gradient(ellipse at 30% 60%, ${colorHighlight}22 0%, ${colorMid}44 40%, ${colorDeep} 80%)`,
      }}
    />
  );
}

// ─── Shaders ─────────────────────────────────────────────────────────────────

const VERT_SRC = `
attribute vec2 position;
void main() {
  gl_Position = vec4(position, 0.0, 1.0);
}
`;

const FRAG_SRC = `
precision highp float;

uniform float u_time;
uniform vec2  u_resolution;
uniform vec3  u_colorDeep;
uniform vec3  u_colorMid;
uniform vec3  u_colorHighlight;
uniform float u_speed;
uniform float u_flowStrength;
uniform float u_grain;
uniform float u_contrast;
uniform float u_opacity;
uniform float u_reveal;

mat2 rot = mat2(0.86, 0.51, -0.51, 0.86);

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  float a = hash(i);
  float b = hash(i + vec2(1.0, 0.0));
  float c = hash(i + vec2(0.0, 1.0));
  float d = hash(i + vec2(1.0, 1.0));
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p) {
  float v = 0.0;
  float a = 0.5;
  for (int i = 0; i < 6; i++) {
    v += a * noise(p);
    p  = rot * p * 2.1;
    a *= 0.5;
  }
  return v;
}

void main() {
  vec2 uv = gl_FragCoord.xy / u_resolution;
  uv.y = 1.0 - uv.y;

  // aspect correction
  vec2 p = uv;
  p.x *= u_resolution.x / u_resolution.y;

  float t = u_time * (0.14 * u_speed);

  vec2 flowP = vec2(p.x * 1.1, p.y - t * 0.35);

  float n1 = fbm(flowP * 2.8 + vec2(0.0, t * 0.2));
  float n2 = fbm((flowP + n1 * 0.45) * 4.0 - vec2(0.0, t * 0.35));
  float n3 = fbm((flowP + n2 * 0.4) * 6.5 + vec2(t * 0.15, 0.0));

  float structure = n3 * 1.15 + (n2 - 0.5) * 0.5;
  structure += (n1 - 0.5) * 0.3 * u_flowStrength;

  // color mapping
  float lowBand  = smoothstep(0.18, 0.6,  structure);
  float highBand = smoothstep(0.62, 1.08, structure);

  vec3 col = mix(u_colorDeep, u_colorMid, lowBand);
  col = mix(col, u_colorHighlight, highBand);

  float glow = smoothstep(0.52, 0.95, structure) * (0.35 + 0.5 * u_flowStrength);
  col += glow * u_colorHighlight * 0.35;

  // contrast
  col = (col - 0.5) * u_contrast + 0.5;
  col = clamp(col, 0.0, 1.0);

  // vertical alpha mask
  float verticalMask = smoothstep(1.05, 0.05, uv.y);
  verticalMask = pow(verticalMask, 1.1);

  // reveal mask (left-to-right)
  float alpha = verticalMask * smoothstep(0.08, 0.95, structure);
  alpha *= smoothstep(0.0, 0.28, u_reveal - uv.x);
  alpha *= u_opacity;

  // grain
  float grainVal = hash(uv + fract(u_time * 0.01)) - 0.5;
  col += grainVal * u_grain;

  gl_FragColor = vec4(clamp(col, 0.0, 1.0), clamp(alpha, 0.0, 1.0));
}
`;

// ─── Helpers ─────────────────────────────────────────────────────────────────

function hexToVec3(hex: string): [number, number, number] {
  const c = hex.replace("#", "");
  return [
    parseInt(c.substring(0, 2), 16) / 255,
    parseInt(c.substring(2, 4), 16) / 255,
    parseInt(c.substring(4, 6), 16) / 255,
  ];
}

function compileShader(
  gl: WebGLRenderingContext,
  type: number,
  src: string
): WebGLShader {
  const shader = gl.createShader(type)!;
  gl.shaderSource(shader, src);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    throw new Error(gl.getShaderInfoLog(shader) ?? "Shader compile error");
  }
  return shader;
}

// ─── Props ───────────────────────────────────────────────────────────────────

interface WebGLLiquidProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  description?: string;
  colorDeep?: string;
  colorMid?: string;
  colorHighlight?: string;
  speed?: number;
  flowStrength?: number;
  grain?: number;
  contrast?: number;
  opacity?: number;
  reveal?: boolean;
  delayMs?: number;
  revealDuration?: number;
  children?: React.ReactNode;
}

// ─── Component ───────────────────────────────────────────────────────────────

export function WebGLLiquid({
  title,
  subtitle,
  description,
  colorDeep = "#02051C",
  colorMid = "#050A30",
  colorHighlight = "#00FFFF",
  speed = 1,
  flowStrength = 1,
  grain = 0.05,
  contrast = 1.1,
  opacity = 0.95,
  reveal = true,
  delayMs = 0,
  revealDuration = 1.2,
  children,
  className,
  ...rest
}: WebGLLiquidProps) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const glRef = useRef<WebGLRenderingContext | null>(null);
  const programRef = useRef<WebGLProgram | null>(null);
  const rafRef = useRef<number>(0);
  const startRef = useRef<number>(0);
  const revealRef = useRef(reveal ? 0 : 1.5);
  const [webglFailed, setWebGLFailed] = useState(false);

  const setupWebGL = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let gl: WebGLRenderingContext | null = null;
    try {
      gl = canvas.getContext("webgl", {
        antialias: true,
        alpha: true,
      }) as WebGLRenderingContext | null;
    } catch {
      setWebGLFailed(true);
      return;
    }
    if (!gl) {
      setWebGLFailed(true);
      return;
    }
    glRef.current = gl;

    // Compile + link
    let vert: WebGLShader, frag: WebGLShader;
    try {
      vert = compileShader(gl, gl.VERTEX_SHADER, VERT_SRC);
      frag = compileShader(gl, gl.FRAGMENT_SHADER, FRAG_SRC);
    } catch (e) {
      console.error("WebGLLiquid shader error:", e);
      setWebGLFailed(true);
      return;
    }

    const program = gl.createProgram()!;
    gl.attachShader(program, vert);
    gl.attachShader(program, frag);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error("WebGLLiquid link error:", gl.getProgramInfoLog(program));
      setWebGLFailed(true);
      return;
    }
    programRef.current = program;
    gl.useProgram(program);

    // Geometry: full-screen quad
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]),
      gl.STATIC_DRAW
    );
    const posLoc = gl.getAttribLocation(program, "position");
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

    // Clean up shaders (already linked)
    gl.deleteShader(vert);
    gl.deleteShader(frag);
  }, []);

  const resizeCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const wrapper = wrapperRef.current;
    const gl = glRef.current;
    if (!canvas || !wrapper || !gl) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = wrapper.clientWidth;
    const h = wrapper.clientHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    gl.viewport(0, 0, canvas.width, canvas.height);
  }, []);

  const render = useCallback(
    (now: number) => {
      const gl = glRef.current;
      const program = programRef.current;
      const canvas = canvasRef.current;
      if (!gl || !program || !canvas) return;

      if (startRef.current === 0) startRef.current = now;
      const elapsed = (now - startRef.current) / 1000;

      // Reveal animation
      if (reveal) {
        const revealTarget = 1.5;
        const revealSpeed = revealTarget / revealDuration;
        if (revealRef.current < revealTarget) {
          revealRef.current = Math.min(
            revealTarget,
            revealRef.current + (revealSpeed * 16.67) / 1000
          );
        }
      }

      const u = (name: string) => gl.getUniformLocation(program, name);

      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);

      gl.uniform1f(u("u_time"), elapsed);
      gl.uniform2f(u("u_resolution"), canvas.width, canvas.height);
      gl.uniform3fv(u("u_colorDeep"), hexToVec3(colorDeep));
      gl.uniform3fv(u("u_colorMid"), hexToVec3(colorMid));
      gl.uniform3fv(u("u_colorHighlight"), hexToVec3(colorHighlight));
      gl.uniform1f(u("u_speed"), speed);
      gl.uniform1f(u("u_flowStrength"), flowStrength);
      gl.uniform1f(u("u_grain"), grain);
      gl.uniform1f(u("u_contrast"), contrast);
      gl.uniform1f(u("u_opacity"), opacity);
      gl.uniform1f(u("u_reveal"), revealRef.current);

      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

      rafRef.current = requestAnimationFrame(render);
    },
    [colorDeep, colorMid, colorHighlight, speed, flowStrength, grain, contrast, opacity, reveal, revealDuration]
  );

  useEffect(() => {
    if (webglFailed) return;

    const timer = setTimeout(() => {
      setupWebGL();
      resizeCanvas();

      const observer = new ResizeObserver(() => resizeCanvas());
      if (wrapperRef.current) observer.observe(wrapperRef.current);

      rafRef.current = requestAnimationFrame(render);

      return () => {
        observer.disconnect();
        cancelAnimationFrame(rafRef.current);
        const gl = glRef.current;
        if (gl && programRef.current) gl.deleteProgram(programRef.current);
      };
    }, delayMs);

    return () => clearTimeout(timer);
  }, [webglFailed, setupWebGL, resizeCanvas, render, delayMs]);

  return (
    <div
      ref={wrapperRef}
      className={cn(
        "relative flex min-h-screen w-full overflow-hidden bg-bg-sunken text-foreground",
        className
      )}
      {...rest}
    >
      {/* WebGL canvas */}
      {!webglFailed ? (
        <canvas
          ref={canvasRef}
          aria-hidden
          className="pointer-events-none absolute inset-0 h-full w-full"
        />
      ) : (
        <WebGLFallback
          colorDeep={colorDeep}
          colorMid={colorMid}
          colorHighlight={colorHighlight}
        />
      )}

      {/* Readability overlays */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "linear-gradient(to right, rgba(4,5,11,0.72) 0%, rgba(4,5,11,0.28) 60%, transparent 100%)",
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse at 20% 50%, rgba(140,236,255,0.07) 0%, transparent 60%)",
        }}
      />

      {/* Foreground content */}
      <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-col items-center justify-center px-6 py-32 lg:px-12">
        <div className="w-full max-w-[760px] lg:max-w-none">
          {subtitle && (
            <p
              className="mb-4 text-sm font-semibold uppercase tracking-widest"
              style={{ color: colorHighlight }}
            >
              {subtitle}
            </p>
          )}
          {title && (
            <h1
              className="font-heading font-semibold leading-[0.92] tracking-[-0.03em] text-white"
              style={{
                fontSize: "clamp(2.5rem, 7cqi, 5rem)",
              }}
            >
              {title}
            </h1>
          )}
          {description && (
            <p className="mt-6 max-w-xl text-lg text-white/70">{description}</p>
          )}
          {children && <div className="mt-10">{children}</div>}
        </div>
      </div>
    </div>
  );
}
