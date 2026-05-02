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
    return fract(sin(dot(p, vec2(113.5, 271.9))) * 41538.173);
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
    float amp = 0.54;
    for (int i = 0; i < 5; i++) {
        value += noise(p) * amp;
        p = mat2(1.58, -1.04, 1.04, 1.58) * p + vec2(6.1, 2.7);
        amp *= 0.52;
    }
    return value;
}

float spectrumAt(float amount) {
    float index = fract(amount) * 32.0;
    int left = int(floor(index)) % 32;
    int right = (left + 1) % 32;
    return mix(u_spectrum[left], u_spectrum[right], fract(index));
}

float plume(vec2 p, vec2 base, vec2 normal, vec2 tangent, float height, float width, float phase) {
    vec2 q = p - base;
    float up = dot(q, normal);
    float side = dot(q, tangent);
    float sway = sin(up * 17.0 + phase) * width * 0.42 + sin(up * 9.0 - phase * 0.7) * width * 0.2;
    float taper = smoothstep(0.0, height * 0.16, up) * smoothstep(height, height * 0.22, up);
    float strand = exp(-abs(side - sway) * (20.0 / max(0.02, width)));
    float body = exp(-abs(side - sway) * (5.4 / max(0.04, width)));
    float lick = strand * 0.62 + body * 0.22;
    return lick * taper;
}

void main() {
    vec2 aspect = vec2(u_resolution.x / max(1.0, u_resolution.y), 1.0);
    vec2 p = (v_uv - 0.5) * aspect;
    float detail = clamp(u_detail, 0.05, 1.5);
    float softness = clamp(u_softness, 0.0, 1.5);
    float pulse = max(u_bass, u_slow_pulse * 0.92) + u_beat_decay * 0.25 + u_beat * 0.2;

    vec2 sun_center = vec2(0.0, -0.82);
    float sun_radius = 0.82 + u_bass * 0.035;
    vec2 solar = p - sun_center;
    float radius = length(solar);
    float angle = atan(solar.y, solar.x);
    float surface_distance = abs(radius - sun_radius);
    float disk = smoothstep(sun_radius + 0.015, sun_radius - 0.035, radius);
    float rim = exp(-surface_distance * (24.0 + detail * 28.0));
    float corona = exp(-max(0.0, radius - sun_radius) * (4.2 - u_bass * 0.7));

    vec2 flow = vec2(angle * 1.8, radius * 5.8 - u_time * (0.18 + u_mid * 0.16));
    float granules = fbm(flow * (2.0 + detail * 1.6));
    float cells = fbm(flow * (6.0 + detail * 4.5) + vec2(u_time * 0.05, -u_time * 0.08));
    float surface = disk * (0.38 + granules * 0.34 + cells * 0.26);

    float prominences = 0.0;
    float sparks = 0.0;
    for (int i = 0; i < 24; i++) {
        float fi = float(i);
        float t = fi / 23.0;
        float anchor_angle = mix(0.18, 0.82, t) * 3.14159265;
        float amount = spectrumAt(t);
        vec2 normal = vec2(cos(anchor_angle), sin(anchor_angle));
        vec2 tangent = vec2(-normal.y, normal.x);
        vec2 base = sun_center + normal * sun_radius;
        float local = sin(u_time * (0.55 + amount * 0.45) + fi * 4.31);
        float height = (0.08 + amount * 0.2 + u_slow_pulse * 0.08) * (0.82 + pulse * 0.28);
        float width = 0.018 + amount * 0.026 + u_line_strength * 0.02;
        float active_level = smoothstep(0.12, 0.72, amount + u_bass * 0.28 + local * 0.16);
        prominences += plume(p, base, normal, tangent, height, width, u_time * 1.2 + fi) * active_level;

        vec2 spark_pos = base + normal * height * (0.45 + 0.35 * local) + tangent * local * width * 2.2;
        sparks += exp(-length(p - spark_pos) * (28.0 + detail * 30.0)) * amount * active_level;
    }

    float heat_haze = fbm(p * (5.5 + detail * 2.5) + vec2(u_time * 0.08, -u_time * 0.18));
    float smoke = smoothstep(0.42, 0.92, heat_haze) * corona * (0.12 + u_mid * 0.18);
    float bloom = surface * 0.45 + rim * (0.48 + pulse * 0.65);
    bloom += corona * 0.16 + prominences * 1.25 + sparks * 0.9 + smoke;
    bloom *= u_bloom_strength;

    vec3 deep = vec3(0.012, 0.002, 0.0);
    vec3 ember = mix(u_palette_base, u_palette_accent, 0.36);
    vec3 color = mix(deep, ember, clamp(surface + smoke * 0.45, 0.0, 1.0));
    color = mix(color, u_palette_accent, clamp(rim * 0.62 + prominences * 0.58, 0.0, 1.0));
    color = mix(color, u_palette_beat, clamp(sparks * 0.68 + pulse * rim * 0.4, 0.0, 1.0));
    color += u_palette_accent * bloom * 0.42;
    color += u_palette_beat * pow(max(0.0, bloom), 1.55 + detail * 0.22) * 0.34;

    float vignette = smoothstep(1.22, 0.16, length(p));
    color *= vignette;
    color = vec3(1.0) - exp(-color * (u_exposure + pulse * 0.48));
    color = pow(color, vec3(0.88 + softness * 0.08));
    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
