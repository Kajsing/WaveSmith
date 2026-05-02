#version 330

in vec2 v_uv;
out vec4 fragColor;

uniform vec2 u_resolution;
uniform float u_time;
uniform float u_progress;
uniform float u_rms;
uniform float u_bass;
uniform float u_mid;
uniform float u_treble;
uniform float u_beat;
uniform float u_beat_decay;
uniform float u_slow_pulse;
uniform vec3 u_palette_base;
uniform vec3 u_palette_accent;
uniform vec3 u_palette_beat;
uniform float u_spectrum[32];

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
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
    float value = 0.0;
    float amp = 0.5;
    for (int i = 0; i < 5; i++) {
        value += noise(p) * amp;
        p = mat2(1.62, -1.12, 1.12, 1.62) * p + vec2(7.3, 3.1);
        amp *= 0.52;
    }
    return value;
}

float spectrumAt(float amount) {
    float index = clamp(amount, 0.0, 0.999) * 31.0;
    int left = int(floor(index));
    int right = min(31, left + 1);
    float blend = fract(index);
    return mix(u_spectrum[left], u_spectrum[right], blend);
}

void main() {
    vec2 uv = v_uv;
    vec2 aspect = vec2(u_resolution.x / max(1.0, u_resolution.y), 1.0);
    vec2 p = (uv - 0.5) * aspect;
    float r = length(p);
    float a = atan(p.y, p.x);

    float pulse = max(u_bass, u_slow_pulse * 0.82) + u_beat_decay * 0.22 + u_beat * 0.18;
    float warp = fbm(p * (3.0 + u_treble * 4.0) + u_time * vec2(0.12, -0.08));
    vec2 warped = p + vec2(cos(a * 2.0 + warp * 5.2), sin(a * 3.0 - warp * 4.0)) * 0.045;
    float wr = length(warped);
    float wa = atan(warped.y, warped.x);

    float ring_radius = 0.23 + u_bass * 0.06 + u_beat_decay * 0.025;
    float ring = exp(-abs(wr - ring_radius) * (28.0 + u_rms * 38.0));
    float inner = exp(-wr * (3.2 - u_bass * 0.9));
    float halo = exp(-abs(wr - ring_radius * 1.55) * 8.0) * 0.55;

    float bands = abs(sin(wa * 48.0 + u_time * (1.4 + u_treble * 2.2)));
    float spectral = spectrumAt(fract((wa + 3.14159265) / 6.2831853));
    float shards = pow(bands, 18.0) * spectral * (0.35 + u_treble * 1.2);

    float field = fbm(warped * (7.0 + u_mid * 7.0) - u_time * 0.22);
    float bloom = ring * (0.65 + pulse * 0.95) + inner * (0.22 + u_rms * 0.35);
    bloom += halo * (0.22 + u_mid * 0.32) + shards * ring * 1.7;
    bloom += smoothstep(0.58, 1.0, field) * (0.16 + u_treble * 0.22);

    vec3 base = mix(vec3(0.004, 0.006, 0.018), u_palette_base, 0.18 + u_rms * 0.18);
    vec3 color = base;
    color = mix(color, u_palette_accent, clamp(ring * 0.72 + field * 0.18, 0.0, 1.0));
    color = mix(color, u_palette_beat, clamp(shards * 0.7 + pulse * ring * 0.6, 0.0, 1.0));
    color += u_palette_accent * bloom * 0.48;
    color += u_palette_beat * pow(max(0.0, bloom), 2.0) * 0.38;

    float vignette = smoothstep(1.25, 0.2, r);
    color *= vignette;
    color = vec3(1.0) - exp(-color * (1.05 + pulse * 0.55));
    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
