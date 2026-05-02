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
uniform float u_detail;
uniform float u_bloom_strength;
uniform float u_warp_strength;
uniform float u_line_strength;
uniform float u_exposure;
uniform float u_softness;

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

float flowField(vec2 p, float t) {
    float value = 0.0;
    value += sin(p.x * 2.7 + p.y * 1.8 + t * 0.31) * 0.34;
    value += sin(p.x * -1.6 + p.y * 3.1 - t * 0.24) * 0.28;
    value += cos(length(p + vec2(0.18, -0.12)) * 5.4 - t * 0.42) * 0.22;
    value += sin(atan(p.y, p.x) * 3.0 + length(p) * 7.5 + t * 0.18) * 0.16;
    return value * 0.5 + 0.5;
}

float spectrumAt(float amount) {
    float wrapped = fract(amount);
    float index = wrapped * 32.0;
    int left = int(floor(index)) % 32;
    int right = (left + 1) % 32;
    float blend = fract(index);
    return mix(u_spectrum[left], u_spectrum[right], blend);
}

void main() {
    vec2 uv = v_uv;
    vec2 aspect = vec2(u_resolution.x / max(1.0, u_resolution.y), 1.0);
    vec2 p = (uv - 0.5) * aspect;
    float r = length(p);
    float a = atan(p.y, p.x);

    float detail = clamp(u_detail, 0.05, 1.5);
    float softness = clamp(u_softness, 0.0, 1.5);
    float pulse = max(u_bass, u_slow_pulse * 0.82) + u_beat_decay * 0.22 + u_beat * 0.18;
    float warp = fbm(p * (2.4 + u_treble * 2.8 + detail * 2.2) + u_time * vec2(0.1, -0.07));
    vec2 warped = p + vec2(cos(a * 2.0 + warp * 4.3), sin(a * 3.0 - warp * 3.6)) * 0.042 * u_warp_strength;
    float wr = length(warped);
    float wa = atan(warped.y, warped.x);

    float ring_radius = 0.23 + u_bass * 0.06 + u_beat_decay * 0.025;
    float ring_sharpness = mix(18.0, 44.0, clamp(1.0 - softness * 0.45 + detail * 0.25, 0.0, 1.0));
    float ring = exp(-abs(wr - ring_radius) * (ring_sharpness + u_rms * 18.0));
    float inner = exp(-wr * (3.2 - u_bass * 0.9));
    float halo = exp(-abs(wr - ring_radius * 1.55) * mix(5.0, 9.5, 1.0 - softness * 0.4)) * 0.62;

    float bands = abs(sin(wa * mix(26.0, 64.0, detail) + u_time * (1.0 + u_treble * 1.7)));
    float spectral = spectrumAt((wa + 3.14159265) / 6.2831853);
    float shards = pow(bands, mix(5.5, 13.0, detail)) * spectral * (0.16 + u_treble * 0.72) * u_line_strength;

    float mist = flowField(warped * (1.25 + u_mid * 0.55 + detail * 0.35), u_time);
    float fine = fbm(warped * (18.0 + u_treble * 8.0 + detail * 7.0) + u_time * 0.11);
    float grain = smoothstep(0.68, 1.0, fine) * (0.45 + mist * 0.35);
    float bloom = ring * (0.78 + pulse * 0.82) + inner * (0.24 + u_rms * 0.28);
    bloom += halo * (0.28 + u_mid * 0.28) + shards * ring * 1.35;
    bloom += grain * (0.055 + u_treble * 0.08) * (0.65 + detail * 0.35);
    bloom *= u_bloom_strength;

    vec3 base = mix(vec3(0.004, 0.006, 0.018), u_palette_base, 0.18 + u_rms * 0.18);
    vec3 color = base;
    color = mix(color, u_palette_accent, clamp(ring * 0.68 + mist * 0.035, 0.0, 1.0));
    color = mix(color, u_palette_beat, clamp(shards * 0.42 + pulse * ring * 0.5, 0.0, 1.0));
    color += u_palette_accent * bloom * 0.44;
    color += u_palette_beat * pow(max(0.0, bloom), 1.55 + detail * 0.35) * 0.34;

    float vignette = smoothstep(1.25, 0.2, r);
    color *= vignette;
    color = vec3(1.0) - exp(-color * (u_exposure + pulse * 0.42));
    color = pow(color, vec3(0.92 + softness * 0.08));
    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
