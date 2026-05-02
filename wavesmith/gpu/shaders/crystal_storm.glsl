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
    return fract(sin(dot(p, vec2(41.7, 289.3))) * 19341.713);
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
    float amp = 0.52;
    for (int i = 0; i < 5; i++) {
        value += noise(p) * amp;
        p = mat2(1.48, -1.08, 1.08, 1.48) * p + vec2(4.2, 8.7);
        amp *= 0.5;
    }
    return value;
}

float spectrumAt(float amount) {
    float index = fract(amount) * 32.0;
    int left = int(floor(index)) % 32;
    int right = (left + 1) % 32;
    return mix(u_spectrum[left], u_spectrum[right], fract(index));
}

float lineDistance(vec2 p, float angle) {
    vec2 n = vec2(cos(angle), sin(angle));
    return abs(dot(p, n));
}

void main() {
    vec2 aspect = vec2(u_resolution.x / max(1.0, u_resolution.y), 1.0);
    vec2 p = (v_uv - 0.5) * aspect;
    float r = length(p);
    float a = atan(p.y, p.x);
    float detail = clamp(u_detail, 0.05, 1.5);
    float pulse = max(u_bass, u_slow_pulse * 0.75) + u_beat_decay * 0.28 + u_beat * 0.22;

    float cloud = fbm(p * (2.0 + detail * 1.2) + vec2(u_time * 0.04, -u_time * 0.03));
    float nebula = fbm(p * 5.0 + vec2(cloud * 1.8, -cloud * 1.4) + u_time * 0.06);

    float core_radius = 0.22 + u_bass * 0.05 + u_beat_decay * 0.025;
    float core = exp(-abs(r - core_radius) * (20.0 + detail * 20.0));
    float inner = exp(-r * (3.6 - u_bass * 0.7));
    float aura = exp(-abs(r - core_radius * 1.9) * 5.5) * (0.28 + u_mid * 0.28);

    float shard_sum = 0.0;
    float spark_sum = 0.0;
    for (int i = 0; i < 32; i++) {
        float fi = float(i);
        float amount = spectrumAt((fi + 0.5) / 32.0);
        float angle = fi * 0.19634954 + sin(fi * 3.1) * 0.08 + u_time * 0.035;
        float radial_gate = smoothstep(0.05, 0.68 + amount * 0.22, r) * smoothstep(1.15, 0.2, r);
        float shard = exp(-lineDistance(p, angle) * (56.0 + detail * 86.0));
        shard *= radial_gate * amount * (0.12 + u_treble * 0.5 + u_line_strength * 0.75);
        shard_sum += shard;

        vec2 crystal_pos = vec2(cos(angle), sin(angle)) * (0.28 + amount * 0.42);
        float crystal = exp(-length(p - crystal_pos) * (28.0 + detail * 26.0));
        spark_sum += crystal * amount * (0.11 + u_beat_decay * 0.26);
    }

    float facets = pow(abs(sin(a * (9.0 + detail * 15.0) + cloud * 3.2 - u_time * 0.12)), 10.0);
    facets *= smoothstep(0.1, 0.7, r) * smoothstep(1.18, 0.32, r) * (0.05 + u_mid * 0.18);
    float fracture_a = exp(-lineDistance(p, 0.72 + cloud * 0.2) * 42.0);
    float fracture_b = exp(-lineDistance(p, -0.94 + nebula * 0.18) * 38.0);
    float fractures = (fracture_a + fracture_b) * smoothstep(0.08, 0.62, r) * smoothstep(1.1, 0.25, r);
    fractures *= 0.045 + u_treble * 0.12 + u_beat_decay * 0.08;

    float bloom = core * (0.48 + pulse * 0.72);
    bloom += inner * (0.16 + u_rms * 0.25);
    bloom += aura + shard_sum * 0.95 + spark_sum * 1.25 + fractures + facets;
    bloom *= u_bloom_strength;

    vec3 color = mix(vec3(0.004, 0.006, 0.019), u_palette_base, 0.12 + nebula * 0.24);
    color = mix(color, u_palette_accent, clamp(core * 0.56 + shard_sum * 0.74 + facets * 0.42, 0.0, 1.0));
    color = mix(color, u_palette_beat, clamp(spark_sum * 0.8 + pulse * core * 0.32, 0.0, 1.0));
    color += u_palette_accent * bloom * 0.38;
    color += u_palette_beat * pow(max(0.0, bloom), 1.6) * 0.32;
    color += vec3(0.12, 0.22, 0.35) * nebula * (0.08 + u_mid * 0.12);

    float vignette = smoothstep(1.24, 0.15, r);
    color *= vignette;
    color = vec3(1.0) - exp(-color * (u_exposure + pulse * 0.4));
    color = pow(color, vec3(0.9 + clamp(u_softness, 0.0, 1.5) * 0.08));
    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
