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

float loopArc(vec2 p, vec2 foot_a, vec2 foot_b, vec2 lift, float width, float phase) {
    float best = 0.0;
    for (int i = 0; i < 24; i++) {
        float t0 = float(i) / 24.0;
        float t1 = float(i + 1) / 24.0;
        vec2 a = mix(foot_a, foot_b, t0) + lift * sin(t0 * 3.14159265);
        vec2 b = mix(foot_a, foot_b, t1) + lift * sin(t1 * 3.14159265);
        a += vec2(sin(t0 * 9.0 + phase), cos(t0 * 7.0 - phase * 0.6)) * width * 0.42;
        b += vec2(sin(t1 * 9.0 + phase), cos(t1 * 7.0 - phase * 0.6)) * width * 0.42;
        vec2 pa = p - a;
        vec2 ba = b - a;
        float h = clamp(dot(pa, ba) / max(0.0001, dot(ba, ba)), 0.0, 1.0);
        float d = length(pa - ba * h);
        float t = mix(t0, t1, h);
        float strand = exp(-d * (1.25 / max(0.03, width)));
        float core = exp(-d * (0.42 / max(0.05, width)));
        float taper = smoothstep(0.0, 0.16, t) * smoothstep(1.0, 0.84, t);
        best = max(best, (strand * 0.46 + core * 0.28) * taper);
    }
    return best;
}

float eruptionCloud(vec2 p, vec2 base, vec2 normal, vec2 tangent, float height, float width, float phase) {
    vec2 q = p - base;
    float up = dot(q, normal);
    float side = dot(q, tangent);
    float rise = clamp(up / max(0.02, height), 0.0, 1.4);
    float curl = sin(rise * 8.0 + phase) * width * (0.35 + rise * 0.85);
    curl += sin(rise * 15.0 - phase * 0.62) * width * 0.2;
    float radius = width * (1.4 + rise * 2.4);
    float side_field = exp(-pow(abs(side - curl) / max(0.02, radius), 1.55));
    float vertical = smoothstep(-0.03, height * 0.18, up) * smoothstep(height * 1.35, height * 0.2, up);
    float turbulent = fbm(p * 12.0 + vec2(phase * 0.12, -phase * 0.18));
    float broken = smoothstep(0.18, 0.92, turbulent);
    return side_field * vertical * (0.28 + broken * 0.5);
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
    float wisps = 0.0;
    float eruptions = 0.0;
    float source_bursts = 0.0;
    float sparks = 0.0;
    for (int i = 0; i < 9; i++) {
        float fi = float(i);
        float t = fi / 8.0;
        float center_angle = mix(0.16, 0.84, t) * 3.14159265 + sin(fi * 5.17) * 0.075;
        float spread = 0.09 + 0.045 * sin(fi * 2.4);
        float amount = spectrumAt(t * 0.86 + 0.07);
        float life = 0.5 + 0.5 * sin(u_time * (0.15 + 0.03 * fi) + fi * 1.71);
        float growth = smoothstep(0.18, 0.92, life);
        float fade_out = mix(1.0, 0.34, smoothstep(0.66, 1.0, life));
        float gate = smoothstep(0.33, 0.84, life + amount * 0.3 + u_bass * 0.14);
        float active_level = gate * gate * fade_out;
        vec2 normal = vec2(cos(center_angle), sin(center_angle));
        vec2 tangent = vec2(-normal.y, normal.x);
        vec2 foot_a = sun_center + vec2(cos(center_angle - spread), sin(center_angle - spread)) * sun_radius;
        vec2 foot_b = sun_center + vec2(cos(center_angle + spread), sin(center_angle + spread)) * sun_radius;
        float height = 0.12 + amount * 0.18 + u_slow_pulse * 0.08 + growth * 0.2;
        vec2 lift = normal * height + tangent * sin(u_time * 0.18 + fi) * height * 0.32;
        float width = 0.032 + amount * 0.022 + u_line_strength * 0.016;
        float flare = loopArc(p, foot_a, foot_b, lift, width, u_time * 0.55 + fi * 2.3);
        prominences += flare * active_level * 0.72;

        vec2 source = mix(foot_a, foot_b, 0.5);
        source_bursts += exp(-length(p - source) * (20.0 + detail * 14.0))
            * active_level
            * (0.16 + u_bass * 0.42 + u_beat_decay * 0.34);
        float eruption_height = height * (0.48 + pulse * 0.28 + growth * 0.24);
        float eruption_width = width * (0.95 + u_bass * 0.75 + growth * 0.62);
        eruptions += eruptionCloud(
            p,
            source,
            normal,
            tangent,
            eruption_height,
            eruption_width,
            u_time * (0.62 + amount * 0.2) + fi * 2.9
        ) * active_level * (0.22 + u_bass * 0.36 + u_beat_decay * 0.26);

        for (int j = 0; j < 4; j++) {
            float fj = float(j);
            float side = fj - 1.5;
            float split = smoothstep(0.2, 0.86, growth + amount * 0.2);
            float branch_phase = u_time * (0.34 + fj * 0.07) + fi * 1.4 + fj * 2.1;
            vec2 branch_a = foot_a + tangent * side * width * (0.45 + split * 0.45) + normal * width * 0.35;
            vec2 branch_b = foot_b + tangent * side * width * (0.65 + split * 0.85) + normal * width * 0.35;
            vec2 branch_lift = lift * (1.04 + split * (0.08 + fj * 0.025));
            branch_lift += tangent * side * width * (3.4 + split * 6.2);
            float branch_width = width * (0.68 - fj * 0.08);
            float branch = loopArc(p, branch_a, branch_b, branch_lift, branch_width, branch_phase);
            float treble_flicker = 0.72 + u_treble * 0.55 + sin(branch_phase * 1.7) * 0.12;
            float outer_fade = mix(1.0, 0.52, abs(side) / 1.5);
            wisps += branch * active_level * split * treble_flicker * outer_fade * (0.1 + amount * 0.16);
        }

        vec2 spark_pos = mix(foot_a, foot_b, 0.5) + lift * (0.9 + life * 0.18);
        sparks += exp(-length(p - spark_pos) * (14.0 + detail * 14.0)) * amount * active_level;
    }

    float heat_haze = fbm(p * (5.5 + detail * 2.5) + vec2(u_time * 0.08, -u_time * 0.18));
    float plasma_noise = fbm(p * (12.0 + detail * 6.0) + vec2(u_time * 0.12, -u_time * 0.24));
    prominences *= 0.82 + plasma_noise * 0.42;
    wisps *= 0.7 + plasma_noise * 0.62;
    eruptions *= 0.76 + plasma_noise * 0.58;
    float smoke = smoothstep(0.42, 0.92, heat_haze) * corona * (0.12 + u_mid * 0.18);
    float bloom = surface * 0.45 + rim * (0.48 + pulse * 0.65);
    bloom += corona * 0.16 + source_bursts * 0.82 + eruptions * 0.78 + prominences * 1.05 + wisps * 0.56 + sparks * 0.42 + smoke * 0.68;
    bloom *= u_bloom_strength;

    vec3 deep = vec3(0.012, 0.002, 0.0);
    vec3 ember = mix(u_palette_base, u_palette_accent, 0.36);
    vec3 color = mix(deep, ember, clamp(surface + smoke * 0.45, 0.0, 1.0));
    color = mix(color, u_palette_accent, clamp(rim * 0.56 + source_bursts * 0.42 + eruptions * 0.48 + prominences * 0.6 + wisps * 0.32, 0.0, 1.0));
    color = mix(color, u_palette_beat, clamp(source_bursts * 0.34 + sparks * 0.22 + pulse * rim * 0.24 + eruptions * 0.1, 0.0, 1.0));
    color += u_palette_base * eruptions * 0.32;
    color += u_palette_accent * bloom * 0.34;
    color += u_palette_beat * pow(max(0.0, bloom), 1.45 + detail * 0.18) * 0.22;

    float vignette = smoothstep(1.22, 0.16, length(p));
    color *= vignette;
    color = vec3(1.0) - exp(-color * (u_exposure + pulse * 0.48));
    color = pow(color, vec3(0.88 + softness * 0.08));
    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
